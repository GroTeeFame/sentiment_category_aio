import logging
from flask_socketio import SocketIO, emit

from flask import Flask
from app.blueprints.category import category_blueptint
from app.blueprints.sentiment import sentiment_blueprint
from app.blueprints.category import init_category
from app.blueprints.sentiment import init_sentiment

from flask_dropzone import Dropzone


def create_app(basedir):
    print(f" __init__.py create_app() ")
    logging.info(f" __init__.py create_app() ")

    # socketio = SocketIO()

    # basedir = os.path.abspath(os.path.dirname(__file__))


    app = Flask(__name__)
    # app.config.from_pyfile('config.py')

    dropzone = Dropzone(app)
    
    socketio = SocketIO(app, cors_allowed_origins="*")
    # socketio.init_app(app, cors_allowed_origins="*")
    
    # UPLOAD_FOLDER = 'uploads' 


    app.secret_key = 'mysupersecretkey'

    # app.register_blueprint(category_blueptint, url_prefix='/category')
    # app.register_blueprint(category_blueptint)
    # app.register_blueprint(sentiment_blueprint, url_prefix='/sentiment')
    # app.register_blueprint(sentiment_blueprint)
    init_sentiment(app, basedir=basedir)
    init_category(app, basedir=basedir)

    app.socketio = socketio
    

    return app