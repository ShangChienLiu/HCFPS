#!/usr/bin/env python3
"""
Task Status Writer

This module:
1. Updates task status in AWS DynamoDB and GCP Firestore
2. Supports various status values (SUCCESS, FAILED, etc.)
3. Tracks error information and task metadata
"""

import os
import logging
import json
import datetime
import time
from typing import Dict, Any, Optional, Union

# Configure logging
logger = logging.getLogger("status_writer")

# Default values
DEFAULT_DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'task-tracking')
DEFAULT_FIRESTORE_COLLECTION = os.environ.get('FIRESTORE_COLLECTION', 'tasks')

def update_status(task_id: str, status: str, error_type: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Update task status in DynamoDB or Firestore
    
    Args:
        task_id: Unique identifier for the task
        status: Task status (SUCCESS, FAILED, PROCESSING, etc.)
        error_type: Error type if status is FAILED
        metadata: Additional metadata to store with the status
        config: Configuration options:
            - db_type: 'dynamodb', 'firestore', or 'both' (default: auto-detect based on env vars)
            - dynamodb_table: DynamoDB table name
            - firestore_collection: Firestore collection name
            
    Returns:
        True if update was successful, False otherwise
    """
    if not task_id:
        logger.error("Task ID is required to update status")
        return False
        
    # Default config
    if config is None:
        config = {}
        
    # Determine which database(s) to use
    db_type = config.get('db_type')
    if not db_type:
        # Auto-detect based on environment variables
        if 'AWS_REGION' in os.environ:
            if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                db_type = 'both'
            else:
                db_type = 'dynamodb'
        elif 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            db_type = 'firestore'
        else:
            logger.warning("No cloud credentials found, status update may fail")
            db_type = 'both'  # Try both and see what works
            
    # Build the status update payload
    timestamp = datetime.datetime.now().isoformat()
    update_data = {
        'status': status,
        'updated_at': timestamp
    }
    
    if error_type:
        update_data['error_type'] = error_type
        
    if metadata:
        update_data['metadata'] = metadata
        
    # Update in the appropriate database(s)
    result = True
    
    if db_type in ['dynamodb', 'both']:
        dynamodb_result = update_dynamodb_status(
            task_id=task_id,
            update_data=update_data,
            table_name=config.get('dynamodb_table', DEFAULT_DYNAMODB_TABLE)
        )
        result = result and dynamodb_result
        
    if db_type in ['firestore', 'both']:
        firestore_result = update_firestore_status(
            task_id=task_id,
            update_data=update_data,
            collection_name=config.get('firestore_collection', DEFAULT_FIRESTORE_COLLECTION)
        )
        result = result and firestore_result
        
    return result

def update_dynamodb_status(task_id: str, update_data: Dict[str, Any], 
                         table_name: str) -> bool:
    """
    Update task status in DynamoDB
    
    Args:
        task_id: Task ID
        update_data: Data to update
        table_name: DynamoDB table name
        
    Returns:
        True if update was successful, False otherwise
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        region = os.environ.get('AWS_REGION', 'us-west-2')
        dynamodb = boto3.resource('dynamodb', region_name=region)
        table = dynamodb.Table(table_name)
        
        # Prepare update expression and attribute values
        update_expression = "SET "
        expression_attribute_values = {}
        
        for key, value in update_data.items():
            # Handle special characters in attribute names
            attribute_name = f"#{key}"
            attribute_value = f":{key}"
            
            update_expression += f"{attribute_name} = {attribute_value}, "
            expression_attribute_values[attribute_value] = value
            
        # Remove trailing comma and space
        update_expression = update_expression[:-2]
        
        # Prepare expression attribute names
        expression_attribute_names = {
            f"#{key}": key for key in update_data.keys()
        }
        
        # Update the item
        logger.info(f"Updating task {task_id} in DynamoDB table {table_name}")
        table.update_item(
            Key={
                'task_id': task_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        logger.info(f"Successfully updated task {task_id} status to {update_data.get('status')}")
        return True
        
    except ImportError:
        logger.error("boto3 library not installed, cannot update DynamoDB")
        return False
    except Exception as e:
        logger.error(f"Error updating DynamoDB: {str(e)}")
        return False

def update_firestore_status(task_id: str, update_data: Dict[str, Any],
                          collection_name: str) -> bool:
    """
    Update task status in Firestore
    
    Args:
        task_id: Task ID
        update_data: Data to update
        collection_name: Firestore collection name
        
    Returns:
        True if update was successful, False otherwise
    """
    try:
        import os
        from google.cloud import firestore
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not cred_path or not os.path.isfile(cred_path):
            logger.error(f"GOOGLE_APPLICATION_CREDENTIALS is not set or file does not exist: {cred_path}")
            return False
        db = firestore.Client()
        
        # Get document reference
        doc_ref = db.collection(collection_name).document(task_id)
        
        # Convert datetime objects to Firestore timestamps
        processed_data = {}
        for key, value in update_data.items():
            if isinstance(value, datetime.datetime):
                from google.cloud.firestore import SERVER_TIMESTAMP
                processed_data[key] = SERVER_TIMESTAMP
            else:
                processed_data[key] = value
                
        # Update the document
        logger.info(f"Updating task {task_id} in Firestore collection {collection_name}")
        doc_ref.set(processed_data, merge=True)
        
        logger.info(f"Successfully updated task {task_id} status to {update_data.get('status')}")
        return True
        
    except ImportError:
        logger.error("google-cloud-firestore library not installed, cannot update Firestore")
        return False
    except Exception as e:
        logger.error(f"Error updating Firestore: {str(e)}")
        return False

def get_task_status(task_id: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get current task status from DynamoDB or Firestore
    
    Args:
        task_id: Task ID
        config: Configuration options (same as update_status)
        
    Returns:
        Task status data or empty dict if not found
    """
    if not task_id:
        logger.error("Task ID is required to get status")
        return {}
        
    # Default config
    if config is None:
        config = {}
        
    # Determine which database to use
    db_type = config.get('db_type')
    if not db_type:
        # Auto-detect based on environment variables
        if 'AWS_REGION' in os.environ:
            db_type = 'dynamodb'
        elif 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            db_type = 'firestore'
        else:
            logger.warning("No cloud credentials found, defaulting to DynamoDB")
            db_type = 'dynamodb'
            
    # Get from the appropriate database
    if db_type == 'dynamodb':
        return get_dynamodb_status(
            task_id=task_id,
            table_name=config.get('dynamodb_table', DEFAULT_DYNAMODB_TABLE)
        )
    else:  # db_type == 'firestore'
        return get_firestore_status(
            task_id=task_id,
            collection_name=config.get('firestore_collection', DEFAULT_FIRESTORE_COLLECTION)
        )

def get_dynamodb_status(task_id: str, table_name: str) -> Dict[str, Any]:
    """
    Get task status from DynamoDB
    
    Args:
        task_id: Task ID
        table_name: DynamoDB table name
        
    Returns:
        Task status data or empty dict if not found
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Create DynamoDB resource
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Get the item
        response = table.get_item(
            Key={
                'task_id': task_id
            }
        )
        
        # Return the item if found
        if 'Item' in response:
            return response['Item']
        else:
            logger.warning(f"Task {task_id} not found in DynamoDB")
            return {}
            
    except Exception as e:
        logger.error(f"Error getting status from DynamoDB: {str(e)}")
        return {}

def get_firestore_status(task_id: str, collection_name: str) -> Dict[str, Any]:
    """
    Get task status from Firestore
    
    Args:
        task_id: Task ID
        collection_name: Firestore collection name
        
    Returns:
        Task status data or empty dict if not found
    """
    try:
        from google.cloud import firestore
        
        # Create Firestore client
        db = firestore.Client()
        
        # Get document reference
        doc_ref = db.collection(collection_name).document(task_id)
        
        # Get the document
        doc = doc_ref.get()
        
        # Return the document data if it exists
        if doc.exists:
            return doc.to_dict()
        else:
            logger.warning(f"Task {task_id} not found in Firestore")
            return {}
            
    except Exception as e:
        logger.error(f"Error getting status from Firestore: {str(e)}")
        return {} 