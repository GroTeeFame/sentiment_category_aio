from . import category_blueptint
from flask import render_template
from app.config import Config
from flask import current_app

import os
import sys
import uuid
from flask import Flask, request, Response, copy_current_request_context, send_file, render_template, session, flash, jsonify, redirect, url_for, redirect, send_from_directory, url_for
from flask_dropzone import Dropzone
from flask_socketio import emit
from flask_session import Session
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

# from app import socketio

load_dotenv()

KEY = os.getenv("SS_KEY")
LOCATION = os.getenv("SS_LOCATION")






print(f" routes.py /app/blueprints/category ")


# # @category_blueptint.route('/category')
# @category_blueptint.route('/category')
# def category_index():
#     print(f" routes.py /app/blueprints/category category_index()")
#     return render_template('category/category.html', title='Категоризація')


# @category_blueptint.route('/newcategory')
# def newcategory():
#     pass
#     return render_template('category/newcategory.html', title="Нові категорії")



# DB 
DB_NAME = Config.DB_NAME
COLLECTION = Config.COLLECTION
CATEGORIES_COLLECTION = Config.CATEGORIES_COLLECTION

# GPT_REPETITION_CALLS = 5


#for debuging, set this flag to True to production.
# use_hash_flag = False
use_hash_flag = True


UPLOAD_FOLDER = 'uploads'
basedir = os.path.abspath(os.path.dirname(__file__))


# def create_hash(data):
#     from . import hash_file

#     return hash_file(data)

try:
    dbh = MongoDBHandler(db_name=DB_NAME)

    collection = COLLECTION

    print(f"{Color.BLUE} Connection with DB({Color.RED}{DB_NAME}{Color.BLUE}) was successfully established in app.py{Color.END}")

    # print(create_category_collection_in_db(dbh, CATEGORIES_COLLECTION, categories_for_db))

except Exception as e:
    print(f"Error when trying to connect to db...")
    raise e


    # socketio = SocketIO(app, cors_allowed_origins="*")



# def connect_to_db():
#     from . import MongoDBHandler

#     try:
#         dbh = MongoDBHandler(db_name=DB_NAME)

#         collection = COLLECTION

#         print(f"{Color.BLUE} Connection with DB({Color.RED}{DB_NAME}{Color.BLUE}) was successfully established in app.py{Color.END}")

#         # print(create_category_collection_in_db(dbh, CATEGORIES_COLLECTION, categories_for_db))

#     except Exception as e:
#         print(f"Error when trying to connect to db...")
#         raise e

#     return dbh

# app = Flask(__name__)

# app.secret_key = 'mysupersecretkey'

# app.config.update(
#     UPLOADED_PATH=os.path.join(basedir, UPLOAD_FOLDER),
#     DROPZONE_ALLOWED_FILE_CUSTOM= True,
#     DROPZONE_ALLOWED_FILE_TYPE='.wav',
#     DROPZONE_MAX_FILE_SIZE=50,
#     DROPZONE_MAX_FILES=10,
#     DROPZONE_UPLOAD_ON_CLICK=True,
#     SESSION_PERMANENT = True,
#     SESSION_TYPE = 'filesystem',
#     PERMANENT_SESSION_LIFETIME = timedelta(hours=5)
# )
# dropzone = Dropzone(app)
# socketio = SocketIO(app, cors_allowed_origins="*")



# app.config['SESSION_TYPE'] = 'filesystem'

# # Optionally set a directory to store session files
# app.config['SESSION_FILE_DIR'] = os.path.join(basedir, 'flask_session')
# os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize the session
# Session(app)


# @category_blueptint.route('/category')
@category_blueptint.route('/category')
def category_index():
    print(f" routes.py /app/blueprints/category category_index()")
    return render_template('category/category.html', title='Категоризація')


# @category_blueptint.route('/newcategory')
# def newcategory():
#     pass
#     return render_template('category/newcategory.html', title="Нові категорії")

# socketio = current_app.socketio

# @socketio.on("connect")
# def handle_connect():
#     print(f"{Color.GREEN} Client connected with socketIO...{Color.END} ")


