# app/logger_setup.py
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from app.config import Config

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)

# Get the base directory of the application
basedir = os.path.dirname(os.path.dirname(current_file_path))

logs_path = f"{os.path.join(basedir, Config.LOGS_FOLDER)}/app.log"

def setup_logger(name='custom_logger'):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():  # Avoid adding multiple handlers
        handler = TimedRotatingFileHandler(
            logs_path,
            when='midnight',
            interval=1,
            backupCount=14
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger