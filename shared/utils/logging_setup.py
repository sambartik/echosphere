import logging

LOG_ENABLED = True


def configure_logging(filepath, log_level="DEBUG"):
    if not LOG_ENABLED:
        return logging.disable(logging.CRITICAL + 1)
    # Configure logging
    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler(filepath)])