@category_blueptint.route('/analyze', methods=['POST'])
async def analyze():
    print("'/analyze' route in app.py", file=sys.stderr)

    socketio = current_app.socketio

    # socketio.emit("client_update", "--- '/analyze' route in app.py ---")

    if request.method == 'POST':
        results = []  # To store the results for each file

        print("'/analyze' route in app.py - if request.method == 'POST':", file=sys.stderr)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        i = 1

        print("---------------------------------------")
        print(f"FILES COUNTS: {len(request.files)}")
        print("---------------------------------------")

        for key, f in request.files.items():
            print(f"i : {i}")
            # print(f"request.files.items() :  {request.files.items()}")

            # print(f"{Color.BOLD} f: {f} {Color.END}")
            # print(f"{Color.BOLD} f.filename: {f.filename} {Color.END}")

            if key.startswith('file'):
                socketio.emit("client_update", f"Опрацьовується доумент {i} з {len(request.files)}")

                print(f"'/analyze' route in app.py - processing {key}:", file=sys.stderr)
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
                    print(f"Error when trying to create hash from file ({filepath})", file=sys.stderr)
                    continue  # Skip to next file

                fileInSystem = dbh.find_document(collection, {"_id": fileHash})
                if use_hash_flag:
                    print(f"{Color.YELLOW} use_hash_flag = TRUE {Color.END}")
                    if fileInSystem is None:
                        print(f"New file in system, start processing file...")
                        result = compose_file_process(dbh, og_filename, filepath, fileHash, collection, CATEGORIES_COLLECTION)
                        print(f"result: {result}")
                    else:
                        result = fileInSystem
                        # TODO: delete time.sleep() its only for testing. <
                        # print("time.sleep(3)")
                        # time.sleep(3)
                        # print("time.sleep(3)")
                        # TODO: delete time.sleep() its only for testing. >

                        print(f"--- Result from DB for file: '{filepath}' with hash (_id in db): '{fileHash}' ---")
                        print(fileInSystem)
                else:
                    print(f"{Color.YELLOW} use_hash_flag = FALSE {Color.END}")
                    result = compose_file_process(dbh, filepath, fileHash, collection, CATEGORIES_COLLECTION)
                    print(f"result: {result}")

                results.append(result)

                try:
                    os.remove(filepath)
                    print(f"{Color.PURPLE} {filepath} file was successfully deleted from system.{Color.END}")
                except Exception as e:
                    print(f"{Color.RED} ERROR: can't delete {filepath} from system. Details: {e} {Color.END}")

            i += 1

        print("===============================")
        print(f"{Color.BLUE}results: {results} {Color.END}")
        print(f"{Color.GREEN} length of results: {len(results)} {Color.END}")
        print("===============================")

        # Session['documents'] = results
        session['documents'] = results

        # session['documents'] = json.dumps(results)

        return render_template('category/category_result.html', documents=results)













@category_blueptint.route('/newcategory')
def newcategory():
    print("'/newcategory' route in app.py", file=sys.stderr)

    socketio = current_app.socketio

    socketio.emit("newcategory", f"@app.route('/newcategory')")


    categories = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)
    print(f"{Color.BRIGHT_CYAN}categories = {categories} {Color.END}")
    session['categories_from_db'] = categories
    return render_template('category/newcategory.html', title="Нові категорії", categories=categories)


