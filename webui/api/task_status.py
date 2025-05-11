"""
This file imports from routes/task_status.py to maintain backward compatibility.
In future updates, the implementation should be moved directly to this location.
"""

from flask import Blueprint, request, jsonify, current_app
import os
import uuid
import boto3
from google.cloud import firestore
import logging

# Create blueprint
task_status_blueprint = Blueprint('task_status', __name__)

@task_status_blueprint.route('/api/task_status', methods=['POST'])
def task_status():
    """
    Endpoint to check the status of submitted tasks.
    Queries both AWS DynamoDB and GCP Firestore based on the session_id.
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400
        
        # Get logger and configuration
        logger = current_app.logger
        AWS_REGION = current_app.config.get('AWS_REGION')
        DYNAMODB_TABLE = current_app.config.get('DYNAMODB_TABLE')
        GCP_PROJECT_ID = current_app.config.get('GCP_PROJECT_ID')
        FIRESTORE_COLLECTION = current_app.config.get('FIRESTORE_COLLECTION', 'tasks')
        
        # Initialize response data
        tasks = []
        aws_status = 'unknown'
        gcp_status = 'unknown'
        overall_status = 'unknown'
        error_messages = []
        
        # Query AWS DynamoDB for tasks
        try:
            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table(DYNAMODB_TABLE)
            response = table.query(
                IndexName='SessionIdIndex',  # Assuming there's a GSI on session_id
                KeyConditionExpression=boto3.dynamodb.conditions.Key('session_id').eq(session_id)
            )
            
            if 'Items' in response:
                for item in response['Items']:
                    tasks.append({
                        'task_id': item.get('task_id'),
                        'source_path': item.get('source_path'),
                        'action': item.get('action'),
                        'output_path': item.get('output_path'),
                        'status': item.get('status', 'PENDING'),
                        'platform': 'aws',
                        'message': item.get('message', ''),
                        'timestamp': item.get('timestamp', '')
                    })
                
                if tasks:
                    aws_status = 'fetched'
                    logger.info(f"Retrieved {len(tasks)} AWS tasks for session: {session_id}")
                else:
                    aws_status = 'no_tasks'
                    
        except Exception as e:
            aws_status = 'error'
            error_message = f"Error querying DynamoDB: {str(e)}"
            error_messages.append(error_message)
            logger.error(error_message)
        
        # Query GCP Firestore for tasks
        try:
            if GCP_PROJECT_ID:
                firestore_client = firestore.Client(project=GCP_PROJECT_ID)
                task_collection = firestore_client.collection(FIRESTORE_COLLECTION)
                query = task_collection.where('session_id', '==', session_id)
                docs = query.stream()
                
                gcp_tasks = []
                for doc in docs:
                    task_data = doc.to_dict()
                    gcp_tasks.append({
                        'task_id': doc.id,
                        'source_path': task_data.get('source_path'),
                        'action': task_data.get('action'),
                        'output_path': task_data.get('output_path'),
                        'status': task_data.get('status', 'PENDING'),
                        'platform': 'gcp',
                        'message': task_data.get('message', ''),
                        'timestamp': task_data.get('timestamp', '')
                    })
                
                tasks.extend(gcp_tasks)
                
                if gcp_tasks:
                    gcp_status = 'fetched'
                    logger.info(f"Retrieved {len(gcp_tasks)} GCP tasks for session: {session_id}")
                else:
                    gcp_status = 'no_tasks'
            else:
                gcp_status = 'not_configured'
                
        except Exception as e:
            gcp_status = 'error'
            error_message = f"Error querying Firestore: {str(e)}"
            error_messages.append(error_message)
            logger.error(error_message)
        
        # Determine overall status
        if tasks:
            # Count tasks by status
            status_counts = {}
            for task in tasks:
                task_status = task.get('status', 'PENDING')
                status_counts[task_status] = status_counts.get(task_status, 0) + 1
            
            total_tasks = len(tasks)
            
            # Determine overall status based on task counts
            if status_counts.get('FAILED', 0) == total_tasks:
                overall_status = 'failed'
            elif status_counts.get('SUCCESS', 0) == total_tasks:
                overall_status = 'completed'
            elif status_counts.get('PENDING', 0) == total_tasks:
                overall_status = 'pending'
            elif status_counts.get('RUNNING', 0) > 0:
                overall_status = 'processing'
            else:
                overall_status = 'mixed'
        else:
            if aws_status == 'error' and gcp_status == 'error':
                overall_status = 'error'
            else:
                overall_status = 'not_found'
        
        # Return the combined results
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': overall_status,
            'aws_status': aws_status,
            'gcp_status': gcp_status,
            'total_tasks': len(tasks),
            'tasks': tasks,
            'errors': error_messages
        })
        
    except Exception as e:
        error_message = f"Error checking task status: {str(e)}"
        current_app.logger.error(error_message)
        return jsonify({'success': False, 'error': error_message}), 500 