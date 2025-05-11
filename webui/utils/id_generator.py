#!/usr/bin/env python3
"""
ID Generator Module

Provides utility functions for generating unique task and session IDs.
"""

import uuid
import time


def generate_task_id(prefix="task"):
    """
    Generate a unique task ID using UUID4.
    
    Args:
        prefix (str): Optional prefix for the task ID
        
    Returns:
        str: A unique task ID in the format "{prefix}-{uuid4}"
    """
    unique_id = str(uuid.uuid4())
    return f"{prefix}-{unique_id}"


def generate_session_id(prefix="session"):
    """
    Generate a unique session ID using timestamp and UUID4.
    
    Args:
        prefix (str): Optional prefix for the session ID
        
    Returns:
        str: A unique session ID in the format "{prefix}-{timestamp}-{uuid4_short}"
    """
    timestamp = int(time.time())
    unique_part = str(uuid.uuid4()).split('-')[0]  # Use just the first part of UUID for brevity
    return f"{prefix}-{timestamp}-{unique_part}"


def is_valid_uuid(id_string):
    """
    Check if a string is a valid UUID.
    
    Args:
        id_string (str): The string to validate
        
    Returns:
        bool: True if the string is a valid UUID, False otherwise
    """
    try:
        uuid_obj = uuid.UUID(id_string)
        return True
    except (ValueError, AttributeError):
        return False


def extract_uuid_from_task_id(task_id):
    """
    Extract the UUID part from a task ID.
    
    Args:
        task_id (str): Task ID in the format "{prefix}-{uuid}"
        
    Returns:
        str: The UUID part of the task ID, or None if the format is invalid
    """
    if not task_id or '-' not in task_id:
        return None
        
    parts = task_id.split('-', 1)
    if len(parts) != 2:
        return None
        
    uuid_part = parts[1]
    if is_valid_uuid(uuid_part):
        return uuid_part
    return None 