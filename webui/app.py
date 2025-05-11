from flask import Flask, render_template, request, has_request_context
import os
import logging
import yaml
import logging.handlers
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
print("Environment variables loaded from .env file")

# Import route modules
from api.validate_path import validate_path_blueprint
from api.upload_local import upload_local_blueprint
from api.submit_task import submit_tasks_blueprint
from api.task_status import task_status_blueprint
from api.debug import debug_blueprint

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Load configuration
config_path = os.environ.get('CONFIG_PATH', '../config/app_config.yaml')

try:
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
        app.config['APP_CONFIG'] = config
    print(f"Configuration loaded from {config_path}")
except Exception as e:
    print(f"Error loading configuration: {e}")
    config = {}
    app.config['APP_CONFIG'] = config

# Configure logging
log_config = config.get('logging', {})
log_level_name = log_config.get('level', 'INFO')
log_level = getattr(logging, log_level_name)

# Setup logging format
log_format = log_config.get('format', '[%(asctime)s] [%(levelname)s] [%(name)s] [%(request_id)s] %(message)s')
date_format = log_config.get('date_format', '%Y-%m-%d %H:%M:%S.%03d')
file_size_limit = log_config.get('file_size_limit', 10485760)  # Default 10MB
backup_count = log_config.get('backup_count', 5)

# Create formatter
formatter = logging.Formatter(log_format, date_format)

# Create request ID filter
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            # Only try to get request.request_id if we're in a request context
            if has_request_context():
                record.request_id = getattr(request, 'request_id', 'N/A')
            else:
                record.request_id = 'N/A'  # Outside of a request context
        return True

# Create logs directory if it doesn't exist
current_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(current_dir, 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Setup process log with absolute path
process_log_path = log_config.get('process_log', 'logs/process.log')
if not os.path.isabs(process_log_path):
    process_log_path = os.path.join(current_dir, process_log_path)

# Make sure the directory exists
process_log_dir = os.path.dirname(process_log_path)
os.makedirs(process_log_dir, exist_ok=True)

process_file_handler = logging.handlers.RotatingFileHandler(
    process_log_path, 
    maxBytes=file_size_limit, 
    backupCount=backup_count
)
process_file_handler.setFormatter(formatter)
process_file_handler.setLevel(log_level)
process_file_handler.addFilter(RequestIdFilter())

# Setup error log with absolute path
error_log_path = log_config.get('error_log', 'logs/error.log')
if not os.path.isabs(error_log_path):
    error_log_path = os.path.join(current_dir, error_log_path)

# Make sure the directory exists
error_log_dir = os.path.dirname(error_log_path)
os.makedirs(error_log_dir, exist_ok=True)

error_file_handler = logging.handlers.RotatingFileHandler(
    error_log_path, 
    maxBytes=file_size_limit, 
    backupCount=backup_count
)
error_file_handler.setFormatter(formatter)
error_file_handler.setLevel(logging.ERROR)
error_file_handler.addFilter(RequestIdFilter())

# Optional console handler
if log_config.get('console_logging', True):
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_level_name = log_config.get('console_level', 'INFO')
    console_level = getattr(logging, console_level_name)
    console_handler.setLevel(console_level)
    console_handler.addFilter(RequestIdFilter())

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(log_level)
root_logger.addHandler(process_file_handler)
root_logger.addHandler(error_file_handler)
if log_config.get('console_logging', True):
    root_logger.addHandler(console_handler)

# Create app logger
logger = logging.getLogger('webui')
logger.info("Logging system initialized")

# Extract configuration variables with fallbacks
AWS_REGION = os.environ.get('AWS_REGION') or config.get('aws', {}).get('region', 'us-west-2')
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL') or config.get('aws', {}).get('sqs', {}).get('queue_url', '')
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID') or config.get('gcp', {}).get('project_id', '')
GCP_PUBSUB_TOPIC = os.environ.get('GCP_PUBSUB_TOPIC') or config.get('gcp', {}).get('pubsub', {}).get('topic_name', '')
GCP_SERVICE_ACCOUNT_KEY = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
AWS_TEMP_BUCKET = os.environ.get('AWS_TEMP_BUCKET') or config.get('aws', {}).get('s3', {}).get('temp_bucket', 'temp-uploads-aws')
GCP_TEMP_BUCKET = os.environ.get('GCP_TEMP_BUCKET') or config.get('gcp', {}).get('gcs', {}).get('temp_bucket', 'temp-uploads-gcp')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE') or config.get('aws', {}).get('dynamodb', {}).get('table_name', 'task_status')
FIRESTORE_COLLECTION = os.environ.get('FIRESTORE_COLLECTION') or config.get('gcp', {}).get('firestore', {}).get('collection_name', 'tasks')

# Make configuration available to blueprints
app.config.update(
    AWS_REGION=AWS_REGION,
    SQS_QUEUE_URL=SQS_QUEUE_URL,
    GCP_PROJECT_ID=GCP_PROJECT_ID,
    GCP_PUBSUB_TOPIC=GCP_PUBSUB_TOPIC,
    GCP_SERVICE_ACCOUNT_KEY=GCP_SERVICE_ACCOUNT_KEY,
    AWS_TEMP_BUCKET=AWS_TEMP_BUCKET,
    GCP_TEMP_BUCKET=GCP_TEMP_BUCKET,
    DYNAMODB_TABLE=DYNAMODB_TABLE,
    FIRESTORE_COLLECTION=FIRESTORE_COLLECTION
)

# Middleware to add request ID to each request
@app.before_request
def add_request_id():
    request.request_id = str(uuid.uuid4())

# Register route blueprints
app.register_blueprint(validate_path_blueprint)
app.register_blueprint(upload_local_blueprint)
app.register_blueprint(submit_tasks_blueprint)
app.register_blueprint(task_status_blueprint)
app.register_blueprint(debug_blueprint)

# Main route
@app.route('/')
def home():
    """Serve the main application page"""
    logger.info(f"Home page requested")
    return render_template('index.html')

# Test page for API connectivity
@app.route('/test')
def test_page():
    """Serve the API test page"""
    logger.info(f"Test page requested")
    return render_template('test.html')

# Diagnostic endpoint
@app.route('/api/diagnostic', methods=['GET', 'POST'])
def diagnostic():
    """Simple diagnostic endpoint to verify API connectivity"""
    logger.info("Diagnostic endpoint called")
    return {
        'status': 'ok',
        'timestamp': str(uuid.uuid4()),
        'method': request.method,
        'aws_region': AWS_REGION,
        'gcp_project': GCP_PROJECT_ID,
        'environment': 'production' if not debug else 'development'
    }

# Health check endpoint
@app.route('/health')
def health():
    logger.debug("Health check called")
    return {
        'status': 'ok',
        'aws': SQS_QUEUE_URL is not None and SQS_QUEUE_URL != '',
        'gcp': GCP_PROJECT_ID is not None and GCP_PROJECT_ID != '' and GCP_PUBSUB_TOPIC is not None and GCP_PUBSUB_TOPIC != ''
    }

if __name__ == '__main__':
    # Get port from environment variable, config, or default to 8080
    port = int(os.environ.get('PORT') or config.get('app', {}).get('web', {}).get('port', 8080))
    debug = os.environ.get('DEBUG', '').lower() == 'true' or config.get('app', {}).get('web', {}).get('debug', False)
    logger.info(f"Starting web server on port {port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug) 