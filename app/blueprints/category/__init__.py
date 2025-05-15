from flask import Blueprint
import os
import logging
from flask_dropzone import Dropzone
from datetime import datetime, timedelta
from flask_session import Session

# from . import MongoDBHandler


# from app.config import ( UPLOAD_FOLDER )

from app.config import Config

category_blueptint = Blueprint('category', __name__)

from . import routes

logging.info(f" __init__.py /app/blueprints/category ")
print(f" __init__.py /app/blueprints/category ")


def init_category(app, basedir):
    # from . import routes

    app.config.update(
        UPLOADED_PATH=os.path.join(basedir, Config.UPLOAD_FOLDER),
        DROPZONE_ALLOWED_FILE_CUSTOM= True,
        DROPZONE_ALLOWED_FILE_TYPE='.wav',
        DROPZONE_MAX_FILE_SIZE=50,
        DROPZONE_MAX_FILES=50,
        DROPZONE_UPLOAD_ON_CLICK=True,
        SESSION_PERMANENT = True,
        SESSION_TYPE = 'filesystem',
        PERMANENT_SESSION_LIFETIME = timedelta(hours=5)
    )


    # dropzone_category = Dropzone(app)
    # socketio = SocketIO(app, cors_allowed_origins="*")


    app.config['SESSION_TYPE'] = 'filesystem'

    # Optionally set a directory to store session files
    app.config['SESSION_FILE_DIR'] = os.path.join(basedir, 'flask_session')
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    Session(app)


    app.register_blueprint(category_blueptint)