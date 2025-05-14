import logging
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

class MongoDBHandler:
    def __init__(self, uri='mongodb://localhost:27017/', db_name='collection'):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def get_collection(self, collection_name):
        return self.db[collection_name]
    
    def insert_document(self, collection_name, document):
        collection = self.get_collection(collection_name)
        return collection.insert_one(document).inserted_id
    
    def find_document(self, collection_name, query):
        collection = self.get_collection(collection_name)
        return collection.find_one(query)
    
    def find_document_by_id(self, collection_name, document_id):
        collection = self.get_collection(collection_name)
        try:
            document = collection.find_one({'_id': ObjectId(document_id)})
        except Exception as e:
            print(f"Error converting to ObjectId: {e}")
            print(f"Error -> mongodb_handler -> find_document_by_id()")
            logging.info(f"Error converting to ObjectId: {e}")
            logging.info(f"Error -> mongodb_handler -> find_document_by_id()")
            return None
        return document
    
    def find_documents(self, collection_name, query):
        collection = self.get_collection(collection_name)
        # results = collection.find(query)
        # result_list = [x for x in results]
        # return result_list
        return collection.find(query)



    def check_if_collection_exist(self, collection):
        collections = self.db.list_collection_names()
        if collection in collections:
            return True
        return False



    def find_documents_by_date(self, collection_name, start_date, end_date, query={}):
        # print(f"--> class MongoDBHandler, find_documents_by_date() -->")
        # print(f"C: {collection_name}, SD: {start_date}, ED: {end_date}, Q: {query}")
        logging.info(f"--> class MongoDBHandler, find_documents_by_date() -->")
        logging.info(f"C: {collection_name}, SD: {start_date}, ED: {end_date}, Q: {query}")
        collection = self.get_collection(collection_name)
        date_query = {
            'timestamp': {
                '$gte': start_date,
                '$lte': end_date
            },
        }
        full_query = {**date_query, **query}
        return collection.find(full_query)







    def update_document(self, collection_name, query, update_values):
        collection = self.get_collection(collection_name)
        return collection.update_one(query, {"$set": update_values})

    def update_document_by_id(self, collection_name, document_id, update_values):
        collection = self.get_collection(collection_name)
        try:
            # document = collection.update_one({"_id": ObjectId(document_id)}, {"$set": update_values})
            document = collection.update_one({"_id": document_id}, {"$set": update_values})
        except Exception as e:
            print(f"Error converting to ObjectId: {e}")
            print(f"Error -> mongodb_handler -> update_document_by_id()")
            logging.info(f"Error converting to ObjectId: {e}")
            logging.info(f"Error -> mongodb_handler -> update_document_by_id()")

            return None
        return document
    
    def delete_document(self, collection_name, query):
        collection = self.get_collection(collection_name)
        return collection.delete_one(query)
    
    def delete_document_by_id(self, collection_name, document_id):
        collection = self.get_collection(collection_name)
        try:
            document = collection.delete_one({'_id': ObjectId(document_id)})
        except Exception as e:
            print(f"Error converting to ObjectId: {e}")
            print(f"Error -> mongodb_handler -> delete_document_by_id()")
            logging.info(f"Error converting to ObjectId: {e}")
            logging.info(f"Error -> mongodb_handler -> delete_document_by_id()")
            return None
        return document
    
    def delete_documents(self, collection_name, query):
        collection = self.get_collection(collection_name)
        return collection.delete_many(query)

    def close_connection(self):
        self.client.close()

    # def get_document_template(file_path, transcription, category_from_list, category_proposition, timestamp):
    def get_document_template(self, hash_id, file_name, transcription, category_from_list, category_proposition):
        document = {
            # "recording_id": "unique_identifier",
            "_id": hash_id,
            "file_name": file_name,
            "transcription": transcription,
            "category": category_from_list,
            "potential_new_category": category_proposition,
            "timestamp": datetime.now(),
        }
        return document