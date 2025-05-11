from flask import Blueprint, request, jsonify, current_app
import boto3
import os
import uuid
import tempfile
from google.cloud import storage
from boto3.s3.transfer import TransferConfig

# Get environment variables
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
AWS_TEMP_BUCKET = os.environ.get('AWS_TEMP_BUCKET', 'temp-uploads')
GCP_TEMP_BUCKET = os.environ.get('GCP_TEMP_BUCKET', 'temp-uploads')

# Initialize AWS and GCP clients
s3 = boto3.client('s3', region_name=AWS_REGION)
storage_client = None

try:
    GCP_SERVICE_ACCOUNT_KEY = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
    if GCP_SERVICE_ACCOUNT_KEY:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GCP_SERVICE_ACCOUNT_KEY
        storage_client = storage.Client()
    else:
        # Only try default credentials if specifically requested
        if os.environ.get('USE_GCP_DEFAULT_CREDENTIALS', '').lower() == 'true':
            storage_client = storage.Client()
        else:
            print("Skipping GCP storage client initialization - no credentials provided")
except Exception as e:
    print(f"Error initializing GCP storage client: {e}")

# Create blueprint
upload_local_blueprint = Blueprint('upload_local', __name__)

@upload_local_blueprint.route('/api/upload', methods=['POST'])
def upload_local():
    """
    Uploads a file to a temporary location in AWS S3 or Google Cloud Storage.
    Uses a session ID to group files together.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
        
    upload_to = request.form.get('upload_to')
    if not upload_to or upload_to not in ['aws', 'gcp']:
        return jsonify({'success': False, 'error': 'Invalid upload platform'}), 400
        
    session_id = request.form.get('session_id', str(uuid.uuid4()))
    
    try:
        # Create a unique path for the file in the temp bucket
        filename = os.path.basename(file.filename)
        object_key = f"{session_id}/{filename}"
        
        if upload_to == 'aws':
            # Save file to temp location
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                file.save(tmp.name)
                # Upload to S3 with TransferConfig
                config = TransferConfig(
                    multipart_threshold=8 * 1024 * 1024,
                    multipart_chunksize=8 * 1024 * 1024,
                    max_concurrency=10,
                    use_threads=True
                )
                s3.upload_file(tmp.name, AWS_TEMP_BUCKET, object_key, Config=config)
                os.unlink(tmp.name)  # Delete temp file
                
            cloud_path = f"s3://{AWS_TEMP_BUCKET}/{object_key}"
            current_app.logger.info(f"Uploaded file to S3: {cloud_path}")
            
        else:  # upload_to == 'gcp'
            if not storage_client:
                return jsonify({'success': False, 'error': 'GCP Storage client not initialized - credentials missing. Please set GCP_SERVICE_ACCOUNT_KEY environment variable.'}), 500
                
            # Upload to GCS
            bucket = storage_client.bucket(GCP_TEMP_BUCKET)
            blob = bucket.blob(object_key)
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                file.save(tmp.name)
                blob.upload_from_filename(tmp.name)
                os.unlink(tmp.name)  # Delete temp file
                
            cloud_path = f"gs://{GCP_TEMP_BUCKET}/{object_key}"
            current_app.logger.info(f"Uploaded file to GCS: {cloud_path}")
            
        return jsonify({'success': True, 'path': cloud_path, 'session_id': session_id})
        
    except Exception as e:
        current_app.logger.error(f"Error uploading file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 