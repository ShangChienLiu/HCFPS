import os
import json
import logging
from flask import Flask, request, jsonify
from urllib.parse import urlparse

# Import cloud SDKs and stubs for processing
try:
    import boto3
    from google.cloud import storage, firestore
except ImportError:
    boto3 = None
    storage = None
    firestore = None

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("processor-app")

# --- Logging setup for CloudWatch and Cloud Logging ---
try:
    import google.cloud.logging as gcp_logging
    gcp_logging_client = gcp_logging.Client()
    gcp_logging_client.setup_logging()
except Exception:
    gcp_logging_client = None

# --- Helper for AWS Secrets Manager (optional, for cross-cloud uploads) ---
def get_aws_secret(secret_name):
    if not boto3:
        logger.error("boto3 not available for Secrets Manager")
        return None
    try:
        client = boto3.client('secretsmanager')
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)
    except Exception as e:
        logger.error(f"Failed to get AWS secret: {e}")
        return None

# --- Helper for GCP Secret Manager (optional, for cross-cloud uploads) ---
def get_gcp_secret(secret_id):
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(request={"name": secret_id})
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.error(f"Failed to get GCP secret: {e}")
        return None

# --- Import processor modules ---
from processor import (
    convert_h265, compress_file, rename_file, detect_format, upload_file, download_file, update_status
)

# --- Main processing logic ---
def process_task(task_data, provider):
    task_id = task_data.get('task_id', 'unknown')
    action = task_data.get('action')
    source_path = task_data.get('source_path')
    output_path = task_data.get('output_path')
    params = task_data.get('params', {})
    # Fallback logic for source_path
    if not source_path:
        if provider == 'aws':
            bucket = os.environ.get('AWS_TEMP_BUCKET')
            if bucket:
                source_path = f"s3://{bucket}/input_{task_id}"
        elif provider == 'gcp':
            bucket = os.environ.get('GCP_TEMP_BUCKET')
            if bucket:
                source_path = f"gs://{bucket}/input_{task_id}"
    # Fallback logic for output_path
    if not output_path:
        if action == 'convert_h265' and source_path:
            # Auto-generate output path for H.265 conversion
            from urllib.parse import urlparse
            parsed = urlparse(source_path)
            base, ext = os.path.splitext(os.path.basename(parsed.path))
            output_filename = f"{base}_h265.mp4"
            if provider == 'aws':
                bucket = os.environ.get('AWS_DESTINATION_BUCKET')
                if bucket:
                    output_path = f"s3://{bucket}/{output_filename}"
            elif provider == 'gcp':
                bucket = os.environ.get('GCP_DESTINATION_BUCKET')
                if bucket:
                    output_path = f"gs://{bucket}/{output_filename}"
            else:
                # fallback: same scheme as source_path
                output_path = source_path.replace(base + ext, output_filename)
        else:
            if provider == 'aws':
                bucket = os.environ.get('AWS_DESTINATION_BUCKET')
                if bucket:
                    output_path = f"s3://{bucket}/output_{task_id}"
            elif provider == 'gcp':
                bucket = os.environ.get('GCP_DESTINATION_BUCKET')
                if bucket:
                    output_path = f"gs://{bucket}/output_{task_id}"
    work_dir = '/tmp/processing'
    os.makedirs(work_dir, exist_ok=True)
    # Determine local input/output paths, preserving extension for input
    source_ext = os.path.splitext(source_path)[1] if source_path else ''
    local_input = os.path.join(work_dir, f"input_{task_id}{source_ext}")
    local_output = os.path.join(work_dir, f"output_{task_id}")
    if not download_file(source_path, local_input):
        logger.error("Download failed")
        update_status(task_id, 'FAILED', error_type='download_failed')
        return False
    ok = False
    if action == 'convert_h265':
        file_format = detect_format(local_input)
        ok = convert_h265(local_input, local_output, file_format, params)
    elif action == 'compress':
        # Use compress_file, which now handles .bag (gzip) and others (zip)
        file_format = detect_format(local_input)
        compress_success = compress_file(local_input, local_output, params)
        if not compress_success:
            logger.error(f"Compression failed for {local_input}")
            raise Exception("Compression failed")
        ok = True
    elif action == 'rename':
        ok = rename_file(local_input, local_output, params)
    else:
        logger.error(f"Unknown action: {action}")
        update_status(task_id, 'FAILED', error_type='unknown_action')
        ok = False
    if not ok:
        logger.error("Processing failed")
        update_status(task_id, 'FAILED', error_type='processing_failed')
        return False
    logger.info(f"Attempting to upload {local_output} to {output_path}")
    upload_result = upload_file(local_output, output_path)
    logger.info(f"upload_file result: {upload_result}")
    if not upload_result:
        logger.error("Upload failed")
        update_status(task_id, 'FAILED', error_type='upload_failed')
        return False
    update_status(task_id, 'SUCCESS')
    return True

# --- Flask endpoints ---
@app.route('/sns', methods=['POST'])
def handle_sns():
    envelope = request.get_json()
    logger.info(f"[SNS] Envelope: {envelope}")
    if envelope.get("Type") == "SubscriptionConfirmation":
        logger.info(f"Subscription confirmation: {envelope.get('SubscribeURL')}")
        return jsonify({"status": "Subscription confirmation received"}), 200
    if envelope.get("Type") == "Notification" and "Message" in envelope:
        try:
            task_data = json.loads(envelope["Message"])
            logger.info(f"[SNS] Task: {task_data}")
            if process_task(task_data, provider='aws'):
                return jsonify({"status": "success"}), 200
            else:
                return jsonify({"status": "error"}), 500
        except Exception as e:
            logger.error(f"SNS processing error: {e}")
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid SNS message format"}), 400

@app.route('/', methods=['POST'])
def handle_pubsub():
    envelope = request.get_json()
    logger.info(f"[PubSub] Envelope: {envelope}")
    if not envelope or 'message' not in envelope:
        return jsonify({"error": "Invalid Pub/Sub message format"}), 400
    pubsub_message = envelope['message']
    if 'data' not in pubsub_message:
        return jsonify({"error": "No data in Pub/Sub message"}), 400
    try:
        import base64
        data = base64.b64decode(pubsub_message['data']).decode('utf-8')
        task_data = json.loads(data)
        logger.info(f"[PubSub] Task: {task_data}")
        if process_task(task_data, provider='gcp'):
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 500
    except Exception as e:
        logger.error(f"PubSub processing error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080) 