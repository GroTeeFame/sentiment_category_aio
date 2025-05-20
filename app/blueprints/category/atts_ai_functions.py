import os
from flask import current_app

# os.environ['http_proxy'] = 'http://proxy.ubank.local:3128'
# os.environ['https_proxy'] = 'http://proxy.ubank.local:3128'
# os.environ['HTTP_PROXY'] = 'http://proxy.ubank.local:3128'
# os.environ['HTTPS_PROXY'] = 'http://proxy.ubank.local:3128'

import azure.cognitiveservices.speech as speechsdk
import sys
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI
from collections import Counter

from app.config import Config

CONVERSATION_CATEGORIES = Config.CONVERSATION_CATEGORIES
GET_CATEGORY_FROM_GPT_PROMPT = Config.GET_CATEGORY_FROM_GPT_PROMPT
CLASSIFY_CATEGORIES_WITH_GPT_PROMPT = Config.CLASSIFY_CATEGORIES_WITH_GPT_PROMPT
categories_for_db = Config.categories_for_db

from app.blueprints.category.hasher import hash_file

from app.logger_setup import setup_logger

logger = setup_logger(__name__)

# from colors import Color
from app.blueprints.category.colors import Color

load_dotenv()

KEY = os.getenv("SS_KEY")
LOCATION = os.getenv("SS_LOCATION")

GPT_REPETITION_CALLS = Config.GPT_REPETITION_CALLS

use_hash_flag = False

def validate_environment_variables():
    if not KEY or not LOCATION:
        logger.error("Speech Service key and location must be set in environment variables.")
        raise ValueError("Speech Service key and location must be set in environment variables.")

def configure_speech(audio_file_path):
    # validate_environment_variables()
    if not KEY or not LOCATION:
        logger.error("Speech Service key and location must be set in environment variables.")
        raise ValueError("Speech Service key and location must be set in environment variables.")
    # Configure speech
    speech_config = speechsdk.SpeechConfig(subscription=KEY, region=LOCATION)
    speech_config.speech_recognition_language = "uk-UA"

    # Set proxy config
    proxy_hostname = 'proxy.ubank.local'
    proxy_port = 3128
    proxy_username = None
    proxy_password = None

    speech_config.set_proxy(proxy_hostname, proxy_port, proxy_username, proxy_password)
    
    # Config audio
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
    return speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)


def process_azure_standard(filename):
    log_lines = [
        f"🔊 Використовується Azure Speech Standard для файлу: {filename}",
        "🛠️ Створення конфігурації Azure Speech..."
    ]
    all_texts = []

    recognizer = configure_speech(filename)
    done = False

    def handle_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            txt = evt.result.text.strip()
            all_texts.append(txt)
            logger.info(f"Розпізнано: {txt}")

    def handle_canceled(evt):
        if evt.reason == speechsdk.CancellationReason.Error:
            log_lines.append(f"⚠️ Azure STT Cancelled: {evt.error_details}")
            logger.info(f"Azure STT Cancelled: {evt.error_details}")

    def stop_cb(evt):
        nonlocal done
        done = True
        log_lines.append("🛑 Сесія розпізнавання завершена.")
        logger.info("Сесія розпізнавання завершена.")

    recognizer.recognized.connect(handle_recognized)
    recognizer.canceled.connect(handle_canceled)
    recognizer.session_stopped.connect(stop_cb)

    log_lines.append("▶️ Початок розпізнавання (асинхронно)...")
    logger.info("Початок розпізнавання (асинхронно)...")
    recognizer.start_continuous_recognition_async().get()

    while not done:
        time.sleep(0.1)
    recognizer.stop_continuous_recognition_async().get()

    if not all_texts:
        return "Сталася під час опрацювання файлу, немає результату (порожньо)"
    
    aggregated_text = " ".join(all_texts).strip()
    log_lines.append(f"🎤 Розпізнано (загалом): {aggregated_text}")
    logger.info(f"Розпізнано (загалом): {aggregated_text}")

    out_name = filename.replace(".wav", "-azure.txt")
    log_lines.append("✅ Розпізнавання Azure завершено успішно.")
    logger.info("Розпізнавання Azure завершено успішно.")
    logger.info("------PRINTING LOGS:----------------------------------------------------")
    for log in log_lines:
        logger.info(log)
    logger.info("------------------------------------------------------------------------")

    return aggregated_text

