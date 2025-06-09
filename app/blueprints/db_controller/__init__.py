from flask import Blueprint
import os

from app.config import Config

db_controller_blueprint = Blueprint('db_controller', __name__)

from . import routes

from app.logger_setup import setup_logger

def init_db_controller(app, basedir):

    logger = setup_logger(__name__)

    logger.info(" init_db_controller")


    app.register_blueprint(db_controller_blueprint)