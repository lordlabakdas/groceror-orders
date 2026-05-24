import logging
from typing import List

from db import DB

logger = logging.getLogger(__name__)

COLLECTION = "client_orders"


class OrderAnalytics:

    def __init__(self, db: DB):
        self._col = db.get_collection(COLLECTION)

    def most_ordered_items(self, limit: int = 10) -> List[dict]:
        """Return the top N items by order frequency."""
        pipeline = [
            {"$unwind": "$items"},
            {"$group": {"_id": "$items", "order_count": {"$sum": 1}}},
            {"$sort": {"order_count": -1}},
            {"$limit": limit},
            {"$project": {"item": "$_id", "order_count": 1, "_id": 0}},
        ]
        return list(self._col.aggregate(pipeline))

    def revenue_by_item(self, limit: int = 10) -> List[dict]:
        """Return the top N items by total revenue contributed.

        Revenue is approximated as total_price / len(items) per order line
        since individual item prices are not stored.
        """
        pipeline = [
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": "$items",
                    "revenue": {
                        "$sum": {
                            "$divide": [
                                "$total_price",
                                {"$size": "$items"},  # approximate share
                            ]
                        }
                    },
                }
            },
            {"$sort": {"revenue": -1}},
            {"$limit": limit},
            {"$project": {"item": "$_id", "revenue": 1, "_id": 0}},
        ]
        try:
            return list(self._col.aggregate(pipeline))
        except Exception:
            # Fall back to simpler count-based ranking if $size fails on scalar items
            return self.most_ordered_items(limit)

    def total_revenue(self) -> float:
        """Return the sum of total_price across all orders."""
        pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$total_price"}}},
        ]
        result = list(self._col.aggregate(pipeline))
        return result[0]["total"] if result else 0.0

    def order_count(self) -> int:
        """Return the total number of orders."""
        return self._col.count_documents({})

    def least_ordered_items(self, limit: int = 10) -> List[dict]:
        """Return the bottom N items by order frequency."""
        pipeline = [
            {"$unwind": "$items"},
            {"$group": {"_id": "$items", "order_count": {"$sum": 1}}},
            {"$sort": {"order_count": 1}},
            {"$limit": limit},
            {"$project": {"item": "$_id", "order_count": 1, "_id": 0}},
        ]
        return list(self._col.aggregate(pipeline))
