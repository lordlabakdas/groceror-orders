import json
import logging

from pydantic import ValidationError

import metrics
from db import DB
from validator import Order as OrderModel

logger = logging.getLogger(__name__)


class Order(object):
    def __init__(self):
        pass

    @staticmethod
    def save_order_info(ch, method, properties, body: bytes):
        # --- Deserialise -------------------------------------------------
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON — rejecting without requeue: %s", exc)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            metrics.increment_error("unknown", "validation")
            return

        # --- Validate ----------------------------------------------------
        try:
            order = OrderModel(**payload)
        except ValidationError as exc:
            logger.error("Validation error — rejecting without requeue: %s", exc)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            metrics.increment_error("unknown", "validation")
            return

        # --- Persist -----------------------------------------------------
        db = DB()
        try:
            db.upsert_order(order.model_dump())
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Saved order_id=%s", order.order_id)
            metrics.increment_event(order.event)
        except Exception as exc:
            requeue = not method.redelivered
            logger.error(
                "MongoDB error for order_id=%s: %s — %s",
                order.order_id,
                exc,
                "requeueing" if requeue else "sending to DLQ",
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=requeue)
            metrics.increment_error(order.event, "db")
        finally:
            db.close()
