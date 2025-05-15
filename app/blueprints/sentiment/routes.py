from . import sentiment_blueprint
import os
import sys
import uuid
from flask import Flask, request, send_file, render_template, session, flash, jsonify, redirect, url_for#, redirect, send_from_directory, url_for
from flask_dropzone import Dropzone
import logging

# import alp as alapi
from . import alp as alapi

from app.config import Config



print(f" routes.py /app/blueprints/sentiment ")


@sentiment_blueprint.route('/sentiment')
def sentiment_index():
    print(f" routes.py /app/blueprints/sentiment sentiment_index()")
    logging.info(f" routes.py /app/blueprints/sentiment sentiment_index()")
    return render_template('sentiment/sentiment.html', title='Сентимент')



@sentiment_blueprint.route('/analyze-sentiment', methods=['POST'])
async def analyze_sentiment():
    # print("'/analyze' route in app.py", file=sys.stderr)
    print("'/analyze' route in app.py")
    logging.info("'/analyze' route in routes.py sentiment blueprint", file=sys.stderr)
    # app.logging.info("'/analyze' route in app.py")
    # flash("'/analyze' route in app.py")

    unique_filename = f"uploaded_file_{uuid.uuid4()}.xlsx"
    filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)

    file = ''

    if request.method == 'POST':
        # print("----------------------------------", file=sys.stderr)
        # print("'/analyze' route in app.py - if request.method == 'POST':", file=sys.stderr)
        print("----------------------------------")
        print("'/analyze' route in app.py - if request.method == 'POST':")
        logging.info("'/analyze' route in routes.py sentiment blueprint - if request.method == 'POST':")
        # app.logging.info("'/analyze' route in app.py - if request.method == 'POST':")
        for key, f in request.files.items():
            if key.startswith('file'):
                # print("'/analyze' route in app.py - if key.startswith('file'):", file=sys.stderr)
                print("'/analyze' route in app.py - if key.startswith('file'):")
                logging.info("'/analyze' route in app.py - if key.startswith('file'):")
                # app.logging.info("'/analyze' route in app.py - if key.startswith('file'):")
                file = f
                try:
                    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                    file.save(filepath)
                except Exception as e:
                    return str(e), 500

    messages = []
    try:
        # print("'/analyze' trying to make call to API:", file=sys.stderr)
        print("'/analyze' trying to make call to API:")
        logging.info("'/analyze' trying to make call to API:")
        # app.logging.info("'/analyze' trying to make call to API:")
        with open(filepath, 'rb') as f:
            # response = requests.post("http://127.0.0.1:8000/orchestrate_full_analysis", files={"file": f})

            orchestrated_filename = f"DOWNLOADED_FILE_ORCHESTRATED_{uuid.uuid4()}.xlsx"
            orchestrated_filepath = os.path.join(Config.UPLOAD_FOLDER, orchestrated_filename)
            
            try:
                response = await alapi.orchestrate_full_analysis(filepath, orchestrated_filepath)
            except Exception as e:
                # flash(str(e), 'error')
                # print(f"ERROR in backend: {e}", file=sys.stderr)
                print(f"ERROR in backend: {e}")
                logging.info(f"ERROR in backend: {e}")
                # app.logging.info(f"ERROR in backend: {e}")
                messages.append(str(e))
                print(f"messages: {messages}")
                logging.info(f"messages: {messages}")
                # app.logging.info(f"messages: {messages}")
                return jsonify({'messages': messages, 'status': 'error'}), 500

        # if response.status_code == 200:
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
    # print("/download route in app.py", file=sys.stderr)
    print("/download route in app.py")
    logging.info("/download route in app.py")
    # app.logging.info("/download route in app.py")

    uploaded_filepath = session.get('uploaded_filepath')
    orchestrated_filepath = session.get('orchestrated_filepath')
    filename = session.get('filename')
    # print(f"filename in '/download': {filename}", file=sys.stderr)
    print(f"filename in '/download': {filename}")
    logging.info(f"filename in '/download': {filename}")
    # app.logging.info(f"filename in '/download': {filename}")
    # print(f"orchestrated_filepath in '/download': {orchestrated_filepath}", file=sys.stderr)
    print(f"orchestrated_filepath in '/download': {orchestrated_filepath}")
    logging.info(f"orchestrated_filepath in '/download': {orchestrated_filepath}")
    # app.logging.info(f"orchestrated_filepath in '/download': {orchestrated_filepath}")

    # file_to_send = orchestrated_filepath

    # file_to_send = os.path.join('/Users/rostislavzubenko/Work/CC AI/combine_sent_cat_aio/', orchestrated_filepath)
    
    file_to_send = os.path.join('/home/P-RZuben10302/flask/test/sentiment_category_aio', orchestrated_filepath)
    
    print(f"!!!   ----- file_to_send: {file_to_send}")


    # application_root = os.path.dirname('uploads')
    # uploads_dir = os.path.join(application_root, 'uploads')

    # print(f"application_root: {application_root}")
    # print(f"uploads_dir: {uploads_dir}")
    # print(f"orchestrated_filepath: {orchestrated_filepath}")
    # print(f"basedir: {basedir}")

    response = send_file(
        file_to_send,
        # orchestrated_filepath,
        as_attachment=True,
        download_name=f"AI_{filename}",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    logging.info('------deleting orchestrated_filepath------')
    print('------deleting orchestrated_filepath------')
    # app.logging.info('------deleting orchestrated_filepath------')
    os.remove(orchestrated_filepath)
    logging.info('------deleting uploaded_filepath------')
    # app.logging.info('------deleting uploaded_filepath------')
    os.remove(uploaded_filepath)
    return response