def get_category_from_gpt(text):
    client = AzureOpenAI(
        azure_endpoint = os.getenv("GPT_ENDPOINT"), 
        api_key = os.getenv("GPT_KEY"),  
        api_version="2024-02-01"
    )
    response = client.chat.completions.create(
        model="gpt-4o-ub-test-080624", # model = "deployment_name".
        messages=[
            {"role": "system", "content": f"{GET_CATEGORY_FROM_GPT_PROMPT} {CONVERSATION_CATEGORIES}"},
            {"role": "user", "content": f"{text}"},
        ],
        temperature=0.0001,  # Adjust the creativity of the model's responses
        max_tokens=150,  # Limit the response length
        top_p=0.8,       # Limit the probability mass of the tokens considered
        frequency_penalty=0.0,  # Penalize new tokens based on their frequency in text so far
        presence_penalty=0.0    # Penalize new tokens based on their presence in text so far
    )

    logger.info(response.choices[0].message.content)

    return response.choices[0].message.content


def classify_categories_with_gpt(categories):
    """Classify categories using the GPT model.

    Args:
        categories (list): A list of categories to classify.

    Returns:
        dict | None: A dictionary of classified categories or None on error.
    """
    logger.info(f"--> classify_categories_with_gpt() -->")
    client = AzureOpenAI(
        azure_endpoint = os.getenv("GPT_ENDPOINT"), 
        api_key = os.getenv("GPT_KEY"),  
        api_version="2024-02-01"
        # api_version="2024-10-01"
    )

    try:
        logger.info(f"CLASSIFY_CATEGORIES_WITH_GPT_PROMPT: ---")
        logger.info(CLASSIFY_CATEGORIES_WITH_GPT_PROMPT)
        logger.info("------------------------------")
        logger.info(f"CATEGORIES: {categories}")
        logger.info("------------------------------")
        response = client.chat.completions.create(
            model="gpt-4o-ub-test-080624", # model = "deployment_name".
            messages=[
                {"role": "system", "content": f"{CLASSIFY_CATEGORIES_WITH_GPT_PROMPT} {categories}"},
                # {"role": "user", "content": f"{text}"},
            ],
            temperature=0.0001,  # Adjust the creativity of the model's responses
            # max_tokens=150,  # Limit the response length
            top_p=0.8,       # Limit the probability mass of the tokens considered
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        logger.info('-response.choices[0].message.content---------------------------------')
        logger.info(response.choices[0].message.content)
        logger.info('----------------------------------')
    except Exception as e:
        logger.error(f"⚠️ ERROR: Error with connecting to GPT: {e}")
        return None

    logger.info("=======================================")
    logger.info(f"Fresh from GPT: ")
    logger.info("response.choices[0].message.content :")
    logger.info(response.choices[0].message.content)
    logger.info("=======================================")
    logger.info("response.choices[0].message.content[8:-3] :")
    logger.info(response.choices[0].message.content[8:-3])
    logger.info("=======================================")

    try:
        json_data = f"""{response.choices[0].message.content[8:-3]}"""
        data = json.loads(json_data)
        logger.info(f"All good in try to parse json")
        return data
    except Exception as e:
        logger.error(f"Except in try to parse json")
        json_data = f"""{response.choices[0].message.content}"""
        data = json.loads(json_data)
        return data


def get_category_from_gpt_with_repetition(dbh, CATEGORIES_COLLECTION, text, repetition=5,):
    """Get a category from the GPT model with repeated calls to ensure consistency.

    Args:
        text (str): The text to categorize.
        repetition (int): The number of repetition calls.

    Returns:
        dict: The most frequent category results.
    """
    logger.info(f"--> get_category_from_gpt_with_repetition() -->")
    client = AzureOpenAI(
        azure_endpoint = os.getenv("GPT_ENDPOINT"), 
        api_key = os.getenv("GPT_KEY"),  
        api_version="2024-02-01"
        # api_version="2024-10-01"
    )

    if dbh.check_if_collection_exist(CATEGORIES_COLLECTION) == False:
        try:
            categories_collection_ids = create_category_collection_in_db(dbh, CATEGORIES_COLLECTION, categories_for_db)
        except Exception as e:
            logger.error(f"⚠️ ERROR: {e}")
            raise e #TODO: #FIXME: bad error handling!!!! 
        if categories_collection_ids:
            logger.info(f" Collection of categories was successfully created in DB. Categories ids: {categories_collection_ids}")
        else:
            logger.error("Data needed for file processing NOT found in DB...")
            raise ValueError("Data needed for file processing NOT found in DB...")

    conversation_categories = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)
    logger.info("----------TEST_PROMPT------------------>")
    logger.info(f"{GET_CATEGORY_FROM_GPT_PROMPT}")
    logger.info(f"=====conversation_categories==========")
    logger.info(f"{conversation_categories}")
    logger.info("----------TEST_PROMPT------------------<")

    aggregated_responce = []

    for i in range(1, repetition+1):
        logger.info(f"Repetition {i}...")
        try:
            response = client.chat.completions.create(
                model="gpt-4o-ub-test-080624", # model = "deployment_name".
                messages=[
                    # {"role": "system", "content": f"{GET_CATEGORY_FROM_GPT_PROMPT} {CONVERSATION_CATEGORIES}"},
                    {"role": "system", "content": f"{GET_CATEGORY_FROM_GPT_PROMPT} {conversation_categories}"},
                    {"role": "user", "content": f"{text}"},
                ],
                temperature=0.0001,  # Adjust the creativity of the model's responses
                max_tokens=150,  # Limit the response length
                top_p=0.8,       # Limit the probability mass of the tokens considered
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
        except Exception as e:
            logger.info(f"⚠️ ERROR: arouse an error with connecting to GPT: {e}")
        try:
            json_gpt_category = json.loads(response.choices[0].message.content[8:-3])
            aggregated_responce.append({
                "category_from_list": json_gpt_category["category_from_list"],
                "potential_category": json_gpt_category["potential_category"]
            })
        except Exception as e:
            logger.error(f"⚠️ ERROR: arouse an error with converting GPT response to json: {e}")

    aggregated_category_from_list = [i["category_from_list"] for i in aggregated_responce]
    aggregated_potential_category = [i["potential_category"] for i in aggregated_responce]

    logger.info(f"Printing results from GPT:")
    logger.info(aggregated_category_from_list)
    logger.info(aggregated_potential_category)
    logger.info('--------------------------------')

    sorted_aggregated_category_from_list = sorted(aggregated_category_from_list, key=Counter(aggregated_category_from_list).get, reverse=True)
    sorted_aggregated_potential_category = sorted(aggregated_potential_category, key=Counter(aggregated_potential_category).get, reverse=True)

    return {
        "category_from_list": sorted_aggregated_category_from_list[0],
        "potential_category": sorted_aggregated_potential_category[0]
    }

#=DB================================================================


def create_category_collection_in_db(dbh, collection, categories):
    """Create a collection of category documents in the database.

    Args:
        collection (str): The name of the database collection.
        categories (list): The list of category names to create.

    Returns:
        list: IDs of the inserted category documents.
    """
    inserted_doc_ids = []
    for category in categories:
        try: # if one category is fail to create as a document in db, code is continue to creates remaining categories.
            document = {
                "category_name": category,
                "timestamp": datetime.now(),
            }
            inserted_id = dbh.insert_document(collection, document)
            inserted_doc_ids.append(inserted_id)
        except Exception as e:
            logger.error('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
            logger.error(f"⚠️ ERROR: when trying to create a category document occur an error: ")
            logger.error(f"⚠️ category: {category}")
            logger.error(f"⚠️ more details: {e}")
            logger.error('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
    logger.info(f"inserted_doc_ids: {inserted_doc_ids}")
    return inserted_doc_ids

def get_list_of_categories_from_db(dbh, collection):
    """Retrieve a list of categories from the database.

    Args:
        collection (str): The name of the database collection.

    Returns:
        list: The list of category names.
    """
    list_of_categories = []
    try:
        result = dbh.find_documents(collection, {})
    except Exception as e:
        logger.error('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
        logger.error(f"⚠️ ERROR: when trying to get categories from DB: ")
        logger.error(f"⚠️ more details: {e}")
        logger.error('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
        return []

    for doc in result:
        list_of_categories.append(doc["category_name"])
    return list_of_categories


def get_potential_category_by_dates(dbh, collection, start_date, end_date):
    """Retrieve potential categories by date range from the database.

    Args:
        start_date (datetime): The start date for the query.
        end_date (datetime): The end date for the query.

    Returns:
        list: The list of potential categories within the date range.
    """
    documents = dbh.find_documents_by_date(
        collection,
        start_date,
        end_date,
        {"potential_new_category": {"$ne": "Null"}}
    )
    list_of_potential_category = [doc for doc in documents]
    return list_of_potential_category


def abandon_potential_category_by_id(dbh, documents_to_update, collection):
    """Update potential categories for documents in the database.

    Args:
        documents_to_update (list): The documents to update.
        new_categories (dict): The mapping of new categories.
    """
    updated_documents = []
    for document in documents_to_update:
        logger.info('--document------------------------->')
        logger.info(document)
        logger.info('---------------------------<')
        update_values = {
            "potential_new_category": "Null"
        }
        try:
            upd_doc = dbh.update_document_by_id(collection, document["_id"], update_values)
            logger.info('-- Updated Document ------------------------->')
            logger.info(upd_doc)
            logger.info('---------------------------<')
        except Exception as e:
            logger.info('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
            logger.info(f"⚠️ ERROR: when trying to update a document occur an error: ")
            logger.info(f"⚠️ document: {document}")
            logger.info(f"⚠️ update_values: {update_values}")
            logger.info(f"⚠️ more details: {e}")
            logger.info('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')

        logger.info('--upd_doc------------------------->')
        logger.info(upd_doc)
        logger.info('---------------------------<')

        updated_documents.append(upd_doc)
        
    return updated_documents


def update_potential_category_by_id(dbh, documents_to_update, new_category, collection):
    """Update potential categories for documents in the database.

    Args:
        documents_to_update (list): The documents to update.
        new_categories (dict): The mapping of new categories.
    """
    updated_documents = []
    for document in documents_to_update:
        logger.info('--document------------------------->')
        logger.info(document)
        logger.info('---------------------------<')
        update_values = {
            "category": new_category,
            "potential_new_category": "Null"
        }
        try:
            upd_doc = dbh.update_document_by_id(collection, document["_id"], update_values)
            logger.info('-- Updated Document ------------------------->')
            logger.info(upd_doc)
            logger.info('---------------------------<')
        except Exception as e:
            logger.info('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
            logger.info(f"⚠️ ERROR: when trying to update a document occur an error: ")
            logger.info(f"⚠️ document: {document}")
            logger.info(f"⚠️ update_values: {update_values}")
            logger.info(f"⚠️ more details: {e}")
            logger.info('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')

        logger.info('--upd_doc------------------------->')
        logger.info(upd_doc)
        logger.info('---------------------------<')

        updated_documents.append(upd_doc)
        
    return updated_documents


def compose_document_update(start_date, end_date):
    """Compose and update new categories for documents based on potential categories within a date range.

    Args:
        start_date (datetime): The start date for the document search.
        end_date (datetime): The end date for the document search.
    """
    potencial_new_category = get_potential_category_by_dates(start_date, end_date)
    logger.info("potential_new_category:")
    logger.info(potencial_new_category)
    logger.info("-------------------///")
    potencial_new_category_list = [i["potential_new_category"] for i in potencial_new_category]
    new_categorys = classify_categories_with_gpt(potencial_new_category_list)
    logger.info(f"aggregated new_category: {new_categorys}")

    for key, values in new_categorys.items():
        logger.info(f"Key: {key}")
        for value in values:
            logger.info(f"  ╰─Value: {value}")
    logger.info("-------------------///")

    update_potential_category_by_id(potencial_new_category, new_categorys)

#=================================================================


def compose_file_process(dbh, fileName, filePath, fileHash, collection, CATEGORIES_COLLECTION):
    """Process an audio file and insert the result into the database.

    Args:
        filePath (str): The path to the audio file.
        fileHash (str): The hash value of the file.

    Returns:
        str: The ID of the inserted document in the database, id is a hash of a file.
        # bson.ObjectId: The ID of the inserted document in the database.

    Raises:
        ValueError: If processing or writing data to the database fails.
    """
    ###
    rec_text = process_azure_standard(filePath)
    gpt_category = get_category_from_gpt_with_repetition(dbh, CATEGORIES_COLLECTION, rec_text)
    ###
    try:
        document = dbh.get_document_template(fileHash, fileName, rec_text, gpt_category["category_from_list"], gpt_category["potential_category"])
        logger.info(document)
        inserted_doc_id = dbh.insert_document(collection, document)
        logger.info(f"ID of inserted document is : {inserted_doc_id}")
    except Exception as e:
        logger.error(f"⚠️ Error when trying to process answers from AI, and write it to DB: {e}")
        raise ValueError("Cant process and write data to DB.")

    return document


def test_consistency(repetition, text):
    """Test the consistency of category detection by GPT over multiple calls.

    Args:
        repetition (int): The number of times to test.
        text (str): The text for testing.

    Returns:
        list: The list of categorization results from repeated GPT calls.
    """
    logger.info(text)

    list_of_category = []

    for i in range(1, repetition+1):
        logger.info(f"GPT call #{i}")

        if i < 10:
            number_for_obj = f" {i}"
        else:
            number_for_obj = f"{i}"
        try:
            gpt_category = get_category_from_gpt(text)
            json_gpt_category = json.loads(gpt_category[8:-3])
            list_of_category.append({
                "repetition": f"{i:02d}",
                "category_from_list": json_gpt_category["category_from_list"],
                "potential_category": json_gpt_category["potential_category"]
            })
        except Exception as e:
            logger.error(f"⚠️ ERROR: Error during GPT call or parsing response...")

    return list_of_category
