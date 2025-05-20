from flask import Blueprint
import os
from flask_dropzone import Dropzone
from datetime import datetime, timedelta
from flask_session import Session

from app.config import Config

category_blueprint = Blueprint('category', __name__)

from . import routes

from app.logger_setup import setup_logger

def init_category(app, basedir):

    logger = setup_logger(__name__)

    logger.info(" init_category in category/__init__.py")

    app.config.update(
        UPLOADED_PATH=os.path.join(basedir, Config.UPLOAD_FOLDER),
        DROPZONE_ALLOWED_FILE_CUSTOM= True,
        DROPZONE_ALLOWED_FILE_TYPE='.wav',
        DROPZONE_MAX_FILE_SIZE=50,
        DROPZONE_MAX_FILES=50,
        DROPZONE_UPLOAD_ON_CLICK=True,
        SESSION_PERMANENT = True,
        PERMANENT_SESSION_LIFETIME = timedelta(hours=5)
    )


    # Optionally set a directory to store session files
    app.config['SESSION_FILE_DIR'] = os.path.join(basedir, 'flask_session')
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

    app.register_blueprint(category_blueprint)