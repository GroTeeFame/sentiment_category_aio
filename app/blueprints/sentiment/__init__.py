from flask import Blueprint
import os
from flask_dropzone import Dropzone

# from config import ( UPLOAD_FOLDER )

from app.config import Config


sentiment_blueprint = Blueprint('sentiment', __name__)

from . import routes

# print(f" __init__.py /app/blueprints/sentiment ")


def init_sentiment(app, basedir):
    # UPLOAD_FOLDER = 'uploads' 

    # basedir = os.path.abspath(os.path.dirname(__file__))

    app.config.update(
        UPLOADED_PATH=os.path.join(basedir, Config.UPLOAD_FOLDER),
        # Flask-Dropzone config:
        DROPZONE_ALLOWED_FILE_CUSTOM= True,
        DROPZONE_ALLOWED_FILE_TYPE='.xlsx',
        DROPZONE_MAX_FILE_SIZE=5,
        DROPZONE_MAX_FILES=1,
        DROPZONE_UPLOAD_ON_CLICK=True,
    )

    # print(f" routes.py /app/blueprints/category ")

    # dropzone_sentiment = Dropzone(app)

    app.register_blueprint(sentiment_blueprint)
