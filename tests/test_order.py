import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from order import Order


def make_valid_body(**overrides):
    payload = {
        "order_id": str(uuid.uuid4()),
        "order_date": datetime.utcnow().isoformat(),
        "items": ["apple", "banana"],
        "event": "order_created",
        "total_price": 9.99,
        "status": "pending",
        "user_id": str(uuid.uuid4()),
    }
    payload.update(overrides)
    return json.dumps(payload).encode()


def make_method(redelivered=False):
    method = MagicMock()
    method.delivery_tag = 1
    method.redelivered = redelivered
    return method


def make_channel():
    return MagicMock()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_valid_message_acks_and_records_event():
    ch = make_channel()
    method = make_method()
    body = make_valid_body()

    with patch("order.DB") as MockDB, \
         patch("order.metrics") as mock_metrics:
        mock_db_instance = MagicMock()
        MockDB.return_value = mock_db_instance

        Order.save_order_info(ch, method, None, body)

        mock_db_instance.upsert_order.assert_called_once()
        ch.basic_ack.assert_called_once_with(delivery_tag=method.delivery_tag)
        mock_metrics.increment_event.assert_called_once_with("order_created")
        mock_metrics.increment_error.assert_not_called()


# ---------------------------------------------------------------------------
# Invalid JSON
# ---------------------------------------------------------------------------

def test_invalid_json_nacks_without_requeue():
    ch = make_channel()
    method = make_method()
    body = b"not valid json{"

    with patch("order.metrics") as mock_metrics:
        Order.save_order_info(ch, method, None, body)

        ch.basic_nack.assert_called_once_with(delivery_tag=method.delivery_tag, requeue=False)
        ch.basic_ack.assert_not_called()
        mock_metrics.increment_error.assert_called_once_with("unknown", "validation")


# ---------------------------------------------------------------------------
# Validation error
# ---------------------------------------------------------------------------

def test_validation_error_nacks_without_requeue():
    ch = make_channel()
    method = make_method()
    # Missing required fields
    body = json.dumps({"event": "order_created"}).encode()

    with patch("order.metrics") as mock_metrics:
        Order.save_order_info(ch, method, None, body)

        ch.basic_nack.assert_called_once_with(delivery_tag=method.delivery_tag, requeue=False)
        ch.basic_ack.assert_not_called()
        mock_metrics.increment_error.assert_called_once_with("unknown", "validation")


# ---------------------------------------------------------------------------
# DB failure — first delivery (requeue=True)
# ---------------------------------------------------------------------------

def test_db_failure_first_delivery_requeues():
    ch = make_channel()
    method = make_method(redelivered=False)
    body = make_valid_body()

    with patch("order.DB") as MockDB, \
         patch("order.metrics") as mock_metrics:
        mock_db_instance = MagicMock()
        mock_db_instance.upsert_order.side_effect = Exception("connection refused")
        MockDB.return_value = mock_db_instance

        Order.save_order_info(ch, method, None, body)

        ch.basic_nack.assert_called_once_with(delivery_tag=method.delivery_tag, requeue=True)
        ch.basic_ack.assert_not_called()
        mock_metrics.increment_error.assert_called_once_with("order_created", "db")


# ---------------------------------------------------------------------------
# DB failure — second delivery (redelivered=True, requeue=False)
# ---------------------------------------------------------------------------

def test_db_failure_second_delivery_sends_to_dlq():
    ch = make_channel()
    method = make_method(redelivered=True)
    body = make_valid_body()

    with patch("order.DB") as MockDB, \
         patch("order.metrics") as mock_metrics:
        mock_db_instance = MagicMock()
        mock_db_instance.upsert_order.side_effect = Exception("timeout")
        MockDB.return_value = mock_db_instance

        Order.save_order_info(ch, method, None, body)

        ch.basic_nack.assert_called_once_with(delivery_tag=method.delivery_tag, requeue=False)
        ch.basic_ack.assert_not_called()
        mock_metrics.increment_error.assert_called_once_with("order_created", "db")
