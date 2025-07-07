from typing import List

from db import DB


class OrderAnalytics:

    def most_selling_item(orders: List):
        pipeline = [
            {"$unwind": "$items"},  # Flatten the items array
            {"$group": {"_id": "$items", "total_price": {"$sum": "total_price"}}},
            {"$sort": {"total_price": -1}},  # Sort descending
            {"$limit": 1},  # Get top item only
        ]

        result = list(orders.aggregate(pipeline))
        print(result)
        if result:
            print("Top selling item:", result[0]["_id"])
            print("Total price:", result[0]["total_price"])
        else:
            print("No data found.")

    def least_selling_item(orders: List):
        pipeline = [
            {"$unwind": "$items"},  # Flatten the items array
            {
                "$group": {
                    "_id": "$items.product_id",
                    "total_price": {"$sum": "$items.price"},
                }
            },
            {"$sort": {"total_price": 1}},  # Sort ascending
            {"$limit": 1},  # Get top item only
        ]

        result = list(orders.aggregate(pipeline))

        if result:
            print("Least selling item:", result[0]["_id"])
            print("Total price:", result[0]["total_price"])
        else:
            print("No data found.")
