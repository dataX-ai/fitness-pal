import logging

def get_logger(name=None):
    """
    Get a configured logger instance.
    If name is not provided, returns a logger with the module name.
    """
    logger = logging.getLogger(name if name else __name__)
    
    # Only add handler if logger doesn't have any handlers
    if not logger.handlers:
        # Configure logging format
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Set log level
        logger.setLevel(logging.INFO)
        
        # Add handler
        logger.addHandler(handler)
        
        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False
    
    return logger