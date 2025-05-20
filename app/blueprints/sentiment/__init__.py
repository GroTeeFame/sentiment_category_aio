from flask import Blueprint
import os
from flask_dropzone import Dropzone
import logging

from app.config import Config


sentiment_blueprint = Blueprint('sentiment', __name__)

from . import routes


def init_sentiment(app, basedir):

    app.config.update(
        UPLOADED_PATH=os.path.join(basedir, Config.UPLOAD_FOLDER),
        # Flask-Dropzone config:
        DROPZONE_ALLOWED_FILE_CUSTOM= True,
        DROPZONE_ALLOWED_FILE_TYPE='.xlsx',
        DROPZONE_MAX_FILE_SIZE=5,
        DROPZONE_MAX_FILES=1,
        DROPZONE_UPLOAD_ON_CLICK=True,
    )

    app.logger.info(f" routes.py /app/blueprints/sentiment ")

    app.register_blueprint(sentiment_blueprint)
