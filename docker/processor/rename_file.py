#!/usr/bin/env python3
"""
File Renaming Module

This module:
1. Renames files based on patterns
2. Supports placeholders like timestamps, UUIDs, etc.
3. Provides file renaming and copying operations
"""

import os
import logging
import shutil
import re
import uuid
import datetime
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger("rename_file")

def rename_file(input_path: str, output_path: str, params: Dict[str, Any] = None) -> bool:
    """
    Rename or copy a file with optional pattern replacements
    
    Args:
        input_path: Path to the input file
        output_path: Path to save the renamed file
        params: Optional parameters:
            - mode: 'copy' or 'move' (default: 'copy')
            - pattern: Filename pattern with placeholders
            - metadata: Additional metadata for pattern replacement
            - timestamp_format: Format for timestamp placeholders (default: '%Y%m%d_%H%M%S')
            
    Returns:
        True if renaming was successful, False otherwise
    """
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return False
    
    # Set default parameters
    if params is None:
        params = {}
        
    mode = params.get('mode', 'copy')
    pattern = params.get('pattern', '')
    metadata = params.get('metadata', {})
    timestamp_format = params.get('timestamp_format', '%Y%m%d_%H%M%S')
    
    try:
        # If a pattern is specified, process it to create the final output path
        if pattern:
            # Get output directory
            output_dir = os.path.dirname(output_path)
            
            # Process the pattern to get the new filename
            new_filename = process_pattern(
                pattern=pattern,
                input_path=input_path,
                metadata=metadata,
                timestamp_format=timestamp_format
            )
            
            # Set the final output path
            final_output_path = os.path.join(output_dir, new_filename)
        else:
            # Use the provided output path directly
            final_output_path = output_path
        
        # Create target directory if it doesn't exist
        target_dir = os.path.dirname(final_output_path)
        os.makedirs(target_dir, exist_ok=True)
        
        # Perform the operation (copy or move)
        if mode == 'copy':
            logger.info(f"Copying {input_path} to {final_output_path}")
            shutil.copy2(input_path, final_output_path)
        else:  # mode == 'move'
            logger.info(f"Moving {input_path} to {final_output_path}")
            shutil.move(input_path, final_output_path)
            
        # Verify the operation succeeded
        if not os.path.exists(final_output_path):
            logger.error("File operation failed: output file was not created")
            return False
            
        logger.info(f"Successfully {'copied' if mode == 'copy' else 'moved'} to {final_output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error during file operation: {str(e)}")
        return False

def process_pattern(pattern: str, input_path: str, metadata: Dict[str, Any], 
                   timestamp_format: str) -> str:
    """
    Process a filename pattern, replacing placeholders
    
    Args:
        pattern: Filename pattern with placeholders
        input_path: Path to the input file
        metadata: Additional metadata for pattern replacement
        timestamp_format: Format for timestamp placeholders
        
    Returns:
        Processed filename
    """
    # Get input file details
    input_filename = os.path.basename(input_path)
    input_basename, input_extension = os.path.splitext(input_filename)
    
    # Get current timestamp
    now = datetime.datetime.now()
    timestamp = now.strftime(timestamp_format)
    
    # Generate UUID
    unique_id = str(uuid.uuid4())
    short_id = unique_id.split('-')[0]
    
    # Define replacements
    replacements = {
        '{filename}': input_filename,
        '{basename}': input_basename,
        '{ext}': input_extension,
        '{timestamp}': timestamp,
        '{date}': now.strftime('%Y%m%d'),
        '{time}': now.strftime('%H%M%S'),
        '{uuid}': unique_id,
        '{uuid_short}': short_id
    }
    
    # Add metadata to replacements
    for key, value in metadata.items():
        replacements[f'{{meta.{key}}}'] = str(value)
    
    # Replace all placeholders in the pattern
    result = pattern
    for placeholder, replacement in replacements.items():
        result = result.replace(placeholder, replacement)
    
    # If the pattern doesn't include the extension and the original file had one,
    # add it to the result (unless the pattern explicitly includes a new extension)
    if not result.endswith(input_extension) and '.' not in os.path.basename(result) and input_extension:
        result += input_extension
    
    return result

def batch_rename(file_paths: list, output_dir: str, pattern: str, params: Dict[str, Any] = None) -> Dict[str, bool]:
    """
    Rename multiple files using a pattern
    
    Args:
        file_paths: List of file paths to rename
        output_dir: Directory to save renamed files
        pattern: Filename pattern with placeholders
        params: Additional parameters for rename_file
        
    Returns:
        Dictionary mapping input paths to success/failure status
    """
    if params is None:
        params = {}
    
    # Add pattern to params
    params['pattern'] = pattern
    
    results = {}
    for input_path in file_paths:
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            results[input_path] = False
            continue
        
        # Create a temporary output path (will be replaced by pattern)
        filename = os.path.basename(input_path)
        output_path = os.path.join(output_dir, filename)
        
        # Rename the file
        success = rename_file(input_path, output_path, params)
        results[input_path] = success
    
    return results 