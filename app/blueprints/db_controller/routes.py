from . import db_controller_blueprint
from app.config import Config
from app.logger_setup import setup_logger
from app.mongodb_handler import MongoDBHandler


import os
import sys
from datetime import datetime


from flask import Flask, request, Response, copy_current_request_context, send_file, render_template, session, flash, jsonify, redirect, url_for, redirect, send_from_directory, url_for

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


DB_NAME = Config.DB_NAME
COLLECTION = Config.COLLECTION
CATEGORIES_COLLECTION = Config.CATEGORIES_COLLECTION

logger = setup_logger(__name__)

try:
    dbh = MongoDBHandler(db_name=DB_NAME)

    collection = COLLECTION

    logger.info(f"Connection with DB({DB_NAME}) was successfully established in db_controller/routes.py")

except Exception as e:
    logger.error(f"Error when trying to connect to db... db_controller/routes.py")
    raise e

@db_controller_blueprint.route('/db_controller')
def db_controller_index():
    return render_template('db_controller/db_controller.html', title='Контролер БД')
    # return "db_controller db_controller_index()"
    pass


@db_controller_blueprint.route('/get_category_from_db')
def get_category_from_db():
    categories = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)
    return jsonify(categories)


@db_controller_blueprint.route('/update-document-by-id', methods=['POST'])
def update_document_by_id():

    # print("db_controller_blueprint.route('/update-document-by-id')")

    data = request.get_json()

    updated_fields = {
        "file_name": data.get("file_name"),
        "category": data.get("category"),
        "potential_new_category": data.get("potential_new_category"),
        "transcription": data.get("transcription"),
    }

    result = dbh.update_document_by_id(COLLECTION, data["_id"], updated_fields)
    if result.modified_count > 0:
        return {"success": 1}
    else: 
        return {"error": 0}
    

@db_controller_blueprint.route('/delete-document-by-id', methods=['POST'])
def delete_document_by_id():
    data = request.get_json()
    # print(f"db_controller_blueprint.route('/delete-document-by-id') :  {data}")
    result = dbh.delete_document_by_id(COLLECTION, data)
    # print(f"RESULT -:- : {result}")
    if result.deleted_count > 0:
        return {"success": 1}
    else:
        return {"error": 0}


@db_controller_blueprint.route('/submit-dates-dbc', methods=['POST'])
def submit_dates():
    logger.info("'/submit-dates-dbc' route in db_controller/routes.py")

    start_date = datetime.strptime(request.form.get('startDate'), "%d-%m-%Y")
    end_date = datetime.strptime(request.form.get('endDate'), "%d-%m-%Y").replace(hour=23, minute=59, second=59)

    # Pagination parameters
    page = int(request.form.get('page', 1))
    limit = int(request.form.get('limit', 50))
    skip = (page - 1) * limit

    total_count = dbh.get_collection(collection).count_documents({
        'timestamp': {
            '$gte': start_date,
            '$lte': end_date
        }
    })

    cursor = dbh.find_documents_by_date(collection, start_date, end_date).skip(skip).limit(limit)
    list_of_documents = list(cursor)

    page_count = (total_count + limit - 1) // limit  # ceil division

    date_obj = {
        "start_date": start_date.strftime("%d.%m.%y"),
        "end_date": end_date.strftime("%d.%m.%y"),
        "page": page,
        "limit": limit,
        "total_pages": page_count,
        "total_count": total_count,
        "count_start": (page*limit)-limit,
    }

    return render_template(
        'db_controller/document_info.html',
        list_of_documents=list_of_documents,
        date_obj=date_obj
    )



# @db_controller_blueprint.route('/submit-dates-dbc', methods=['POST'])
# def submit_dates():
#     logger.info("'/submit-dates' route in db_contr.py")

#     start_date = datetime.strptime(request.form.get('startDate'), "%d-%m-%Y")
#     end_date = datetime.strptime(request.form.get('endDate'), "%d-%m-%Y").replace(hour=23, minute=59, second=59)

#     date_obj = {
#         "start_date": start_date.strftime("%d.%m.%y"),
#         "end_date": end_date.strftime("%d.%m.%y")
#     }

#     documents = dbh.find_documents_by_date(
#         collection,
#         start_date,
#         end_date
#     )
#     list_of_documents = [doc for doc in documents]
#     size_of_docs = sys.getsizeof(list_of_documents)
#     print(f"SIZE OF VARIABLE WITH DB DOCUMENT ITS {size_of_docs} bytes")

#     return render_template('db_controller/document_info.html', list_of_documents=list_of_documents, date_obj=date_obj)
