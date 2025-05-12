import azure.cognitiveservices.speech as speechsdk
import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI
from collections import Counter

from app.config import Config

CONVERSATION_CATEGORIES = Config.CONVERSATION_CATEGORIES
GET_CATEGORY_FROM_GPT_PROMPT = Config.GET_CATEGORY_FROM_GPT_PROMPT
CLASSIFY_CATEGORIES_WITH_GPT_PROMPT = Config.CLASSIFY_CATEGORIES_WITH_GPT_PROMPT
categories_for_db = Config.categories_for_db

# from mongodb_handler import MongoDBHandler
# from hasher import hash_file
# from . import hash_file

from app.blueprints.category.hasher import hash_file

# def hash_file(filepath):
#     # Create a hash object
#     sha256_hash = hashlib.sha256()
    
#     # Open the file in binary mode and read it in chunks
#     try:
#         with open(filepath, 'rb') as f:
#             # Read the file in chunks to efficiently handle large files
#             for byte_block in iter(lambda: f.read(4096), b""):
#                 sha256_hash.update(byte_block)
#     except FileNotFoundError:
#         # If the file is not found, provide a clear error message
#         print(f"Error: The file '{filepath}' does not exist.")
#         return None
#     except PermissionError:
#         # Handle permission errors when attempting to open the file
#         print(f"Error: Permission denied for file '{filepath}'.")
#         return None
    
#     # Get the hexadecimal digest of the hash
#     return sha256_hash.hexdigest()



# from colors import Color
from app.blueprints.category.colors import Color

load_dotenv()

KEY = os.getenv("SS_KEY")
LOCATION = os.getenv("SS_LOCATION")

GPT_REPETITION_CALLS = Config.GPT_REPETITION_CALLS

use_hash_flag = False

def validate_environment_variables():
    if not KEY or not LOCATION:
        raise ValueError("Speech Service key and location must be set in environment variables.")

def configure_speech(audio_file_path):
    # validate_environment_variables()
    if not KEY or not LOCATION:
        raise ValueError("Speech Service key and location must be set in environment variables.")
    speech_config = speechsdk.SpeechConfig(subscription=KEY, region=LOCATION)
    speech_config.speech_recognition_language = "uk-UA"
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
            # print(f"Розпізнано: {txt}")

    def handle_canceled(evt):
        if evt.reason == speechsdk.CancellationReason.Error:
            log_lines.append(f"⚠️ Azure STT Cancelled: {evt.error_details}")
            # print(f"Azure STT Cancelled: {evt.error_details}")

    def stop_cb(evt):
        nonlocal done
        done = True
        log_lines.append("🛑 Сесія розпізнавання завершена.")
        # print("Сесія розпізнавання завершена.")

    recognizer.recognized.connect(handle_recognized)
    recognizer.canceled.connect(handle_canceled)
    recognizer.session_stopped.connect(stop_cb)

    log_lines.append("▶️ Початок розпізнавання (асинхронно)...")
    # print("Початок розпізнавання (асинхронно)...")
    recognizer.start_continuous_recognition_async().get()

    while not done:
        time.sleep(0.1)
    recognizer.stop_continuous_recognition_async().get()

    if not all_texts:
        return "", "", "немає результату (порожньо)"
    
    aggregated_text = " ".join(all_texts).strip()
    log_lines.append(f"🎤 Розпізнано (загалом): {aggregated_text}")
    # print(f"Розпізнано (загалом): {aggregated_text}")

    out_name = filename.replace(".wav", "-azure.txt")
    log_lines.append("✅ Розпізнавання Azure завершено успішно.")
    # print("Розпізнавання Azure завершено успішно.")
    # print("------PRINTING LOGS:----------------------------------------------------")
    # for log in log_lines:
    #     print(log)
    # print("------------------------------------------------------------------------")

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

    # print(response.choices[0].message.content)

    return response.choices[0].message.content


