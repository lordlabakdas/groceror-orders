import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

log = logging.getLogger(__name__)


class DB:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["orders"]

    def save_to_mongodb(self, data, collection_name):
        collection = self.db[collection_name]
        if isinstance(data, list):
            today = datetime.utcnow().isoformat()
            result = collection.insert_one({"uploaded_date": today, "data": data})
            log.info(f"Inserted 1 document into {collection_name}")
        elif isinstance(data, dict):
            result = collection.insert_one(data)
            log.info(
                f"Inserted 1 document into {collection_name} with id {result.inserted_id}"
            )
        else:
            log.error(f"Unsupported data type for {collection_name}")

    def close(self):
        self.client.close()

    def get_collection(self, collection_name):
        return self.db[collection_name]
