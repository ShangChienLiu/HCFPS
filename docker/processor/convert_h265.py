#!/usr/bin/env python3
"""
Video Conversion to H.265

This module:
1. Converts videos to H.265 format
2. Extracts and converts videos from ROS and MCAP files
3. Optimizes for size and quality
"""

import os
import logging
import subprocess
import tempfile
import shutil
import time
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger("convert_h265")

def convert_h265(input_file: str, output_file: str, file_format: Dict[str, Any], 
                params: Dict[str, Any] = None) -> bool:
    """
    Convert a video file to H.265 format
    
    Args:
        input_file: Path to input file
        output_file: Path to save converted video
        file_format: Format information from format_detect
        params: Optional parameters for conversion:
            - crf: Constant Rate Factor (0-51, default 28)
            - preset: Encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
            - resolution: Output resolution (e.g., "1920x1080")
            - fps: Output framerate (e.g., 30)
            
    Returns:
        True if conversion was successful, False otherwise
    """
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return False
    
    # Set default parameters
    if params is None:
        params = {}
        
    crf = params.get('crf', 28)
    preset = params.get('preset', 'medium')
    resolution = params.get('resolution', None)
    fps = params.get('fps', None)
    
    try:
        # Handle different input formats
        file_type = file_format.get('type', 'unknown')
        
        if file_type == 'video':
            # Direct video conversion
            return convert_video_file(input_file, output_file, crf, preset, resolution, fps)
            
        elif file_type == 'rosbag':
            # Extract and convert from ROS bag
            return convert_from_rosbag(input_file, output_file, crf, preset, resolution, fps)
            
        elif file_type == 'mcap':
            # Extract and convert from MCAP
            return convert_from_mcap(input_file, output_file, crf, preset, resolution, fps)
            
        else:
            logger.error(f"Unsupported input format for conversion: {file_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}")
        return False

def convert_video_file(input_file: str, output_file: str, crf: int = 28, preset: str = 'medium',
                      resolution: Optional[str] = None, fps: Optional[int] = None) -> bool:
    """Convert a standard video file to H.265"""
    try:
        # Build ffmpeg command
        command = ['ffmpeg', '-i', input_file, '-c:v', 'libx265', '-crf', str(crf), '-preset', preset]
        
        # Add resolution if specified
        if resolution:
            command.extend(['-vf', f'scale={resolution}'])
        
        # Add framerate if specified
        if fps:
            command.extend(['-r', str(fps)])
        
        # Add audio codec and output file
        command.extend(['-c:a', 'aac', '-strict', 'experimental', output_file])
        
        # Run ffmpeg
        logger.info(f"Running conversion: {' '.join(command)}")
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            logger.error(f"ffmpeg error: {process.stderr}")
            return False
            
        logger.info(f"Conversion successful: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error converting video: {str(e)}")
        return False

def convert_from_rosbag(input_file: str, output_file: str, crf: int = 28, preset: str = 'medium',
                       resolution: Optional[str] = None, fps: Optional[int] = None) -> bool:
    """Extract video from ROS bag and convert to H.265"""
    try:
        # Import ROS bag libraries
        from rosbags.rosbag1 import Reader
        import numpy as np
        import cv2
        
        # Create temporary directory for extracted frames
        temp_dir = tempfile.mkdtemp()
        temp_video = os.path.join(temp_dir, 'extracted.mp4')
        frames_dir = os.path.join(temp_dir, 'frames')
        os.makedirs(frames_dir, exist_ok=True)
        
        # Find image topics in the bag
        logger.info(f"Reading ROS bag: {input_file}")
        image_topics = []
        
        with Reader(input_file) as reader:
            # Find image topics
            for conn in reader.connections:
                if conn.msgtype in ['sensor_msgs/Image', 'sensor_msgs/CompressedImage']:
                    image_topics.append(conn.topic)
            
            if not image_topics:
                logger.error("No image topics found in ROS bag")
                return False
                
            # Use the first image topic
            target_topic = image_topics[0]
            logger.info(f"Extracting images from topic: {target_topic}")
            
            # Extract frames
            frame_count = 0
            for conn, timestamp, data in reader.messages():
                if conn.topic == target_topic:
                    # Convert message to OpenCV image
                    if conn.msgtype == 'sensor_msgs/CompressedImage':
                        # Compressed image
                        import io
                        from PIL import Image
                        img_data = np.asarray(bytearray(data), dtype=np.uint8)
                        img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
                    else:
                        # Raw image
                        # This is a simplified version, in reality we'd need proper message deserialization
                        shape = (data.height, data.width, 3)  # Assuming 3 channels
                        img = np.ndarray(shape=shape, dtype=np.uint8, buffer=data.data)
                    
                    # Save frame
                    frame_path = os.path.join(frames_dir, f"frame_{frame_count:06d}.png")
                    cv2.imwrite(frame_path, img)
                    frame_count += 1
            
            logger.info(f"Extracted {frame_count} frames")
            
            if frame_count == 0:
                logger.error("No frames extracted from ROS bag")
                return False
        
        # Convert frames to video
        frame_pattern = os.path.join(frames_dir, "frame_%06d.png")
        frames_to_video(frame_pattern, temp_video, fps or 30)
        
        # Convert the extracted video to H.265
        result = convert_video_file(temp_video, output_file, crf, preset, resolution, fps)
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting video from ROS bag: {str(e)}")
        return False

