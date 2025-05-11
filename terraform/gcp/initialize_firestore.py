#!/usr/bin/env python3
"""
Script to verify and initialize Firestore collection for task status tracking.
Firestore collections are created on-the-fly, but this script verifies connectivity
and can set up initial documents if needed.

Usage:
    python3 initialize_firestore.py [--collection-name COLLECTION] [--project-id PROJECT_ID]
"""

import argparse
import sys
from google.cloud import firestore
import google.auth.exceptions
import google.api_core.exceptions

def verify_firestore_collection(collection_name='tasks', project_id=None):
    """
    Verifies Firestore connectivity and collection existence.
    Firestore collections are created on demand, so this mostly checks credentials.
    
    The collection will have documents with attributes:
    - task_id: Unique identifier for the task
    - session_id: Session identifier for grouping tasks
    - source_path: Source file path
    - action: Processing action
    - output_path: Output file path
    - status: Task status (PENDING, RUNNING, SUCCESS, FAILED)
    - timestamp: When the task was submitted
    - message: Additional status information or error messages
    """
    print(f"Verifying Firestore collection '{collection_name}'...")
    
    try:
        # Initialize Firestore client
        db = firestore.Client(project=project_id)
        
        # Create a test document
        test_ref = db.collection(collection_name).document('test-init')
        test_ref.set({
            'test': True,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'note': 'This is a test document to verify collection setup'
        })
        
        # Read the test document
        test_doc = test_ref.get()
        if test_doc.exists:
            print(f"Successfully verified Firestore collection: {collection_name}")
            
            # Delete the test document
            test_ref.delete()
            print("Test document deleted")
            
            return True
        else:
            print("Error: Test document was not created")
            return False
            
    except google.auth.exceptions.DefaultCredentialsError:
        print("Error: GCP credentials not found. Make sure GOOGLE_APPLICATION_CREDENTIALS is set.")
        return False
        
    except google.api_core.exceptions.PermissionDenied:
        print("Error: Permission denied. Check your service account permissions.")
        return False
        
    except Exception as e:
        print(f"Error verifying Firestore collection: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Initialize Firestore collection for task status tracking')
    parser.add_argument('--collection-name', default='tasks', help='Name of the Firestore collection')
    parser.add_argument('--project-id', help='GCP project ID')
    
    args = parser.parse_args()
    
    if verify_firestore_collection(args.collection_name, args.project_id):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main() 