def classify_categories_with_gpt(categories):
    """Classify categories using the GPT model.

    Args:
        categories (list): A list of categories to classify.

    Returns:
        dict | None: A dictionary of classified categories or None on error.
    """
    # print(f"--> classify_categories_with_gpt() -->")
    client = AzureOpenAI(
        azure_endpoint = os.getenv("GPT_ENDPOINT"), 
        api_key = os.getenv("GPT_KEY"),  
        api_version="2024-02-01"
        # api_version="2024-10-01"
    )

    try:
        # print(f"CLASSIFY_CATEGORIES_WITH_GPT_PROMPT: ---")
        # print(CLASSIFY_CATEGORIES_WITH_GPT_PROMPT)
        # print("------------------------------")
        # print(f"CATEGORIES: {Color.PURPLE}{categories}{Color.END}")
        # print("------------------------------")
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
        # print('-response.choices[0].message.content---------------------------------')
        # print(response.choices[0].message.content)
        # print('----------------------------------')
    except Exception as e:
        print(f"⚠️ ERROR: Error with connecting to GPT: {e}")
        return None

    # print("=======================================")
    # print(f"Fresh from GPT: ")
    # print("response.choices[0].message.content :")
    # print(response.choices[0].message.content)
    # print("=======================================")
    # print("response.choices[0].message.content[8:-3] :")
    # print(response.choices[0].message.content[8:-3])
    # print("=======================================")

    try:
        json_data = f"""{response.choices[0].message.content[8:-3]}"""
        data = json.loads(json_data)
        # print(f"{Color.BRIGHT_GREEN} All good in try to parse json {Color.END}")
        return data
    except Exception as e:
        # print(f"{Color.BRIGHT_RED} Except in try to parse json {Color.END}")
        print(f"Except in try to parse json")
        # data = response.choices[0].message.content
        json_data = f"""{response.choices[0].message.content}"""
        data = json.loads(json_data)
        return data
        # print(f"⚠️ ERROR: Error converting GPT response to JSON: {e}")
        # return None
    
    # try:
    #     gpt_response_start = response.choices[0].message.content[:8]
    #     gpt_response_end = response.choices[0].message.content[-3:]
    #     print(f"gpt_response_start : {gpt_response_start}")
    #     print(f"gpt_response_end : {gpt_response_end}")

    #     if gpt_response_start == "```json" and gpt_response_end == "```":
    #         json_data = f"""{response.choices[0].message.content[8:-3]}"""
    #         # print('-json_data---------------------------------')
    #         # print(json_data)
    #         # print('----------------------------------')
    #         data = json.loads(json_data)
    #     else:
    #         data = response.choices[0].message.content
    #     return data
    # except Exception as e:
    #     print(f"⚠️ ERROR: Error converting GPT response to JSON: {e}")
    #     return None

