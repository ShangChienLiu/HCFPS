"""
This file imports from routes/validate_path.py to maintain backward compatibility.
In future updates, the implementation should be moved directly to this location.
"""

from flask import Blueprint, request, jsonify, current_app
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from google.cloud import storage
from google.cloud.exceptions import NotFound
import os
import logging

# Get environment variables
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')

# Setup logger
logger = logging.getLogger('validate_path')

# Initialize AWS and GCP clients
s3 = None
storage_client = None

# Initialize S3 client
try:
    s3 = boto3.client('s3', region_name=AWS_REGION)
    logger.info("AWS S3 client initialized successfully")
except NoCredentialsError:
    logger.error("AWS credentials not found. S3 client initialization failed.")
except Exception as e:
    logger.error(f"Error initializing AWS S3 client: {e}")

# Initialize GCP client
try:
    GCP_SERVICE_ACCOUNT_KEY = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
    if GCP_SERVICE_ACCOUNT_KEY:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GCP_SERVICE_ACCOUNT_KEY
        storage_client = storage.Client()
        logger.info("GCP Storage client initialized with provided service account key")
    else:
        # Only try default credentials if specifically requested
        if os.environ.get('USE_GCP_DEFAULT_CREDENTIALS', '').lower() == 'true':
            storage_client = storage.Client()
            logger.info("GCP Storage client initialized with default credentials")
        else:
            logger.warning("Skipping GCP storage client initialization - no credentials provided")
except Exception as e:
    logger.error(f"Error initializing GCP storage client: {e}")

# Create blueprint
validate_path_blueprint = Blueprint('validate_path', __name__)

@validate_path_blueprint.route('/api/validate_path', methods=['POST'])
def validate_path():
    """
    Validates if a cloud path (s3:// or gs://) exists.
    For 'source' mode: check full path (bucket + object).
    For 'output' mode: check only bucket existence.
    """
    try:
        data = request.get_json()
        path = data.get('path')
        mode = data.get('mode', 'source')  # 'source' or 'output'
        logger.info(f"Validating path: {path}, mode: {mode}")

        if not path:
            return jsonify({'success': False, 'error': 'No path provided'}), 400

        check_bucket_only = (mode == 'output')

        if path.startswith('s3://'):
            if not s3:
                return jsonify({
                    'success': False, 
                    'error': 'AWS S3 client not initialized. Check your AWS credentials.',
                    'client_status': 'not_initialized'
                }), 500
            parts = path[5:].split('/', 1)
            bucket = parts[0]
            if check_bucket_only:
                try:
                    s3.head_bucket(Bucket=bucket)
                    logger.info(f"S3 bucket exists: {bucket}")
                    return jsonify({'success': True, 'exists': True, 'bucket': bucket})
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code')
                    if error_code == '404':
                        return jsonify({'success': True, 'exists': False, 'bucket': bucket, 'reason': 'bucket_not_found'})
                    elif error_code == '403':
                        return jsonify({'success': True, 'exists': False, 'bucket': bucket, 'reason': 'access_denied'})
                    else:
                        return jsonify({'success': False, 'error': str(e), 'error_code': error_code}), 500
            else:
                if len(parts) < 2:
                    return jsonify({'success': False, 'error': 'Invalid S3 path format. Must be s3://bucket/key', 'validation_error': 'invalid_format'}), 400
                key = parts[1]
                try:
                    s3.head_object(Bucket=bucket, Key=key)
                    return jsonify({'success': True, 'exists': True, 'bucket': bucket, 'key': key})
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code')
                    if error_code == '404':
                        return jsonify({'success': True, 'exists': False, 'bucket': bucket, 'key': key, 'reason': 'object_not_found'})
                    elif error_code == '403':
                        return jsonify({'success': True, 'exists': False, 'bucket': bucket, 'key': key, 'reason': 'access_denied'})
                    else:
                        return jsonify({'success': False, 'error': str(e), 'error_code': error_code}), 500

        elif path.startswith('gs://'):
            if not storage_client:
                return jsonify({
                    'success': False, 
                    'error': 'GCP Storage client not initialized. Check your GCP credentials.',
                    'client_status': 'not_initialized'
                }), 500
            parts = path[5:].split('/', 1)
            bucket_name = parts[0]
            if check_bucket_only:
                try:
                    bucket = storage_client.bucket(bucket_name)
                    bucket.reload()
                    return jsonify({'success': True, 'exists': True, 'bucket': bucket_name})
                except NotFound:
                    return jsonify({'success': True, 'exists': False, 'bucket': bucket_name, 'reason': 'bucket_not_found'})
                except Exception as e:
                    return jsonify({'success': True, 'exists': False, 'bucket': bucket_name, 'reason': 'error', 'error': str(e)})
            else:
                if len(parts) < 2:
                    return jsonify({'success': False, 'error': 'Invalid GCS path format. Must be gs://bucket/object', 'validation_error': 'invalid_format'}), 400
                blob_name = parts[1]
                try:
                    bucket = storage_client.bucket(bucket_name)
                    blob = bucket.blob(blob_name)
                    exists = blob.exists()
                    if exists:
                        return jsonify({'success': True, 'exists': True, 'bucket': bucket_name, 'blob': blob_name})
                    else:
                        return jsonify({'success': True, 'exists': False, 'bucket': bucket_name, 'blob': blob_name, 'reason': 'object_not_found'})
                except NotFound:
                    return jsonify({'success': True, 'exists': False, 'bucket': bucket_name, 'blob': blob_name, 'reason': 'object_not_found'})
                except Exception as e:
                    return jsonify({'success': False, 'error': str(e)}), 500
        else:
            return jsonify({'success': False, 'error': 'Unsupported path format. Must start with s3:// or gs://', 'validation_error': 'unsupported_format'}), 400
    except Exception as e:
        logger.error(f"Error validating path: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 