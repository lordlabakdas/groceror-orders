import logging

from prometheus_client import Counter, Gauge, push_to_gateway, REGISTRY

import config

log = logging.getLogger(__name__)

events_total = Counter(
    "groceror_orders_events_total",
    "Total order events successfully processed",
    ["event_type"],
)
processing_errors_total = Counter(
    "groceror_orders_processing_errors_total",
    "Total order event processing errors",
    ["event_type", "reason"],
)
consumer_up = Gauge(
    "groceror_orders_consumer_up",
    "1 when pika consumer is connected, 0 otherwise",
)


def increment_event(event_type: str) -> None:
    events_total.labels(event_type=event_type).inc()
    _push_if_needed()


def increment_error(event_type: str, reason: str) -> None:
    processing_errors_total.labels(event_type=event_type, reason=reason).inc()
    _push_if_needed()


def set_consumer_up(val: int) -> None:
    consumer_up.set(val)
    _push_if_needed()


def _push_if_needed() -> None:
    if config.METRICS_BACKEND == "pushgateway":
        try:
            push_to_gateway(config.PUSHGATEWAY_URL, job="groceror-orders", registry=REGISTRY)
        except Exception as exc:
            log.warning("Pushgateway push failed: %s", exc)