def get_category_from_gpt_with_repetition(dbh, CATEGORIES_COLLECTION, text, repetition=5,):
    """Get a category from the GPT model with repeated calls to ensure consistency.

    Args:
        text (str): The text to categorize.
        repetition (int): The number of repetition calls.

    Returns:
        dict: The most frequent category results.
    """
    # print(f"--> get_category_from_gpt_with_repetition() -->")
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
            # print(f"{Color.RED}⚠️ ERROR: {e} {Color.END}")
            print(f"⚠️ ERROR: {e}")
            raise e #TODO: #FIXME: bad error handling!!!! 
        if categories_collection_ids:
            # print(f"{Color.GREEN} Collection of categories was successfully created in DB. Categories ids: {categories_collection_ids}{Color.END}")
            print(f" Collection of categories was successfully created in DB. Categories ids: {categories_collection_ids}")
        else:
            raise ValueError("Data needed for file processing NOT found in DB...")

    conversation_categories = get_list_of_categories_from_db(dbh, CATEGORIES_COLLECTION)
    # print("----------TEST_PROMPT------------------>")
    # print(f"{GET_CATEGORY_FROM_GPT_PROMPT}")
    # print(f"=====conversation_categories==========")
    # print(f"{conversation_categories}")
    # print("----------TEST_PROMPT------------------<")

    aggregated_responce = []

    for i in range(1, repetition+1):
        # print(f"Repetition {i}...")
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
            print(f"⚠️ ERROR: arouse an error with connecting to GPT: {e}")
        try:
            json_gpt_category = json.loads(response.choices[0].message.content[8:-3])
            aggregated_responce.append({
                "category_from_list": json_gpt_category["category_from_list"],
                "potential_category": json_gpt_category["potential_category"]
            })
        except Exception as e:
            print(f"⚠️ ERROR: arouse an error with converting GPT response to json: {e}")

    aggregated_category_from_list = [i["category_from_list"] for i in aggregated_responce]
    aggregated_potential_category = [i["potential_category"] for i in aggregated_responce]

    # print(f"Printing results from GPT:")
    # print(aggregated_category_from_list)
    # print(aggregated_potential_category)
    # print('--------------------------------')

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
    # try: # if at least category is fails to add to db, all process will be stopt.
    for category in categories:
        try: # if one category is fail to create as a document in db, code is continue to creates remaining categories.
            document = {
                "category_name": category,
                "timestamp": datetime.now(),
            }
            inserted_id = dbh.insert_document(collection, document)
            inserted_doc_ids.append(inserted_id)
        except Exception as e:
            print('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
            print(f"⚠️ ERROR: when trying to create a category document occur an error: ")
            print(f"⚠️ category: {category}")
            print(f"⚠️ more details: {e}")
            print('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
    print(f"inserted_doc_ids: {inserted_doc_ids}")
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
        print('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
        print(f"⚠️ ERROR: when trying to get categories from DB: ")
        print(f"⚠️ more details: {e}")
        print('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
        return []

    for doc in result:
        list_of_categories.append(doc["category_name"])
    return list_of_categories


# def update_categories_in_db(collection):
#     pass

# start_date = datetime(2025, 3, 26)
# start_date = datetime(2025, 3, 27)
# end_date = datetime(2025, 3, 28) # up to 28.03.2025 00:00:00
# end_date = datetime(2025, 3, 26, 23, 59, 59)
# end_date = datetime(2025, 3, 27, 23, 59, 59)
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


# def add_new_category_


def abandon_potential_category_by_id(dbh, documents_to_update, collection):
    """Update potential categories for documents in the database.

    Args:
        documents_to_update (list): The documents to update.
        new_categories (dict): The mapping of new categories.
    """
    updated_documents = []
    for document in documents_to_update:
        # print('--document------------------------->')
        # print(document)
        # print('---------------------------<')
        # new_category = [key for key, values in new_categories.items() if document['potential_new_category'] in values]
        update_values = {
            "potential_new_category": "Null"
        }
        try:
            upd_doc = dbh.update_document_by_id(collection, document["_id"], update_values)
            # print('-- Updated Document ------------------------->')
            # print(upd_doc)
            # print('---------------------------<')
            # return upd_doc
        except Exception as e:
            print('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
            print(f"⚠️ ERROR: when trying to update a document occur an error: ")
            print(f"⚠️ document: {document}")
            print(f"⚠️ update_values: {update_values}")
            print(f"⚠️ more details: {e}")
            print('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')


        # print('--upd_doc------------------------->')
        # print(upd_doc)
        # print('---------------------------<')
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
        # print('--document------------------------->')
        # print(document)
        # print('---------------------------<')
        # new_category = [key for key, values in new_categories.items() if document['potential_new_category'] in values]
        update_values = {
            "category": new_category,
            "potential_new_category": "Null"
        }
        try:
            upd_doc = dbh.update_document_by_id(collection, document["_id"], update_values)
            # print('-- Updated Document ------------------------->')
            # print(upd_doc)
            # print('---------------------------<')
            # return upd_doc
        except Exception as e:
            print('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
            print(f"⚠️ ERROR: when trying to update a document occur an error: ")
            print(f"⚠️ document: {document}")
            print(f"⚠️ update_values: {update_values}")
            print(f"⚠️ more details: {e}")
            print('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')


        # print('--upd_doc------------------------->')
        # print(upd_doc)
        # print('---------------------------<')
        updated_documents.append(upd_doc)
        
    return updated_documents

# TODO: almost og...
# def update_potential_category_by_id(dbh, documents_to_update, new_categories, collection):
#     """Update potential categories for documents in the database.

#     Args:
#         documents_to_update (list): The documents to update.
#         new_categories (dict): The mapping of new categories.
#     """
#     updated_documents = []
#     for document in documents_to_update:
#         # print('--document------------------------->')
#         # print(document)
#         # print('---------------------------<')
#         new_category = [key for key, values in new_categories.items() if document['potential_new_category'] in values]
#         update_values = {
#             "category": new_category[0],
#             "potential_new_category": "Null"
#         }
#         try:
#             upd_doc = dbh.update_document_by_id(collection, document["_id"], update_values)
#             print('-- Updated Document ------------------------->')
#             print(upd_doc)
#             print('---------------------------<')
#             # return upd_doc
#         except Exception as e:
#             print('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')
#             print(f"⚠️ ERROR: when trying to update a document occur an error: ")
#             print(f"⚠️ document: {document}")
#             print(f"⚠️ update_values: {update_values}")
#             print(f"⚠️ more details: {e}")
#             print('-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!')


#         print('--upd_doc------------------------->')
#         print(upd_doc)
#         print('---------------------------<')
#         updated_documents.append(upd_doc)

#     return updated_documents



def compose_document_update(start_date, end_date):
    """Compose and update new categories for documents based on potential categories within a date range.

    Args:
        start_date (datetime): The start date for the document search.
        end_date (datetime): The end date for the document search.
    """
    # start_date = datetime(2025, 3, 26)
    # end_date = datetime(2025, 3, 28) # up to 28.03.2025 00:00:00
    potencial_new_category = get_potential_category_by_dates(start_date, end_date)
    # print("potential_new_category:")
    # print(potencial_new_category)
    # print("-------------------///")
    potencial_new_category_list = [i["potential_new_category"] for i in potencial_new_category]
    new_categorys = classify_categories_with_gpt(potencial_new_category_list)
    # print("aggregated new_category:")
    # print(new_categorys)
    # for key, values in new_categorys.items():
    #     print(f"Key: {key}")
    #     for value in values:
    #         print(f"  ╰─Value: {value}")
    # print("-------------------///")

    update_potential_category_by_id(potencial_new_category, new_categorys)


        # print(f"old category: {document['category']}")
        # print(f"old potential category: {document['potential_new_category']}")
        # print(f"new category: {new_category}")
        # for key, value in new_category.items():
        #     for value in values:
        #         if value ==     
    # dbh.update_document_by_id()


    # return ""
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
    # rec_text = 'TEXT'
    gpt_category = get_category_from_gpt_with_repetition(dbh, CATEGORIES_COLLECTION, rec_text)
    ###
    try:
        # document = dbh.get_document_template(fileHash, filePath, rec_text, gpt_category["category_from_list"], gpt_category["potential_category"])
        document = dbh.get_document_template(fileHash, fileName, rec_text, gpt_category["category_from_list"], gpt_category["potential_category"])
        # print(document)
        inserted_doc_id = dbh.insert_document(collection, document)
        print(f"ID of inserted document is : {inserted_doc_id}")
    except Exception as e:
        print(f"⚠️ Error when trying to process answers from AI, and write it to DB: {e}", file=sys.stderr)
        raise ValueError("Cant process and write data to DB.")

# TODO: remove this section of code for production, its only for testing. ---<
#     with open(f"{filePath[:-4]}.txt", "w") as f:
#         f.write(f"""
# Текст розпізнаний з розмови :
# {rec_text}
    
# Категорія дзвінка : 
# {gpt_category}

# Hash файлу, та _id в базі данних : "{fileHash}"
#     """)
#     print(f"Transcribed text write to '{filePath[:-4]}.txt' file.")
# TODO: end of section to remove --->


    # return inserted_doc_id#TODO: it return only the _id of created doc in db, i need to get back all document
    return document


def test_consistency(repetition, text):
    """Test the consistency of category detection by GPT over multiple calls.

    Args:
        repetition (int): The number of times to test.
        text (str): The text for testing.

    Returns:
        list: The list of categorization results from repeated GPT calls.
    """
    print(text)

    list_of_category = []

    for i in range(1, repetition+1):
        print(f"GPT call #{i}")

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
            print(f"⚠️ ERROR: Error during GPT call or parsing response...")

    return list_of_category

#TODO:####################################################################################################################
#TODO:####################################################################################################################
####################################################################################################################
#TODO: after compose_document_update() need to add new category to DB.
#TODO: change place where categories for gpt analize are taken. Now it hardcoded and get from conv_category.py. Need to redo it, so categories was taken from DB.
####################################################################################################################
#TODO:####################################################################################################################
#TODO:####################################################################################################################





# if __name__ == "__main__":
#     filePath = sys.argv[1]
#     print(f"file path : {filePath}")

#     try:
#         fileHash = hash_file(filePath)
#     except Exception as e:
#         print(f"Error when trying to create hash from file ({filePath})")
#         raise ValueError("Something wrong with file")

#     collection = 'ZALUPA' #TODO: temporary, to prevent build errors. !!!!!!!!!!!!

#     fileInSystem = dbh.find_document(collection, {"_id": fileHash})
#     # print(f"fileInSystem: {fileInSystem}")
#     if use_hash_flag: #TODO: #for debuging, set this flag to True to production.
#         if fileInSystem == None:
#             print(f"New file in system, start processing file...")
#             result = compose_file_process(filePath, fileHash)
#         else:
#             print(f"File already has been process by system.")
#             print(f"--- Result from DB for file: '{filePath}' with hash(_id in db): '{fileHash}' --- =>")
#             # print("---------------------------------------------------------")
#             print(fileInSystem)
#             print("---------------------------------------------------------------------------------------------------------------------------------------------")
#     else: 
#         result = compose_file_process(filePath, fileHash)
# # #TODO: dont touch code above.


















# classify_categories_with_gpt ================================================
    # start_date = datetime(2025, 3, 26)
    # end_date = datetime(2025, 3, 28) # up to 28.03.2025 00:00:00

    # compose_document_update(start_date, end_date)
#================================================
#-----TEST_CREATION-OF-CATEGORIES-IN-DB----------------------------------
    # list_of_created_cat = create_category_collection_in_db(CATEGORIES_COLLECTION, categories_for_db)
    # print("---printing list_of_created_cat ------------------------------")
    # for locc in list_of_created_cat:
    #     print(locc)
    # print("-------------------------------------------------")
    # list_of_categories = get_list_of_categories_from_db(CATEGORIES_COLLECTION)
    # print("---printing list_of_categories ------------------------------")
    # for loc in list_of_categories:
    #     print(loc)
    # print("-------------------------------------------------")
    # if need to add new category to db, use create_category_collection_in_db() and give it new category in list. example: create_category_collection_in_db(CATEGORIES_COLLECTION ,['Криптовалюта'])
    
    


    # gpt_category = get_category_from_gpt_with_repetition(TEXT_D_f)
    # print(f"------------------------gpt_category: ")
    # print(gpt_category)
    # print("--------------------------------------")












    pass



