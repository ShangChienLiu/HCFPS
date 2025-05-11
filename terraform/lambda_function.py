import json
import os
import boto3
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sqs_client = boto3.client('sqs')
dynamodb_client = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

# Get environment variables
DLQ_URL = os.environ.get('DLQ_URL')
MAIN_QUEUE_URL = os.environ.get('MAIN_QUEUE_URL')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    """
    Lambda function to process messages from DLQ
    
    This function:
    1. Reads messages from the DLQ
    2. Analyzes the failure reason
    3. Updates the task status in DynamoDB
    4. Optionally requeues fixable messages
    5. Sends notification for non-fixable errors
    """
    logger.info(f"Starting DLQ processing at {datetime.now().isoformat()}")
    
    # Get the DynamoDB table
    task_table = dynamodb_client.Table(DYNAMODB_TABLE_NAME)
    
    # Retrieve messages from DLQ
    response = sqs_client.receive_message(
        QueueUrl=DLQ_URL,
        MaxNumberOfMessages=10,
        VisibilityTimeout=60,
        WaitTimeSeconds=5,
        AttributeNames=['All'],
        MessageAttributeNames=['All']
    )
    
    messages = response.get('Messages', [])
    logger.info(f"Retrieved {len(messages)} messages from DLQ")
    
    if not messages:
        return {
            'statusCode': 200,
            'body': json.dumps('No messages in DLQ')
        }
    
    # Process each message
    for message in messages:
        message_id = message['MessageId']
        receipt_handle = message['ReceiptHandle']
        
        try:
            # Parse message body
            body = json.loads(message['Body'])
            task_id = body.get('task_id')
            
            if not task_id:
                logger.error(f"Message {message_id} has no task_id, skipping")
                delete_message(DLQ_URL, receipt_handle)
                continue
            
            # Get failure information
            approximate_receive_count = int(message['Attributes'].get('ApproximateReceiveCount', 0))
            error_type = get_error_type(body, message)
            
            # Update task status in DynamoDB
            update_task_status(task_table, task_id, error_type, approximate_receive_count)
            
            # Determine if task should be requeued or is permanently failed
            if is_retriable_error(error_type) and approximate_receive_count <= 3:
                # Requeue the message to the main queue
                requeue_message(MAIN_QUEUE_URL, body)
                logger.info(f"Requeued task {task_id} to main queue")
            else:
                # Send notification for permanent failure
                send_failure_notification(task_id, error_type, body)
                logger.info(f"Task {task_id} permanently failed: {error_type}")
            
            # Delete from DLQ after processing
            delete_message(DLQ_URL, receipt_handle)
            
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {str(e)}")
            # Don't delete the message so it can be retried later
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Processed {len(messages)} DLQ messages')
    }

def get_error_type(body, message):
    """Determine the type of error from the message"""
    # Check if error type is included in the message
    if 'error_type' in body:
        return body['error_type']
    
    # Otherwise try to infer from the message
    original_body = body.get('original_message', {})
    source_path = original_body.get('source_path', '')
    
    if 'access denied' in str(message).lower():
        return 'PERMISSION_ERROR'
    elif 'not found' in str(message).lower():
        return 'NOT_FOUND_ERROR'
    elif source_path.startswith('s3://') and 'NoSuchKey' in str(message):
        return 'S3_FILE_NOT_FOUND'
    elif source_path.startswith('gs://') and 'does not exist' in str(message):
        return 'GCS_FILE_NOT_FOUND'
    elif 'timeout' in str(message).lower():
        return 'TIMEOUT_ERROR'
    else:
        return 'UNKNOWN_ERROR'

def is_retriable_error(error_type):
    """Determine if an error type is retriable"""
    retriable_errors = [
        'TIMEOUT_ERROR',
        'TEMPORARY_FAILURE',
        'CONNECTION_ERROR',
        'RATE_LIMIT_ERROR'
    ]
    return error_type in retriable_errors

def update_task_status(table, task_id, error_type, retry_count):
    """Update the task status in DynamoDB"""
    try:
        table.update_item(
            Key={'task_id': task_id},
            UpdateExpression='SET #status = :status, error_type = :error_type, retry_count = :retry_count, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'FAILED',
                ':error_type': error_type,
                ':retry_count': retry_count,
                ':updated_at': datetime.now().isoformat()
            }
        )
        logger.info(f"Updated task {task_id} status to FAILED with error_type {error_type}")
    except Exception as e:
        logger.error(f"Error updating task {task_id} in DynamoDB: {str(e)}")

def requeue_message(queue_url, original_message):
    """Requeue a message to the main processing queue"""
    try:
        # Add a retry flag to the message
        if 'retries' in original_message:
            original_message['retries'] += 1
        else:
            original_message['retries'] = 1
        
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(original_message)
        )
        return response
    except Exception as e:
        logger.error(f"Error requeuing message: {str(e)}")
        return None

def delete_message(queue_url, receipt_handle):
    """Delete a message from a queue"""
    try:
        sqs_client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting message: {str(e)}")
        return False

def send_failure_notification(task_id, error_type, task_details):
    """Send an SNS notification for a permanently failed task"""
    try:
        message = {
            'task_id': task_id,
            'error_type': error_type,
            'task_details': task_details,
            'timestamp': datetime.now().isoformat()
        }
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Task Failed: {task_id}",
            Message=json.dumps(message, indent=2)
        )
        return True
    except Exception as e:
        logger.error(f"Error sending SNS notification: {str(e)}")
        return False 