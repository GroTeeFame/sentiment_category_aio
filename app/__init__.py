import os
import logging
from logging.handlers import RotatingFileHandler
from logging.handlers import TimedRotatingFileHandler
from flask_socketio import SocketIO, emit

from app.config import Config

from flask import Flask
from app.blueprints.category import init_category
from app.blueprints.sentiment import init_sentiment
from app.blueprints.db_controller import init_db_controller

from flask_session import Session

from flask_dropzone import Dropzone

from .logger_setup import setup_logger

def create_app(basedir):
    # Make sure that all needed folders exists:
    if not os.path.exists(os.path.join(basedir, Config.UPLOAD_FOLDER)):
        os.makedirs(os.path.join(basedir, Config.UPLOAD_FOLDER))
    
    if not os.path.exists(os.path.join(basedir, Config.FLASK_SESSION_FOLDER)):
        os.makedirs(os.path.join(basedir, Config.FLASK_SESSION_FOLDER))

    if not os.path.exists(os.path.join(basedir, Config.LOGS_FOLDER)):
        os.makedirs(os.path.join(basedir, Config.LOGS_FOLDER))

    logs_path = f"{os.path.join(basedir, Config.LOGS_FOLDER)}/app.log"

    app = Flask(__name__)

    # Set up logger
    logger = setup_logger()
    app.logger.handlers = []  # Clear any existing handlers
    app.logger.addHandler(logger.handlers[0])
    app.logger.setLevel(logging.INFO)

    dropzone = Dropzone(app)
    
    app.config['SECRET_KEY'] = 'mysupersecretkey'
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)

    socketio = SocketIO(app, cors_allowed_origins="*")

    app.secret_key = 'mysupersecretkey'

    init_sentiment(app, basedir=basedir)
    init_category(app, basedir=basedir)
    init_db_controller(app, basedir=basedir)

    app.socketio = socketio

    return app
