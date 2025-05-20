from . import category_blueprint
from flask import render_template
from app.config import Config
from flask import current_app

import os
import sys
import uuid
import logging
from flask import Flask, request, Response, copy_current_request_context, send_file, render_template, session, flash, jsonify, redirect, url_for, redirect, send_from_directory, url_for
from flask_dropzone import Dropzone
from flask_socketio import emit
from datetime import datetime, timedelta
from dotenv import load_dotenv


from app.blueprints.category.mongodb_handler import MongoDBHandler
from app.blueprints.category.hasher import hash_file
from app.blueprints.category.atts_ai_functions import (
    compose_file_process,
    compose_document_update,
    get_list_of_categories_from_db,
    get_potential_category_by_dates,
    create_category_collection_in_db,
    classify_categories_with_gpt,
    update_potential_category_by_id,
    create_category_collection_in_db,
    abandon_potential_category_by_id,
)
from app.blueprints.category.toxlsx import (create_document_xlsx)
from app.blueprints.category.colors import Color

from app.logger_setup import setup_logger

logger = setup_logger(__name__)

load_dotenv()

KEY = os.getenv("SS_KEY")
LOCATION = os.getenv("SS_LOCATION")

logger.info(" routes.py /app/blueprints/category ")

# DB 
DB_NAME = Config.DB_NAME
COLLECTION = Config.COLLECTION
CATEGORIES_COLLECTION = Config.CATEGORIES_COLLECTION



#for debuging, set this flag to True to production.
use_hash_flag = True


UPLOAD_FOLDER = 'uploads'
basedir = os.path.abspath(os.path.dirname(__file__))

try:
    dbh = MongoDBHandler(db_name=DB_NAME)

    collection = COLLECTION

    logger.info(f"Connection with DB({DB_NAME}) was successfully established in app.py")

except Exception as e:
    print(f"Error when trying to connect to db...")
    raise e



# @category_blueprint.route('/category')
@category_blueprint.route('/category')
def category_index():
    logger.info(f" routes.py /app/blueprints/category category_index()")
    return render_template('category/category.html', title='Категоризація')


@category_blueprint.route('/analyze', methods=['POST'])
async def analyze():
    logger.info("'/analyze' route in app.py")

    socketio = current_app.socketio

    if request.method == 'POST':
        results = []  # To store the results for each file

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        i = 1

        logger.info("---------------------------------------")
        logger.info(f"FILES COUNTS: {len(request.files)}")
        logger.info("---------------------------------------")

        for key, f in request.files.items():
            logger.info(f"i : {i}")
            logger.info(f"request.files.items() :  {request.files.items()}")
            logger.info(f" f.filename: {f.filename}")

            if key.startswith('file'):
                socketio.emit("client_update", f"Опрацьовується доумент {i} з {len(request.files)}")

                print(f"'/analyze' route in app.py - processing {key}:", file=sys.stderr)
                logging.info(f"'/analyze' route in app.py - processing {key}:", file=sys.stderr)
                unique_filename = f"uploaded_file_{uuid.uuid4()}.wav"
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                og_filename = f.filename

                try:
                    f.save(filepath)
                except Exception as e:
                    return str(e), 500

                try:
                    fileHash = hash_file(filepath)
                except Exception as e:
                    logger.error(f"Error when trying to create hash from file ({filepath})", file=sys.stderr)
                    continue  # Skip to next file

                fileInSystem = dbh.find_document(collection, {"_id": fileHash})
                if use_hash_flag:
                    if fileInSystem is None:
                        logger.info(f"New file in system, start processing file...")
                        result = compose_file_process(dbh, og_filename, filepath, fileHash, collection, CATEGORIES_COLLECTION)
                        logger.info(f"result: {result}")
                    else:
                        result = fileInSystem
                        # TODO: delete time.sleep() its only for testing. <
                        # print("time.sleep(3)")
                        # time.sleep(3)
                        # print("time.sleep(3)")
                        # TODO: delete time.sleep() its only for testing. >

                        logger.info(f"--- Result from DB for file: '{filepath}' with hash (_id in db): '{fileHash}' ---")
                        logger.info(fileInSystem)
                else:
                    result = compose_file_process(dbh, filepath, fileHash, collection, CATEGORIES_COLLECTION)
                    logger.info(f"result: {result}")

                results.append(result)

                try:
                    os.remove(filepath)
                    logger.info(f"{filepath} file was successfully deleted from system.")
                except Exception as e:
                    logger.error(f"ERROR: can't delete {filepath} from system. Details: {e}")

            i += 1

        logger.info("===============================")
        logger.info(f"results: {results}")
        logger.info(f"length of results: {len(results)}")
        logger.info("===============================")

        session['documents'] = results

        return render_template('category/category_result.html', documents=results)


