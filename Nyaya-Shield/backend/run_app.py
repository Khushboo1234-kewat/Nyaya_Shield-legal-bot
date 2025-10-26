import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Log environment information
logger.info("=== Starting Application ===")
logger.info(f"Python executable: {sys.executable}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")

# Log environment variables
logger.info("\n=== Environment Variables ===")
for key in os.environ:
    if 'PYTHON' in key.upper() or 'PATH' in key.upper() or 'FLASK' in key.upper():
        logger.info(f"{key}: {os.environ[key]}")

# Try to import and run the Flask app
try:
    logger.info("\n=== Importing Flask application ===")
    from app import app
    
    # Log Flask configuration
    logger.info("\n=== Flask Configuration ===")
    for key, value in app.config.items():
        logger.info(f"{key}: {value}")
    
    # Run the application
    logger.info("\n=== Starting Flask application ===")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    
except Exception as e:
    logger.error("\n=== ERROR ===")
    logger.error(f"Failed to start application: {str(e)}", exc_info=True)
    raise
