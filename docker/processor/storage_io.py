#!/usr/bin/env python3
"""
Multi-Cloud File Upload Module

This module:
1. Uploads files to AWS S3 and GCP Cloud Storage
2. Supports various upload options like content-type, ACL, etc.
3. Provides verification and progress tracking
"""

import os
import logging
import mimetypes
from typing import Dict, Any, Optional, Callable, Union

# Configure logging
logger = logging.getLogger("storage_io")

def upload_file(source_path: str, destination_uri: str, 
               params: Dict[str, Any] = None) -> bool:
    """
    Upload a file to S3 or GCS
    Args:
        source_path: Path to the local file
        destination_uri: Destination URI (s3:// or gs://)
        params: Optional parameters:
            - content_type: MIME type of the file
            - acl: Access control (e.g., 'public-read', 'private')
            - metadata: Custom metadata for the object
            - progress_callback: Function to call with progress updates
    Returns:
        True if the upload was successful, False otherwise
    """
    if not os.path.exists(source_path):
        logger.error(f"Source file not found: {source_path}")
        return False
    if params is None:
        params = {}
    if destination_uri.startswith('s3://'):
        return upload_to_s3(source_path, destination_uri, params)
    elif destination_uri.startswith('gs://'):
        return upload_to_gcs(source_path, destination_uri, params)
    else:
        logger.error(f"Unsupported destination URI scheme: {destination_uri}")
        return False

def upload_to_s3(source_path: str, destination_uri: str, 
                params: Dict[str, Any]) -> bool:
    """
    Upload a file to Amazon S3 using TransferConfig for multipart/multithreaded upload
    """
    try:
        import boto3
        from boto3.s3.transfer import TransferConfig
        from botocore.exceptions import ClientError
        s3_path = destination_uri[5:]
        bucket_name, key = s3_path.split('/', 1)
        content_type = params.get('content_type')
        if not content_type:
            content_type, _ = mimetypes.guess_type(source_path)
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        acl = params.get('acl')
        if acl:
            extra_args['ACL'] = acl
        metadata = params.get('metadata')
        if metadata:
            extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}
        s3_client = boto3.client('s3')
        config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,
            multipart_chunksize=8 * 1024 * 1024,
            max_concurrency=10,
            use_threads=True
        )
        progress_callback = params.get('progress_callback')
        callback = None
        if progress_callback and callable(progress_callback):
            file_size = os.path.getsize(source_path)
            def s3_progress(bytes_transferred):
                progress_percent = (bytes_transferred * 100) / file_size
                progress_callback(progress_percent)
            callback = s3_progress
        logger.info(f"Uploading {source_path} to s3://{bucket_name}/{key}")
        s3_client.upload_file(
            source_path,
            bucket_name,
            key,
            ExtraArgs=extra_args,
            Config=config,
            Callback=callback
        )
        logger.info(f"Successfully uploaded to s3://{bucket_name}/{key}")
        return True
    except ImportError:
        logger.error("boto3 library not installed, cannot upload to S3")
        return False
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        return False

