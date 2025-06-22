

from db import DB

from validator import Order as OrderModel

class Order(object):
    def __init__(self):
        self.db = DB()
    
    
    def save_order_info(self, order: OrderModel):
        print(order)
        self.db.save_to_mongodb(order.dict(), "client_orders")
        
    
        