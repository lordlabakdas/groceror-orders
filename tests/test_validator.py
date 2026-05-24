import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from validator import Order


def make_valid_payload(**overrides):
    base = {
        "order_id": str(uuid.uuid4()),
        "order_date": datetime.utcnow().isoformat(),
        "items": ["apple", "banana"],
        "event": "order_created",
        "total_price": 9.99,
        "status": "pending",
        "user_id": str(uuid.uuid4()),
    }
    base.update(overrides)
    return base


def test_valid_order_parses_correctly():
    payload = make_valid_payload()
    order = Order(**payload)
    assert str(order.order_id) == payload["order_id"]
    assert order.event == "order_created"
    assert order.total_price == 9.99
    assert order.status == "pending"
    assert len(order.items) == 2


def test_default_schema_version():
    order = Order(**make_valid_payload())
    assert order.schema_version == "1.0"


def test_schema_version_can_be_overridden():
    order = Order(**make_valid_payload(schema_version="2.0"))
    assert order.schema_version == "2.0"


def test_missing_order_id_raises():
    payload = make_valid_payload()
    del payload["order_id"]
    with pytest.raises(ValidationError):
        Order(**payload)


def test_missing_order_date_raises():
    payload = make_valid_payload()
    del payload["order_date"]
    with pytest.raises(ValidationError):
        Order(**payload)


def test_missing_items_raises():
    payload = make_valid_payload()
    del payload["items"]
    with pytest.raises(ValidationError):
        Order(**payload)


def test_missing_event_raises():
    payload = make_valid_payload()
    del payload["event"]
    with pytest.raises(ValidationError):
        Order(**payload)


def test_missing_total_price_raises():
    payload = make_valid_payload()
    del payload["total_price"]
    with pytest.raises(ValidationError):
        Order(**payload)


def test_missing_status_raises():
    payload = make_valid_payload()
    del payload["status"]
    with pytest.raises(ValidationError):
        Order(**payload)


def test_missing_user_id_raises():
    payload = make_valid_payload()
    del payload["user_id"]
    with pytest.raises(ValidationError):
        Order(**payload)


def test_invalid_uuid_raises():
    payload = make_valid_payload(order_id="not-a-uuid")
    with pytest.raises(ValidationError):
        Order(**payload)


def test_invalid_total_price_type_raises():
    payload = make_valid_payload(total_price="free")
    with pytest.raises(ValidationError):
        Order(**payload)


def test_items_is_list():
    order = Order(**make_valid_payload(items=["milk", "eggs", "bread"]))
    assert isinstance(order.items, list)
    assert "milk" in order.items
