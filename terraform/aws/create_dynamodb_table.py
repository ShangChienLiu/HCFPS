#!/usr/bin/env python3
"""
Script to create the DynamoDB table for task status tracking.
This script is used during deployment to create the table with the correct schema.

Usage:
    python3 create_dynamodb_table.py [--table-name TABLENAME] [--region REGION]
"""

import boto3
import argparse
import sys

def create_status_table(table_name='task_status', region='us-west-2'):
    """
    Creates a DynamoDB table for task status tracking with the following schema:
    - Primary key: task_id (string)
    - GSI: session_id (string) for querying by session ID
    
    The table will have attributes:
    - task_id: Unique identifier for the task
    - session_id: Session identifier for grouping tasks
    - source_path: Source file path
    - action: Processing action
    - output_path: Output file path
    - status: Task status (PENDING, RUNNING, SUCCESS, FAILED)
    - timestamp: When the task was submitted
    - message: Additional status information or error messages
    """
    print(f"Creating DynamoDB table '{table_name}' in region '{region}'...")
    
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.client('dynamodb', region_name=region)
        
        # Create table with primary key and GSI
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'task_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'task_id',
                    'AttributeType': 'S'  # String
                },
                {
                    'AttributeName': 'session_id',
                    'AttributeType': 'S'  # String
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'SessionIdIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'session_id',
                            'KeyType': 'HASH'  # Partition key
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'  # All attributes
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        print(f"DynamoDB table created successfully: {response['TableDescription']['TableName']}")
        return True
        
    except dynamodb.exceptions.ResourceInUseException:
        print(f"Table '{table_name}' already exists. Skipping creation.")
        return True
        
    except Exception as e:
        print(f"Error creating DynamoDB table: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Create DynamoDB table for task status tracking')
    parser.add_argument('--table-name', default='task_status', help='Name of the DynamoDB table')
    parser.add_argument('--region', default='us-west-2', help='AWS region')
    
    args = parser.parse_args()
    
    if create_status_table(args.table_name, args.region):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main() 