#!/usr/bin/env python
"""
Database connection verification script.
Run this to test connections to both DynamoDB and Firestore.
"""

import os
import sys
import time
import uuid
import json
import boto3
from google.cloud import firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
print("Environment variables loaded")

# Set up colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def print_status(message, status):
    """Print colored status messages"""
    if status == "success":
        print(f"{GREEN}✓ {message}{RESET}")
    elif status == "warning":
        print(f"{YELLOW}⚠ {message}{RESET}")
    elif status == "error":
        print(f"{RED}✗ {message}{RESET}")
    else:
        print(message)

def check_aws_dynamodb():
    """Test connection to AWS DynamoDB"""
    print("\nTesting AWS DynamoDB connection...")
    
    # Check for required environment variables
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_REGION', 'us-west-2')
    table_name = os.environ.get('DYNAMODB_TABLE')
    
    if not aws_access_key or not aws_secret_key:
        print_status("AWS credentials not found in environment variables", "error")
        return False
    
    if not table_name:
        print_status("DynamoDB table name not specified", "error")
        return False
    
    print_status(f"Using AWS region: {aws_region}", "success")
    print_status(f"Using DynamoDB table: {table_name}", "success")
    
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource(
            'dynamodb',
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        
        # Get the table
        table = dynamodb.Table(table_name)
        
        # Test write and read operations
        test_id = str(uuid.uuid4())
        test_data = {
            'task_id': test_id,
            'session_id': 'test-session',
            'source_path': 's3://test-bucket/test-object',
            'action': 'test',
            'status': 'TEST',
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        
        # Write test item
        print("Writing test record to DynamoDB...")
        table.put_item(Item=test_data)
        
        # Read test item
        print("Reading test record from DynamoDB...")
        response = table.get_item(Key={'task_id': test_id})
        
        if 'Item' in response:
            print_status("Successfully read test record from DynamoDB", "success")
            
            # Clean up by deleting the test item
            print("Cleaning up test record...")
            table.delete_item(Key={'task_id': test_id})
            print_status("Test record deleted", "success")
            
            return True
        else:
            print_status("Could not read test record from DynamoDB", "error")
            return False
            
    except Exception as e:
        print_status(f"DynamoDB Error: {str(e)}", "error")
        return False

def check_gcp_firestore():
    """Test connection to GCP Firestore"""
    print("\nTesting GCP Firestore connection...")
    
    # Check for required environment variables
    gcp_project_id = os.environ.get('GCP_PROJECT_ID')
    gcp_service_account = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
    collection_name = os.environ.get('FIRESTORE_COLLECTION')
    
    if not gcp_project_id:
        print_status("GCP Project ID not found in environment variables", "error")
        return False
    
    if not collection_name:
        print_status("Firestore collection name not specified", "error")
        return False
    
    print_status(f"Using GCP Project ID: {gcp_project_id}", "success")
    print_status(f"Using Firestore collection: {collection_name}", "success")
    
    # Check service account key file
    if gcp_service_account:
        if os.path.exists(gcp_service_account):
            print_status(f"Service account key found: {gcp_service_account}", "success")
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcp_service_account
        else:
            print_status(f"Service account key file not found: {gcp_service_account}", "error")
            return False
    else:
        print_status("No service account key specified, using default credentials", "warning")
    
    try:
        # Initialize Firestore client
        db = firestore.Client(project=gcp_project_id)
        
        # Test write and read operations
        test_id = str(uuid.uuid4())
        test_data = {
            'task_id': test_id,
            'session_id': 'test-session',
            'source_path': 'gs://test-bucket/test-object',
            'action': 'test',
            'status': 'TEST',
            'created_at': time.time(),
            'updated_at': time.time()
        }
        
        # Write test document
        print("Writing test record to Firestore...")
        doc_ref = db.collection(collection_name).document(test_id)
        doc_ref.set(test_data)
        
        # Read test document
        print("Reading test record from Firestore...")
        doc = doc_ref.get()
        
        if doc.exists:
            print_status("Successfully read test record from Firestore", "success")
            
            # Clean up by deleting the test document
            print("Cleaning up test record...")
            doc_ref.delete()
            print_status("Test record deleted", "success")
            
            return True
        else:
            print_status("Could not read test record from Firestore", "error")
            return False
            
    except Exception as e:
        print_status(f"Firestore Error: {str(e)}", "error")
        return False

def main():
    """Main function to run all tests"""
    print("=== Database Connection Verification Tool ===")
    
    # Test AWS DynamoDB
    dynamodb_success = check_aws_dynamodb()
    
    # Test GCP Firestore
    firestore_success = check_gcp_firestore()
    
    # Summary
    print("\n=== Summary ===")
    if dynamodb_success:
        print_status("AWS DynamoDB: Connected successfully", "success")
    else:
        print_status("AWS DynamoDB: Connection failed", "error")
        
    if firestore_success:
        print_status("GCP Firestore: Connected successfully", "success")
    else:
        print_status("GCP Firestore: Connection failed", "error")
    
    if dynamodb_success and firestore_success:
        print_status("\nAll database connections successful! Your application is ready.", "success")
        return 0
    else:
        print_status("\nSome database connections failed. Please check the errors above.", "error")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 