@category_blueprint.route('/newcategory')
def newcategory():
    logger.info("'/newcategory' route in app.py")

    socketio = current_app.socketio

    socketio.emit("newcategory", f"@app.route('/newcategory')")

    categories = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)
    logger.info(f"categories = {categories}")
    session['categories_from_db'] = categories
    return render_template('category/newcategory.html', title="Нові категорії", categories=categories)


@category_blueprint.route('/submit-dates', methods=['POST'])
def submit_dates():
    logger.info("'/submit' route in app.py")

    socketio = current_app.socketio

    socketio.emit("newcategory", f"@app.route('/submit-dates', methods=['POST'])")

    categories_from_db = session.get('categories_from_db')
    logger.info(f"categories_from_db from session : {categories_from_db}")
    if not categories_from_db:
        categories_from_db = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)
        logger.info(f"categories_from_db from DB : {categories_from_db}")

    start_date = datetime.strptime(request.form.get('startDate'), "%d-%m-%Y")
    end_date = datetime.strptime(request.form.get('endDate'), "%d-%m-%Y").replace(hour=23, minute=59, second=59)

    date_obj = {
        "start_date": start_date.strftime("%d.%m.%y"),
        "end_date": end_date.strftime("%d.%m.%y")
    }

    # Perform database operations using the start_date and end_date
    data_with_potencial_new_category = get_potential_category_by_dates(dbh, COLLECTION, start_date, end_date)

    logger.info(f"data_with_potencial_new_category")
    logger.info(data_with_potencial_new_category)
    logger.info("1111111111111111111111111111111")

    if not data_with_potencial_new_category:
        return render_template('category/updated_info.html', combined_data=[], date_obj=date_obj)

    logger.info("---------------------------------")
    logger.info("get_potential_category_by_dates:")
    logger.info(data_with_potencial_new_category)
    logger.info("---------------------------------")

    potencial_new_category = [doc['potential_new_category'] for doc in data_with_potencial_new_category]

    logger.info("---------------------------------")
    logger.info("potencial_new_category:")
    logger.info(f"{potencial_new_category}")
    logger.info("---------------------------------")

    classifyed_potential_categories = classify_categories_with_gpt(potencial_new_category)

    logger.info("---------------------------------")
    logger.info("classify_categories_with_gpt in submit_dates route:")
    logger.info(f"{classifyed_potential_categories}")
    logger.info("---------------------------------")


    logger.info("===PLAY WITH classifyed_potential_categories =============<")
    for key, values in classifyed_potential_categories.items():
        logger.info(f"Key: {key}")
        for value in values:
            logger.info(f"  ╰─Value: {value}")
    for doc in classifyed_potential_categories:
        logger.info(doc)
    logger.info("===PLAY WITH classifyed_potential_categories =============>")

    combined_data = {}

    for key, value_list in classifyed_potential_categories.items():
        # Filter the list to find dictionary entries where `potential_new_category` matches any string in the value list
        matched_dicts = [
            entry for entry in data_with_potencial_new_category if entry['potential_new_category'] in value_list
        ]
        combined_data[key] = matched_dicts

    print("---------------------------------")
    print("combined_data in submit_dates route:")
    print(f"{combined_data}")
    print("---------------------------------")

    session['combined_data'] = combined_data

    # Return only the HTML for the updated information
    return render_template('category/updated_info.html', combined_data=combined_data, date_obj=date_obj)


@category_blueprint.route('/get_category_from_db')
def get_category_from_db():
    categories = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)
    return jsonify(categories)


@category_blueprint.route('/get_category_data')
def get_category_data():
    key = request.args.get('key')

    combined_data = session.get('combined_data')

    data_to_return = combined_data[key]

    logger.info(f"key: {key}")
    logger.info(f"combined_data: {combined_data}")
    logger.info(f"data_to_return: {data_to_return}")


    
    if key in combined_data:
        return jsonify(combined_data[key])
    else:
        return jsonify({'error': 'No data found for this category'}), 404


