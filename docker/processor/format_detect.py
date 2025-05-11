#!/usr/bin/env python3
"""
File Format Detection

This module:
1. Detects file formats (ROS, MCAP, HDF5, etc.)
2. Returns format information for further processing
"""

import os
import logging
import subprocess
import mimetypes
from typing import Dict, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger("format_detect")

def detect_format(file_path: str) -> Dict[str, Any]:
    """
    Detect the format of a file
    
    Args:
        file_path: Path to the file
    
    Returns:
        Dictionary with format information:
        {
            'type': 'video'|'image'|'rosbag'|'mcap'|'hdf5'|'archive'|'unknown',
            'extension': file extension,
            'mime_type': MIME type if detectable,
            'details': format-specific details
        }
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return {
            'type': 'unknown',
            'extension': '',
            'mime_type': '',
            'details': {'error': 'File not found'}
        }
    
    # Get file extension and initial MIME type
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()
    mime_type, _ = mimetypes.guess_type(file_path)
    
    # Detect special formats: ROS bag, MCAP, HDF5
    if is_rosbag(file_path):
        return {
            'type': 'rosbag',
            'extension': extension,
            'mime_type': 'application/octet-stream',
            'details': detect_rosbag_details(file_path)
        }
    
    if is_mcap(file_path):
        return {
            'type': 'mcap',
            'extension': extension,
            'mime_type': 'application/octet-stream',
            'details': detect_mcap_details(file_path)
        }
    
    if is_hdf5(file_path):
        return {
            'type': 'hdf5',
            'extension': extension,
            'mime_type': 'application/x-hdf5',
            'details': detect_hdf5_details(file_path)
        }
    
    # Detect common media formats
    if is_video(file_path):
        return {
            'type': 'video',
            'extension': extension,
            'mime_type': mime_type or 'video/unknown',
            'details': detect_video_details(file_path)
        }
    
    if is_image(file_path):
        return {
            'type': 'image',
            'extension': extension,
            'mime_type': mime_type or 'image/unknown',
            'details': {}
        }
    
    if is_archive(file_path):
        return {
            'type': 'archive',
            'extension': extension,
            'mime_type': mime_type or 'application/zip',
            'details': {}
        }
    
    # Default case - unknown format
    return {
        'type': 'unknown',
        'extension': extension,
        'mime_type': mime_type or 'application/octet-stream',
        'details': {}
    }

def is_rosbag(file_path: str) -> bool:
    """Check if file is a ROS bag"""
    if file_path.endswith('.bag'):
        try:
            # Try to import rosbags to verify it's available
            from rosbags.rosbag1 import Reader
            # Actually testing the file opening would be better
            # but for quick check just verify the extension
            return True
        except ImportError:
            logger.warning("rosbags package not installed, can't verify ROS bag")
    return False

def is_mcap(file_path: str) -> bool:
    """Check if file is an MCAP file"""
    if file_path.endswith('.mcap'):
        try:
            import mcap
            logger.info(f"MCAP package is installed and file ends with .mcap: {file_path}")
            return True
        except ImportError:
            logger.warning("mcap package not installed, can't verify MCAP file")
    else:
        logger.info(f"File does not end with .mcap: {file_path}")
    return False

def is_hdf5(file_path: str) -> bool:
    """Check if file is an HDF5 file"""
    if file_path.endswith('.h5') or file_path.endswith('.hdf5'):
        try:
            # Try to import h5py to verify it's available
            import h5py
            # For more thorough checking, we could open the file
            try:
                with h5py.File(file_path, 'r') as _:
                    return True
            except:
                return False
        except ImportError:
            logger.warning("h5py package not installed, can't verify HDF5 file")
            # Just check extension if h5py isn't available
            return True
    return False

def is_video(file_path: str) -> bool:
    """Check if file is a video"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    _, ext = os.path.splitext(file_path)
    if ext.lower() in video_extensions:
        return True
    
    # Try using ffprobe if available
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0', 
             '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', 
             file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return 'video' in result.stdout
    except:
        # If ffprobe fails, rely on extension check
        return False

def is_image(file_path: str) -> bool:
    """Check if file is an image"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    _, ext = os.path.splitext(file_path)
    return ext.lower() in image_extensions

def is_archive(file_path: str) -> bool:
    """Check if file is an archive"""
    archive_extensions = ['.zip', '.tar', '.gz', '.bz2', '.7z', '.rar']
    _, ext = os.path.splitext(file_path)
    return ext.lower() in archive_extensions

def detect_video_details(file_path: str) -> Dict[str, Any]:
    """Get details about a video file using ffprobe"""
    details = {}
    
    try:
        # Get video information
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height,codec_name,duration,bit_rate,avg_frame_rate',
             '-of', 'json', file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            import json
            video_info = json.loads(result.stdout)
            if 'streams' in video_info and video_info['streams']:
                stream = video_info['streams'][0]
                details.update({
                    'width': int(stream.get('width', 0)),
                    'height': int(stream.get('height', 0)),
                    'codec': stream.get('codec_name', 'unknown'),
                    'duration': float(stream.get('duration', 0)),
                    'bitrate': int(stream.get('bit_rate', 0)),
                    'framerate': stream.get('avg_frame_rate', 'unknown')
                })
    except Exception as e:
        logger.error(f"Error detecting video details: {str(e)}")
    
    return details

def detect_rosbag_details(file_path: str) -> Dict[str, Any]:
    """Get details about a ROS bag file"""
    details = {}
    
    try:
        from rosbags.rosbag1 import Reader
        
        with Reader(file_path) as reader:
            topics = reader.topics
            message_count = sum(c.count for c in reader.connections)
            duration = reader.duration
            
            details.update({
                'topics': list(topics.keys()),
                'message_count': message_count,
                'duration': duration.total_seconds()
            })
    except Exception as e:
        logger.error(f"Error reading ROS bag details: {str(e)}")
    
    return details

def detect_mcap_details(file_path: str) -> Dict[str, Any]:
    """Get details about an MCAP file"""
    details = {}
    try:
        from mcap.reader import make_reader
        with open(file_path, 'rb') as f:
            reader = make_reader(f)
            schema_count = len(getattr(reader, 'schemas', {}))
            channel_count = len(getattr(reader, 'channels', {}))
            channels = [c.topic for c in getattr(reader, 'channels', {}).values()]
            details.update({
                'schema_count': schema_count,
                'channel_count': channel_count,
                'channels': channels
            })
    except Exception as e:
        logger.error(f"Error reading MCAP details: {str(e)}")
    return details

def detect_hdf5_details(file_path: str) -> Dict[str, Any]:
    """Get details about an HDF5 file"""
    details = {}
    
    try:
        import h5py
        
        with h5py.File(file_path, 'r') as f:
            # Get root groups
            root_items = list(f.keys())
            
            details.update({
                'root_groups': root_items,
                'attrs': {key: str(value) for key, value in f.attrs.items()}
            })
    except Exception as e:
        logger.error(f"Error reading HDF5 details: {str(e)}")
    
    return details 