def upload_to_gcs(source_path: str, destination_uri: str, 
                 params: Dict[str, Any]) -> bool:
    """
    Upload a file to Google Cloud Storage
    Args:
        source_path: Path to the local file
        destination_uri: GCS URI (gs://bucket/blob)
        params: Upload parameters
    Returns:
        True if upload was successful, False otherwise
    """
    try:
        from google.cloud import storage
        gs_path = destination_uri[5:]
        bucket_name, blob_name = gs_path.split('/', 1)
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        content_type = params.get('content_type')
        if not content_type:
            content_type, _ = mimetypes.guess_type(source_path)
        if content_type:
            blob.content_type = content_type
        metadata = params.get('metadata')
        if metadata:
            blob.metadata = {k: str(v) for k, v in metadata.items()}
        progress_callback = params.get('progress_callback')
        if progress_callback and callable(progress_callback):
            file_size = os.path.getsize(source_path)
            chunk_size = 5 * 1024 * 1024
            blob.chunk_size = chunk_size
            def track_upload_progress(bytes_uploaded):
                progress_percent = (bytes_uploaded * 100) / file_size
                progress_callback(progress_percent)
            logger.info(f"Uploading {source_path} to gs://{bucket_name}/{blob_name}")
            with open(source_path, 'rb') as f:
                blob.upload_from_file(
                    f,
                    size=file_size,
                    num_retries=3
                )
                progress_callback(100)
        else:
            logger.info(f"Uploading {source_path} to gs://{bucket_name}/{blob_name}")
            blob.upload_from_filename(source_path)
        acl = params.get('acl')
        if acl:
            if acl == 'public-read':
                blob.make_public()
        logger.info(f"Successfully uploaded to gs://{bucket_name}/{blob_name}")
        return True
    except ImportError:
        logger.error("google-cloud-storage library not installed, cannot upload to GCS")
        return False
    except Exception as e:
        logger.error(f"Error uploading to GCS: {str(e)}")
        return False

def check_exists(uri: str) -> bool:
    """
    Check if a file exists in S3 or GCS
    Args:
        uri: URI to check (s3:// or gs://)
    Returns:
        True if the file exists, False otherwise
    """
    try:
        if uri.startswith('s3://'):
            import boto3
            from botocore.exceptions import ClientError
            s3_path = uri[5:]
            bucket_name, key = s3_path.split('/', 1)
            s3_client = boto3.client('s3')
            try:
                s3_client.head_object(Bucket=bucket_name, Key=key)
                return True
            except ClientError as e:
                return False
        elif uri.startswith('gs://'):
            from google.cloud import storage
            gs_path = uri[5:]
            bucket_name, blob_name = gs_path.split('/', 1)
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.exists()
        else:
            logger.error(f"Unsupported URI scheme: {uri}")
            return False
    except Exception as e:
        logger.error(f"Error checking if file exists: {str(e)}")
        return False

def download_file(uri: str, destination_path: str, 
                 params: Dict[str, Any] = None) -> bool:
    """
    Download a file from S3 or GCS using TransferConfig for S3
    """
    if params is None:
        params = {}
    try:
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        if uri.startswith('s3://'):
            import boto3
            from boto3.s3.transfer import TransferConfig
            s3_path = uri[5:]
            bucket_name, key = s3_path.split('/', 1)
            s3_client = boto3.client('s3')
            config = TransferConfig(
                multipart_threshold=8 * 1024 * 1024,
                multipart_chunksize=8 * 1024 * 1024,
                max_concurrency=10,
                use_threads=True
            )
            progress_callback = params.get('progress_callback')
            callback = None
            if progress_callback and callable(progress_callback):
                response = s3_client.head_object(Bucket=bucket_name, Key=key)
                file_size = response['ContentLength']
                def s3_progress(bytes_transferred):
                    progress_percent = (bytes_transferred * 100) / file_size
                    progress_callback(progress_percent)
                callback = s3_progress
            logger.info(f"Downloading s3://{bucket_name}/{key} to {destination_path}")
            s3_client.download_file(
                bucket_name,
                key,
                destination_path,
                Config=config,
                Callback=callback
            )
            logger.info(f"Successfully downloaded to {destination_path}")
            return True
        elif uri.startswith('gs://'):
            from google.cloud import storage
            gs_path = uri[5:]
            bucket_name, blob_name = gs_path.split('/', 1)
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            logger.info(f"Downloading gs://{bucket_name}/{blob_name} to {destination_path}")
            blob.download_to_filename(destination_path)
            progress_callback = params.get('progress_callback')
            if progress_callback and callable(progress_callback):
                progress_callback(100)
            logger.info(f"Successfully downloaded to {destination_path}")
            return True
        else:
            logger.error(f"Unsupported URI scheme: {uri}")
            return False
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return False 