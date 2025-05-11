from flask import Blueprint, request, jsonify
import platform
import os
import sys
import json
import logging

# Setup logger
logger = logging.getLogger('debug')

# Create blueprint
debug_blueprint = Blueprint('debug', __name__)

@debug_blueprint.route('/api/debug', methods=['GET', 'POST', 'OPTIONS'])
def debug_endpoint():
    """Debug endpoint for troubleshooting API connectivity issues"""
    
    # Log the request details
    logger.info(f"Debug endpoint called - method: {request.method}")
    
    # Build response with detailed information
    response_data = {
        'success': True,
        'request': {
            'method': request.method,
            'path': request.path,
            'url': request.url,
            'headers': dict(request.headers),
            'remote_addr': request.remote_addr,
            'content_type': request.content_type,
            'content_length': request.content_length,
        },
        'environment': {
            'platform': platform.platform(),
            'python_version': sys.version,
            'hostname': platform.node(),
            'server_path': os.path.abspath('.'),
        }
    }
    
    # Try to get request data if it's a POST
    if request.method == 'POST':
        try:
            if request.is_json:
                body_data = request.get_json()
                response_data['request']['json_data'] = body_data
                logger.info(f"Received JSON data: {json.dumps(body_data)}")
            else:
                form_data = request.form.to_dict() if request.form else {}
                response_data['request']['form_data'] = form_data
                logger.info(f"Received form data: {json.dumps(form_data)}")
        except Exception as e:
            response_data['request']['data_error'] = str(e)
            logger.error(f"Error parsing request data: {e}")
    
    # Add CORS headers to support cross-origin requests
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    
    # Log the completed request
    logger.info(f"Debug endpoint completed - method: {request.method}")
    
    return response 