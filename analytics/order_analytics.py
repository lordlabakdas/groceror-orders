from typing import List


class OrderAnalytics:
    
    def most_selling_item(orders: List):
        pipeline = [
            {"$unwind": "$items"},  # Flatten the items array
            {"$group": {
                "_id": "$items.product_id",
                "total_quantity": {"$sum": "$items.quantity"}
            }},
            {"$sort": {"total_quantity": -1}},  # Sort descending
        {"$limit": 1}  # Get top item only
        ]

        result = list(orders.aggregate(pipeline))
        
        if result:
            print("Top selling item:", result[0]["_id"])
            print("Quantity sold:", result[0]["total_quantity"])
        else:
            print("No data found.")
    
    def least_selling_item():
        pass
    
    def most_expensive_item_sold():
        pass