@category_blueptint.route('/submit-dates', methods=['POST'])
def submit_dates():
    print("'/submit' route in app.py", file=sys.stderr)

    socketio = current_app.socketio

    socketio.emit("newcategory", f"@app.route('/submit-dates', methods=['POST'])")

    categories_from_db = session.get('categories_from_db')
    print(f"categories_from_db from session : {categories_from_db}")
    if not categories_from_db:
        categories_from_db = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)
        print(f"categories_from_db from DB : {categories_from_db}")


    # categories = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)

    start_date = datetime.strptime(request.form.get('startDate'), "%d-%m-%Y")
    end_date = datetime.strptime(request.form.get('endDate'), "%d-%m-%Y").replace(hour=23, minute=59, second=59)

    date_obj = {
        "start_date": start_date.strftime("%d.%m.%y"),
        "end_date": end_date.strftime("%d.%m.%y")
    }

    # Perform database operations using the start_date and end_date
    data_with_potencial_new_category = get_potential_category_by_dates(dbh, COLLECTION, start_date, end_date)

    print(f"data_with_potencial_new_category")
    print(data_with_potencial_new_category)
    print("1111111111111111111111111111111")

    # TODO: compose_document_update()!!! - hueta...

    if not data_with_potencial_new_category:
        return render_template('category/updated_info.html', combined_data=[], date_obj=date_obj)

    print("---------------------------------")
    print("get_potential_category_by_dates:")
    print(data_with_potencial_new_category)
    print("---------------------------------")

    potencial_new_category = [doc['potential_new_category'] for doc in data_with_potencial_new_category]

    print("---------------------------------")
    print("potencial_new_category:")
    print(f"{Color.CYAN}{potencial_new_category}{Color.END}")
    print("---------------------------------")

    # classifyed_potential_categories = classify_categories_with_gpt(data_with_potencial_new_category)
    classifyed_potential_categories = classify_categories_with_gpt(potencial_new_category)

    print("---------------------------------")
    print("classify_categories_with_gpt in submit_dates route:")
    print(f"{Color.CYAN}{classifyed_potential_categories}{Color.END}")
    print("---------------------------------")

    print("===PLAY WITH classifyed_potential_categories =============<")
    for key, values in classifyed_potential_categories.items():
        print(f"Key: {key}")
        for value in values:
            print(f"  ╰─Value: {value}")
    # for doc in classifyed_potential_categories:
    #     print(doc)
    print("===PLAY WITH classifyed_potential_categories =============>")

    combined_data = {}

    for key, value_list in classifyed_potential_categories.items():
        # Filter the list to find dictionary entries where `potential_new_category` matches any string in the value list
        matched_dicts = [
            entry for entry in data_with_potencial_new_category if entry['potential_new_category'] in value_list
        ]
        combined_data[key] = matched_dicts

    print("---------------------------------")
    print("combined_data in submit_dates route:")
    print(f"{Color.BRIGHT_BLUE}{combined_data}{Color.END}")
    print("---------------------------------")

    session['combined_data'] = combined_data

    # Return only the HTML for the updated information
    return render_template('category/updated_info.html', combined_data=combined_data, date_obj=date_obj)
    # return render_template('partials/updated_info.html', classifyed_potential_categories=classifyed_potential_categories, data_with_potencial_new_category=data_with_potencial_new_category)
    # return render_template('partials/updated_info.html', updated_info=data_with_potencial_new_category)
    # return render_template('partials/updated_info.html', updated_info=data_with_potencial_new_category)


@category_blueptint.route('/get_category_from_db')
def get_category_from_db():
    categories = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)
    return jsonify(categories)


@category_blueptint.route('/get_category_data')
def get_category_data():
    key = request.args.get('key')

    combined_data = session.get('combined_data')

    data_to_return = combined_data[key]

    print(f"{Color.BG_BRIGHT_BLUE}key: {key} {Color.END}")
    print(f"{Color.BG_CYAN}combined_data: {combined_data} {Color.END}")
    print(f"{Color.BG_BRIGHT_GREEN}data_to_return: {data_to_return} {Color.END}")


    
    if key in combined_data:
        return jsonify(combined_data[key])
    else:
        return jsonify({'error': 'No data found for this category'}), 404


@category_blueptint.route('/create_new_category')
def create_new_category():
    print("inside create_new_category(): route +++++++++++++++++++++++++++")
    new_category = request.args.get('key')

    print(f"new_category : {new_category}")

    combined_data = session.get('combined_data')

    print(f"combined_data : {combined_data}")


    data_to_update = combined_data[new_category]

    print(f"inside - create_new_category() <")
    print(f"{Color.BRIGHT_BLUE}new_category: {new_category} {Color.END}")
    print(f"{Color.CYAN}combined_data: {combined_data} {Color.END}")
    print(f"{Color.BRIGHT_GREEN}data_to_update: {data_to_update} {Color.END}")
    print(f"inside - create_new_category() >")

    # update_potential_category_by_id,
    # create_category_collection_in_db,
    updated_documents = update_potential_category_by_id(dbh, data_to_update, new_category, COLLECTION)    

    update_documents_confirmation = []

    print(f"{Color.BG_BRIGHT_WHITE} -------------------------------- {Color.END}")
    print(f"updated_documents :")
    for doc in updated_documents:
        print(doc)
        print('=============')
        if doc.modified_count > 0:
        # if doc['nModified'] > 0:
            update_documents_confirmation.append(True)
    print(f"{Color.BG_BRIGHT_WHITE} -------------------------------- {Color.END}")



    categories_in_db = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)
    if new_category not in categories_in_db:
        temp = True
    else:
        temp = False
    print(f"if new_category not in categories_in_db: {temp}")



    if new_category not in categories_in_db:
        print(f"New category({new_category}) are NOT in category collection in DB")
        print(f"{Color.GREEN} Creating new category in db... {Color.END}")
        new_category_id = create_category_collection_in_db(dbh, CATEGORIES_COLLECTION, [new_category])
        print(f"{Color.BG_BRIGHT_GREEN} -------------------------------- {Color.END}")
        print(f"new_category_id : {new_category_id}")
        print(f"{Color.BG_BRIGHT_GREEN} -------------------------------- {Color.END}")

    # response_data = {
    #     "new_category_id" : new_category_id,
    #     "updated_documents" : updated_documents,
    # }

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



@category_blueptint.route('/abandon_category')
def abandon_category():
    print("inside abandon_category(): route ----------------------")

    new_category = request.args.get('key')

    print(f"new_category : {new_category}")

    combined_data = session.get('combined_data')

    print(f"combined_data : {combined_data}")

    data_to_update = combined_data[new_category]

    print(f"inside - create_new_category() <")
    print(f"{Color.BRIGHT_BLUE}new_category: {new_category} {Color.END}")
    print(f"{Color.CYAN}combined_data: {combined_data} {Color.END}")
    print(f"{Color.BRIGHT_GREEN}data_to_update: {data_to_update} {Color.END}")
    print(f"inside - create_new_category() >")

    updated_documents = abandon_potential_category_by_id(dbh, data_to_update, COLLECTION)    

    update_documents_confirmation = []

    print(f"{Color.BG_BRIGHT_WHITE} -------------------------------- {Color.END}")
    print(f"updated_documents :")
    for doc in updated_documents:
        print(doc)
        print('=============')
        if doc.modified_count > 0:
        # if doc['nModified'] > 0:
            update_documents_confirmation.append(True)
    print(f"{Color.BG_BRIGHT_WHITE} -------------------------------- {Color.END}")

    if False not in update_documents_confirmation:
        is_documents_updated = True
        response_data = {
            'is_successfully': True,
            'text': f"Від категорії '{new_category}' відмова пройшла успішно."
        }
        # return f"Від категорії '{new_category}' відмова пройшла успішно."
    else:
        is_documents_updated = False
        response_data = {
            'is_successfully': False,
            'text': f"Сталася помилка при спробі відмовитись від категорії '{new_category}'"
        }
        # return f"Сталася помилка при спробі відмовитись від категорії '{new_category}'"


    return jsonify(response_data)

    # return "abandon_category(): - complete"
    pass





@category_blueptint.route('/download-category', methods=['GET'])
def download_category():
    print("/download route in app.py", file=sys.stderr)

    documents = session.get('documents')
    print('<<<----------------------------------------------->>>')
    print(f"{Color.YELLOW}documents: {documents} {Color.END}")
    print('<<<----------------------------------------------->>>')


    xlsx_filename = f"AI_results.xlsx"
    xlsx_filepath = os.path.join(UPLOAD_FOLDER, xlsx_filename)

    file_to_send = create_document_xlsx(documents, xlsx_filepath)

    filename = 'RESULTS'

    #FIXME : HARDCODED SHIT
    file_to_send = '/Users/rostislavzubenko/Work/CC AI/combine_sent_cat_aio/uploads/AI_results.xlsx'

    response = send_file(
        file_to_send,
        # orchestrated_filepath,
        as_attachment=True,
        download_name=f"AI_{filename}",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    return response


