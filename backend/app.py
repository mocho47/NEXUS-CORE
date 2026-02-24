import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load configuration from environment variables
app.config['ENV'] = os.getenv('ENV', 'development')
app.config['DEBUG'] = os.getenv('DEBUG', 'False') == 'True'

@app.route('/', methods=['GET'])
def home():
    """Home route"""
    logger.info("Home route accessed")
    return jsonify(message="Welcome to the NEXUS-CORE API!")

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all exceptions"""
    logger.error(f"An error occurred: {str(e)}")
    response = jsonify(message=str(e))
    response.status_code = 500
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