def convert_from_mcap(input_file: str, output_file: str, crf: int = 28, preset: str = 'medium',
                     resolution: Optional[str] = None, fps: Optional[int] = None) -> bool:
    """Extract video from MCAP file and convert to H.265"""
    try:
        # Import MCAP libraries
        from mcap.reader import make_reader
        import numpy as np
        import cv2
        import json
        import base64
        # Create temporary directory for extracted frames
        temp_dir = tempfile.mkdtemp()
        temp_video = os.path.join(temp_dir, 'extracted.mp4')
        frames_dir = os.path.join(temp_dir, 'frames')
        os.makedirs(frames_dir, exist_ok=True)
        # Open MCAP file and find image channels
        logger.info(f"Reading MCAP file: {input_file}")
        image_channels = []
        with open(input_file, 'rb') as f:
            reader = make_reader(f)
            # Find image channels
            for channel in getattr(reader, 'channels', {}).values():
                schema = getattr(reader, 'schemas', {}).get(channel.schema_id, None)
                if schema and (('image' in schema.name.lower()) or ('camera' in channel.topic.lower())):
                    image_channels.append(channel)
            if not image_channels:
                logger.error("No image channels found in MCAP file")
                return False
            # Use the first image channel
            target_channel = image_channels[0]
            logger.info(f"Extracting images from channel: {target_channel.topic}")
            # Extract frames
            frame_count = 0
            for schema, channel, message in reader.iter_messages():
                if channel.topic == target_channel.topic:
                    # Convert message to OpenCV image
                    try:
                        msg_data = json.loads(message.data.decode('utf-8'))
                        if 'data' in msg_data:
                            img_data = base64.b64decode(msg_data['data'])
                            nparr = np.frombuffer(img_data, np.uint8)
                            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            frame_path = os.path.join(frames_dir, f"frame_{frame_count:06d}.png")
                            cv2.imwrite(frame_path, img)
                            frame_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to decode frame: {e}")
                        pass
            logger.info(f"Extracted {frame_count} frames")
            if frame_count == 0:
                logger.error("No frames extracted from MCAP file")
                return False
        # Convert frames to video
        frame_pattern = os.path.join(frames_dir, "frame_%06d.png")
        frames_to_video(frame_pattern, temp_video, fps or 30)
        # Convert the extracted video to H.265
        result = convert_video_file(temp_video, output_file, crf, preset, resolution, fps)
        # Clean up
        shutil.rmtree(temp_dir)
        return result
    except Exception as e:
        logger.error(f"Error extracting video from MCAP file: {str(e)}")
        return False

def frames_to_video(frame_pattern: str, output_file: str, fps: int = 30) -> bool:
    """Convert a sequence of image frames to a video file"""
    try:
        # Build ffmpeg command
        command = [
            'ffmpeg',
            '-framerate', str(fps),
            '-i', frame_pattern,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            output_file
        ]
        
        # Run ffmpeg
        logger.info(f"Creating video from frames: {' '.join(command)}")
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            logger.error(f"ffmpeg error: {process.stderr}")
            return False
            
        logger.info(f"Video creation successful: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating video from frames: {str(e)}")
        return False 