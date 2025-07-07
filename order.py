import json

from db import DB
from validator import Order as OrderModel


class Order(object):
    def __init__(self):
        pass

    @staticmethod
    def save_order_info(ch, method, properties, body: OrderModel):
        print(body)
        db = DB()
        db.save_to_mongodb(json.loads(body), "client_orders")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        db.close()
