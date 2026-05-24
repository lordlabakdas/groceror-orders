import logging

import metrics  # noqa: F401 - imported to register prometheus metrics
from fastapi import FastAPI, HTTPException, Query
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from analytics.order_analytics import OrderAnalytics
from analytics.order_per_day_analytics import OrderPerDayAnalytics
from db import DB

logger = logging.getLogger(__name__)

app = FastAPI(title="groceror-orders analytics", version="1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def _analytics():
    db = DB()
    return db, OrderAnalytics(db), OrderPerDayAnalytics(db)


@app.get("/analytics/most-ordered-items")
def most_ordered_items(limit: int = Query(default=10, ge=1, le=100)):
    db, analytics, _ = _analytics()
    try:
        return {"items": analytics.most_ordered_items(limit)}
    except Exception as exc:
        logger.error("most_ordered_items failed: %s", exc)
        raise HTTPException(status_code=500, detail="Analytics query failed")
    finally:
        db.close()


@app.get("/analytics/revenue-by-item")
def revenue_by_item(limit: int = Query(default=10, ge=1, le=100)):
    db, analytics, _ = _analytics()
    try:
        return {"items": analytics.revenue_by_item(limit)}
    except Exception as exc:
        logger.error("revenue_by_item failed: %s", exc)
        raise HTTPException(status_code=500, detail="Analytics query failed")
    finally:
        db.close()


@app.get("/analytics/orders-per-day")
def orders_per_day(limit: int = Query(default=30, ge=1, le=365)):
    db, _, per_day = _analytics()
    try:
        return {"days": per_day.orders_per_day(limit)}
    except Exception as exc:
        logger.error("orders_per_day failed: %s", exc)
        raise HTTPException(status_code=500, detail="Analytics query failed")
    finally:
        db.close()


@app.get("/analytics/summary")
def summary():
    db, analytics, _ = _analytics()
    try:
        return {
            "total_revenue": analytics.total_revenue(),
            "order_count": analytics.order_count(),
        }
    except Exception as exc:
        logger.error("summary failed: %s", exc)
        raise HTTPException(status_code=500, detail="Analytics query failed")
    finally:
        db.close()
