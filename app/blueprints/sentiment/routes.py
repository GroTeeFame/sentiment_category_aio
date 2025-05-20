from . import sentiment_blueprint
import os
import sys
import uuid
from flask import Flask, request, send_file, render_template, session, flash, jsonify, redirect, url_for#, redirect, send_from_directory, url_for
from flask_dropzone import Dropzone
import logging
from flask import current_app

from . import alp as alapi

from app.config import Config

from app.logger_setup import setup_logger

logger = setup_logger(__name__)

logger.info(f" routes.py /app/blueprints/sentiment ")


@sentiment_blueprint.route('/sentiment')
def sentiment_index():
    logger.info(f" routes.py /app/blueprints/sentiment sentiment_index()")
    return render_template('sentiment/sentiment.html', title='Сентимент')


@sentiment_blueprint.route('/analyze-sentiment', methods=['POST'])
async def analyze_sentiment():
    logger.info("'/analyze' route in routes.py sentiment blueprint")

    unique_filename = f"uploaded_file_{uuid.uuid4()}.xlsx"
    filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)

    file = ''

    if request.method == 'POST':
        logger.info("'/analyze' route in routes.py sentiment blueprint - if request.method == 'POST':")
        for key, f in request.files.items():
            if key.startswith('file'):
                logger.info("'/analyze' route in app.py - if key.startswith('file'):")
                file = f
                try:
                    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                    file.save(filepath)
                except Exception as e:
                    return str(e), 500

    messages = []
    try:
        logger.info("'/analyze' trying to make call to API:")
        with open(filepath, 'rb') as f:

            orchestrated_filename = f"DOWNLOADED_FILE_ORCHESTRATED_{uuid.uuid4()}.xlsx"
            orchestrated_filepath = os.path.join(Config.UPLOAD_FOLDER, orchestrated_filename)
            
            try:
                response = await alapi.orchestrate_full_analysis(filepath, orchestrated_filepath)
            except Exception as e:
                logger.error(f"ERROR in backend: {e}")
                messages.append(str(e))
                logger.info(f"messages: {messages}")
                return jsonify({'messages': messages, 'status': 'error'}), 500

        if response["status_code"] == 200: #TODO: тре подумать, якась хуйня нє???

            session['uploaded_filepath'] = filepath
            session['orchestrated_filepath'] = orchestrated_filepath
            session['filename'] = file.filename
        
        else:
            return f"Analysis service returned {response.status_code}", 500
    except Exception as e:
        return str(e), 500

    return render_template('index.html')


@sentiment_blueprint.route('/download-sentiment', methods=['GET'])
def download_sentiment():
    logger.info("/download route in app.py")

    uploaded_filepath = session.get('uploaded_filepath')
    orchestrated_filepath = session.get('orchestrated_filepath')
    filename = session.get('filename')
    logger.info(f"filename in '/download': {filename}")
    logger.info(f"orchestrated_filepath in '/download': {orchestrated_filepath}")
    
    # file_to_send = os.path.join('/home/P-RZuben10302/flask/test/sentiment_category_aio', orchestrated_filepath)
    
    # Get the absolute path of the current file
    current_file_path = os.path.abspath(__file__)
    logger.info(f"!!!   ----- current_file_path: {current_file_path}")

    # Get the base directory of the application
    basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))
    logger.info(f"!!!   ----- basedir: {basedir}")

    
    file_to_send = os.path.join(basedir, orchestrated_filepath)
    
    logger.info(f"!!!   ----- file_to_send: {file_to_send}")

    response = send_file(
        file_to_send,
        # orchestrated_filepath,
        as_attachment=True,
        download_name=f"AI_{filename}",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    logger.info('------deleting orchestrated_filepath------')
    os.remove(orchestrated_filepath)
    logger.info('------deleting uploaded_filepath------')
    os.remove(uploaded_filepath)
    return response
