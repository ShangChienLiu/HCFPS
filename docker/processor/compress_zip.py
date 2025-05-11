#!/usr/bin/env python3
"""
File and Directory Compression

This module:
1. Compresses files and directories into zip archives
2. Supports various compression levels and methods
3. Handles password protection and file filtering
"""

import os
import logging
import zipfile
import shutil
import tempfile
import gzip
from typing import Dict, Any, List, Optional, Union
from .format_detect import detect_format

# Configure logging
logger = logging.getLogger("compress_zip")

def compress_file(input_path: str, output_path: str, params: Dict[str, Any] = None) -> bool:
    """
    Compress a file or directory. Use gzip for .bag files, zip otherwise.
    
    Args:
        input_path: Path to the input file or directory
        output_path: Path to save the output zip file
        params: Optional parameters:
            - compression_level: 0-9 (default 6, 0=no compression, 9=max compression)
            - include_patterns: List of glob patterns to include (default: all files)
            - exclude_patterns: List of glob patterns to exclude (default: none)
            - password: Password to encrypt the zip (default: none)
            - store_paths: Whether to store full paths in the zip (default: False)
            
    Returns:
        True if compression was successful, False otherwise
    """
    if not os.path.exists(input_path):
        logger.error(f"Input path not found: {input_path}")
        return False
    
    # Set default parameters
    if params is None:
        params = {}
        
    compression_level = params.get('compression_level', 6)
    include_patterns = params.get('include_patterns', ['*'])
    exclude_patterns = params.get('exclude_patterns', [])
    password = params.get('password', None)
    store_paths = params.get('store_paths', False)
    
    # Map compression level to zipfile compression constant
    if compression_level == 0:
        compression = zipfile.ZIP_STORED
    else:
        compression = zipfile.ZIP_DEFLATED
        
    try:
        # Create a temporary dir for any intermediate processing
        temp_dir = None
        
        # Resolve input path - could be a file or directory
        if os.path.isdir(input_path):
            source_path = input_path
            is_dir = True
        else:
            source_path = input_path
            is_dir = False
        
        # Create zip file
        logger.info(f"Compressing {source_path} to {output_path}")
        
        file_format = detect_format(input_path)
        ext = file_format.get('extension', '').lower()
        if ext == '.bag':
            # Use gzip for .bag files
            with open(input_path, 'rb') as f_in, gzip.open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            return True
        else:
            with zipfile.ZipFile(output_path, 'w', compression=compression, 
                               compresslevel=compression_level) as zipf:
                
                # Set password if provided
                if password:
                    zipf.setpassword(password.encode('utf-8'))
                
                # Process a directory
                if is_dir:
                    # Import glob for pattern matching
                    import glob
                    
                    # Process include patterns
                    files_to_include = []
                    for pattern in include_patterns:
                        pattern_path = os.path.join(source_path, pattern)
                        matching_files = glob.glob(pattern_path, recursive=True)
                        files_to_include.extend(matching_files)
                    
                    # Filter out excluded patterns
                    for pattern in exclude_patterns:
                        pattern_path = os.path.join(source_path, pattern)
                        excluded_files = glob.glob(pattern_path, recursive=True)
                        files_to_include = [f for f in files_to_include if f not in excluded_files]
                    
                    # Add files to the zip
                    for file_path in files_to_include:
                        if os.path.isfile(file_path):
                            # Determine arcname (path within the zip)
                            if store_paths:
                                arcname = file_path
                            else:
                                arcname = os.path.relpath(file_path, source_path)
                                
                            zipf.write(file_path, arcname=arcname)
                            logger.debug(f"Added {file_path} as {arcname}")
                
                # Process a single file
                else:
                    filename = os.path.basename(source_path)
                    zipf.write(source_path, arcname=filename)
                    logger.debug(f"Added {source_path} as {filename}")
            
        # Verify the zip file was created successfully
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error("Compression failed: output file is empty or not created")
            return False
            
        logger.info(f"Successfully compressed to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error during compression: {str(e)}")
        return False
        
    finally:
        # Clean up temporary directory if created
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def extract_zip(zip_path: str, output_dir: str, password: Optional[str] = None) -> bool:
    """
    Extract a zip archive to a directory
    
    Args:
        zip_path: Path to the zip file
        output_dir: Directory to extract files to
        password: Password for encrypted zips
        
    Returns:
        True if extraction was successful, False otherwise
    """
    if not os.path.exists(zip_path):
        logger.error(f"Zip file not found: {zip_path}")
        return False
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract the zip
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # Set password if provided
            if password:
                zipf.setpassword(password.encode('utf-8'))
                
            # Extract all files
            zipf.extractall(output_dir)
            
        logger.info(f"Successfully extracted {zip_path} to {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error extracting zip: {str(e)}")
        return False

def list_zip_contents(zip_path: str, password: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List the contents of a zip file
    
    Args:
        zip_path: Path to the zip file
        password: Password for encrypted zips
        
    Returns:
        List of dictionaries with file information
    """
    if not os.path.exists(zip_path):
        logger.error(f"Zip file not found: {zip_path}")
        return []
    
    try:
        contents = []
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # Set password if provided
            if password:
                zipf.setpassword(password.encode('utf-8'))
                
            # Get info for all files
            for info in zipf.infolist():
                contents.append({
                    'filename': info.filename,
                    'size': info.file_size,
                    'compressed_size': info.compress_size,
                    'date_time': f"{info.date_time[0]}-{info.date_time[1]}-{info.date_time[2]} "
                                f"{info.date_time[3]}:{info.date_time[4]}:{info.date_time[5]}",
                    'is_dir': info.is_dir()
                })
                
        return contents
        
    except Exception as e:
        logger.error(f"Error listing zip contents: {str(e)}")
        return [] 