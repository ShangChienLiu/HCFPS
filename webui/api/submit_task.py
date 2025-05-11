"""
This file imports from routes/submit_tasks.py to maintain backward compatibility.
In future updates, the implementation should be moved directly to this location.
"""

from flask import Blueprint, request, jsonify, current_app
import boto3
import json
import os
import time
import uuid
from google.cloud import pubsub_v1
from google.cloud import firestore
import logging

logger = logging.getLogger("webui.submit_task")

# Get environment variables
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL')
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
GCP_PUBSUB_TOPIC = os.environ.get('GCP_PUBSUB_TOPIC')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')
FIRESTORE_COLLECTION = os.environ.get('FIRESTORE_COLLECTION')

# Initialize AWS and GCP clients
sqs = boto3.client('sqs', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
publisher = None
topic_path = None
firestore_client = None

try:
    GCP_SERVICE_ACCOUNT_KEY = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
    
    if GCP_SERVICE_ACCOUNT_KEY:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GCP_SERVICE_ACCOUNT_KEY
    
    if GCP_PROJECT_ID:
        # Initialize Firestore client
        try:
            firestore_client = firestore.Client(project=GCP_PROJECT_ID)
            logger.info(f"Firestore initialized for project: {GCP_PROJECT_ID}")
        except Exception as firestore_error:
            logger.error(f"Error initializing Firestore: {firestore_error}")
    
    if GCP_PROJECT_ID and GCP_PUBSUB_TOPIC:
        logger.info(f"Initializing GCP Pub/Sub with Project ID: {GCP_PROJECT_ID}, Topic: {GCP_PUBSUB_TOPIC}")
        
        # Validate project ID and topic format
        if not GCP_PROJECT_ID.strip() or not GCP_PUBSUB_TOPIC.strip():
            logger.error("Error: GCP Project ID or Topic name is empty after stripping")
        elif '/' in GCP_PUBSUB_TOPIC:
            logger.warning(f"Warning: GCP_PUBSUB_TOPIC contains slash - should be only the topic name, not the full path")
            # Extract just the topic name
            GCP_PUBSUB_TOPIC = GCP_PUBSUB_TOPIC.split('/')[-1]
            logger.info(f"Using topic name: {GCP_PUBSUB_TOPIC}")
        
        if os.environ.get('USE_GCP_DEFAULT_CREDENTIALS', '').lower() == 'true' or GCP_SERVICE_ACCOUNT_KEY:
            try:
                publisher = pubsub_v1.PublisherClient()
                topic_path = publisher.topic_path(GCP_PROJECT_ID, GCP_PUBSUB_TOPIC)
                logger.info(f"GCP Pub/Sub initialized for topic: {topic_path}")
            except Exception as pubsub_error:
                logger.error(f"Error creating Pub/Sub topic path: {pubsub_error}")
        else:
            logger.info("Skipping GCP Pub/Sub initialization - no credentials provided")
except Exception as e:
    logger.error(f"Error initializing GCP Pub/Sub client: {e}")

# Create blueprint
submit_tasks_blueprint = Blueprint('submit_tasks', __name__)

def save_task_to_dynamodb(task_data, task_id):
    """Write task record to DynamoDB for tracking"""
    try:
        if not DYNAMODB_TABLE:
            logger.error("DynamoDB table name not configured")
            return False
        
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        # Add task_id and status fields
        item = {
            'task_id': task_id,
            'session_id': task_data.get('session_id'),
            'source_path': task_data.get('source_path'),
            'action': task_data.get('action'),
            'output_path': task_data.get('output_path'),
            'status': 'PENDING',
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        
        table.put_item(Item=item)
        logger.info(f"Task record saved to DynamoDB: {task_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving task to DynamoDB: {e}")
        return False

def save_task_to_firestore(task_data, task_id):
    """Write task record to Firestore for tracking"""
    try:
        if not firestore_client or not FIRESTORE_COLLECTION:
            logger.error("Firestore client or collection name not configured")
            return False
        
        # Add task_id and status fields
        doc_data = {
            'task_id': task_id,
            'session_id': task_data.get('session_id'),
            'source_path': task_data.get('source_path'),
            'action': task_data.get('action'),
            'output_path': task_data.get('output_path'),
            'status': 'PENDING',
            'created_at': time.time(),
            'updated_at': time.time()
        }
        
        collection_ref = firestore_client.collection(FIRESTORE_COLLECTION)
        collection_ref.document(task_id).set(doc_data)
        logger.info(f"Task record saved to Firestore: {task_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving task to Firestore: {e}")
        return False

@submit_tasks_blueprint.route('/api/submit_task', methods=['POST'])
def submit_task():
    """
    Submits a batch of tasks for processing.
    """
    try:
        data = request.get_json()
        tasks = data.get('tasks', [])
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not tasks:
            return jsonify({'success': False, 'error': 'No tasks provided'}), 400
            
        successful = 0
        failed = 0
        errors = []
        
        # Process each task
        for task in tasks:
            try:
                source_type = task.get('source_type')
                source_path = task.get('source_path')
                action = task.get('action')
                output_path = task.get('output_path')
                
                # Skip tasks with missing required fields
                if not source_path or not action or not output_path:
                    failed += 1
                    errors.append(f"Task missing required fields: {task}")
                    continue
                
                # Generate a unique task ID
                task_id = str(uuid.uuid4())
                
                # Determine the target platform based on the source path
                if source_path.startswith('s3://'):
                    # Send to AWS SQS
                    if not SQS_QUEUE_URL:
                        failed += 1
                        errors.append(f"AWS SQS URL not configured for task: {source_path}")
                        continue
                    
                    task_data = {
                        'task_id': task_id,
                        'source_type': source_type,
                        'source_path': source_path,
                        'action': action,
                        'output_path': output_path,
                        'session_id': session_id,
                        'timestamp': time.time()
                    }
                    
                    # Save task to DynamoDB for tracking
                    save_task_to_dynamodb(task_data, task_id)
                    
                    sqs_response = sqs.send_message(
                        QueueUrl=SQS_QUEUE_URL,
                        MessageBody=json.dumps(task_data)
                    )
                    logger.info(f"Sent task to AWS SQS: {sqs_response.get('MessageId')}")
                    successful += 1
                    
                elif source_path.startswith('gs://'):
                    # Send to GCP Pub/Sub
                    if not publisher or not topic_path:
                        failed += 1
                        errors.append(f"GCP Pub/Sub not configured for task: {source_path}. Please set GCP_SERVICE_ACCOUNT_KEY environment variable.")
                        continue
                    
                    task_data = {
                        'task_id': task_id,
                        'source_type': source_type,
                        'source_path': source_path,
                        'action': action,
                        'output_path': output_path,
                        'session_id': session_id,
                        'timestamp': time.time()
                    }
                    
                    # Save task to Firestore for tracking
                    save_task_to_firestore(task_data, task_id)
                    
                    data_bytes = json.dumps(task_data).encode('utf-8')
                    pubsub_future = publisher.publish(
                        topic_path, 
                        data=data_bytes,
                        origin="web_ui",
                        content_type="application/json"
                    )
                    pubsub_id = pubsub_future.result()
                    logger.info(f"Sent task to GCP Pub/Sub: {pubsub_id}")
                    successful += 1
                    
                else:
                    failed += 1
                    errors.append(f"Invalid source path format: {source_path}")
                
            except Exception as e:
                failed += 1
                errors.append(f"Error processing task: {str(e)}")
                logger.error(f"Error processing task: {e}")
                
        return jsonify({
            'success': True,
            'total': len(tasks),
            'successful': successful,
            'failed': failed,
            'errors': errors[:5] if errors else [],  # Limit number of errors returned
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error in submit_task: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 