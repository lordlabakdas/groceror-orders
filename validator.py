from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel


class Order(BaseModel):
    schema_version: str = "1.0"
    order_id: UUID
    order_date: datetime
    items: List[str]
    event: str
    total_price: float
    status: str
    user_id: UUID