@category_blueprint.route('/create_new_category')
def create_new_category():
    logger.info("inside create_new_category(): route +++++++++++++++++++++++++++")
    new_category = request.args.get('key')

    logger.info(f"new_category : {new_category}")

    combined_data = session.get('combined_data')

    logger.info(f"combined_data : {combined_data}")

    data_to_update = combined_data[new_category]

    logger.info(f"inside - create_new_category() <")
    logger.info(f"{Color.BRIGHT_BLUE}new_category: {new_category} {Color.END}")
    logger.info(f"{Color.CYAN}combined_data: {combined_data} {Color.END}")
    logger.info(f"{Color.BRIGHT_GREEN}data_to_update: {data_to_update} {Color.END}")
    logger.info(f"inside - create_new_category() >")

    updated_documents = update_potential_category_by_id(dbh, data_to_update, new_category, COLLECTION)    

    update_documents_confirmation = []

    logger.info(f"--------------------------------")
    logger.info(f"updated_documents :")
    for doc in updated_documents:
        logger.info(doc)
        logger.info('=============')
        if doc.modified_count > 0:
            update_documents_confirmation.append(True)
    logger.info(f"--------------------------------")



    categories_in_db = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)
    if new_category not in categories_in_db:
        temp = True
    else:
        temp = False
    logger.info(f"if new_category not in categories_in_db: {temp}")


    if new_category not in categories_in_db:
        logger.info(f"New category({new_category}) are NOT in category collection in DB")
        logger.info(f"Creating new category in db...")
        new_category_id = create_category_collection_in_db(dbh, CATEGORIES_COLLECTION, [new_category])
        logger.info(f"--------------------------------")
        logger.info(f"new_category_id : {new_category_id}")
        logger.info(f"--------------------------------")


    if False not in update_documents_confirmation:
        is_documents_updated = True
    else:
        is_documents_updated = False

    if new_category_id[0] is not None:
        is_new_category_created = True
    else:
        is_new_category_created = False
        
    response_data = {
        'is_documents_updated': is_documents_updated,
        'is_new_category_created': is_new_category_created
    }

    return jsonify(response_data)



@category_blueprint.route('/abandon_category')
def abandon_category():
    logger.info("inside abandon_category(): route ----------------------")

    new_category = request.args.get('key')

    logger.info(f"new_category : {new_category}")

    combined_data = session.get('combined_data')

    logger.info(f"combined_data : {combined_data}")

    data_to_update = combined_data[new_category]

    logger.info(f"inside - create_new_category() <")
    logger.info(f"new_category: {new_category}")
    logger.info(f"combined_data: {combined_data}")
    logger.info(f"data_to_update: {data_to_update}")
    logger.info(f"inside - create_new_category() >")

    updated_documents = abandon_potential_category_by_id(dbh, data_to_update, COLLECTION)    

    update_documents_confirmation = []

    logger.info(f"--------------------------------")
    logger.info(f"updated_documents :")
    for doc in updated_documents:
        logger.info(doc)
        logger.info('=============')
        if doc.modified_count > 0:
            update_documents_confirmation.append(True)
    logger.info(f"--------------------------------")

    if False not in update_documents_confirmation:
        is_documents_updated = True
        response_data = {
            'is_successfully': True,
            'text': f"Від категорії '{new_category}' відмова пройшла успішно."
        }
    else:
        is_documents_updated = False
        response_data = {
            'is_successfully': False,
            'text': f"Сталася помилка при спробі відмовитись від категорії '{new_category}'"
        }

    return jsonify(response_data)


@category_blueprint.route('/download-category', methods=['GET'])
def download_category():
    logger.info("/download-category route in app.py")

    documents = session.get('documents')
    logger.info('<<<----------------------------------------------->>>')
    logger.info(f"documents: {documents}")
    logger.info('<<<----------------------------------------------->>>')


    xlsx_filename = f"AI_results.xlsx"
    xlsx_filepath = os.path.join(UPLOAD_FOLDER, xlsx_filename)

    file_to_send = create_document_xlsx(documents, xlsx_filepath)

    filename = 'RESULTS'

    #FIXME : HARDCODED SHIT
    # file_to_send = '/Users/rostislavzubenko/Work/CC AI/combine_sent_cat_aio/uploads/AI_results.xlsx'
    # file_to_send = '/home/P-RZuben10302/flask/test/sentiment_category_aio/uploads/AI_results.xlsx'

    # Get the absolute path of the current file
    current_file_path = os.path.abspath(__file__)

    # Get the base directory of the application
    # basedir = os.path.dirname(os.path.dirname(current_file_path))
    basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))


    file_to_send = os.path.join(basedir, f"{Config.UPLOAD_FOLDER}/AI_results.xlsx")

    response = send_file(
        file_to_send,
        # orchestrated_filepath,
        as_attachment=True,
        download_name=f"AI_{filename}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    return response


