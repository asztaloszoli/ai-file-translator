import os
import logging

# Set up logging
def setup_logging(log_dir: str, timestamp: str):
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"translation_log_{timestamp}.log")
    
    # File handler for detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console handler for relevant info
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return log_file
