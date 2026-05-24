import logging
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient

import config

load_dotenv()

log = logging.getLogger(__name__)


class DB:
    def __init__(self):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client["orders"]

    def upsert_order(self, data: dict):
        """Idempotent upsert — keyed on order_id to survive redelivery."""
        collection = self.db["client_orders"]
        order_id = str(data.get("order_id"))
        # Convert UUID/datetime objects to JSON-safe types
        safe_data = _make_serializable(data)
        result = collection.update_one(
            {"order_id": order_id},
            {"$setOnInsert": safe_data},
            upsert=True,
        )
        if result.upserted_id:
            log.info("Inserted new order order_id=%s", order_id)
        else:
            log.info("Duplicate order_id=%s — skipped", order_id)

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


def _make_serializable(obj):
    """Recursively convert UUID/datetime to str for MongoDB storage."""
    import uuid
    from datetime import datetime
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(i) for i in obj]
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj
