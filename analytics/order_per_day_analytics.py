import logging
from typing import List

from db import DB

logger = logging.getLogger(__name__)

COLLECTION = "client_orders"


class OrderPerDayAnalytics:

    def __init__(self, db: DB):
        self._col = db.get_collection(COLLECTION)

    def orders_per_day(self, limit: int = 30) -> List[dict]:
        """Return order counts grouped by day, most recent first.

        ``order_date`` is stored as an ISO-8601 string (e.g. "2024-03-15T10:00:00").
        The pipeline converts it to a date and truncates to day granularity.
        """
        pipeline = [
            {
                "$addFields": {
                    "parsed_date": {
                        "$dateFromString": {
                            "dateString": "$order_date",
                            "onError": None,
                            "onNull": None,
                        }
                    }
                }
            },
            {"$match": {"parsed_date": {"$ne": None}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$parsed_date"}
                    },
                    "order_count": {"$sum": 1},
                    "total_revenue": {"$sum": "$total_price"},
                }
            },
            {"$sort": {"_id": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "date": "$_id",
                    "order_count": 1,
                    "total_revenue": 1,
                    "_id": 0,
                }
            },
        ]
        return list(self._col.aggregate(pipeline))
