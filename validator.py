from datetime import datetime
from typing import List
from uuid import UUID
from pydantic import BaseModel


class Item(BaseModel):
    item: str
    
class Order(BaseModel):
    order_id: UUID
    order_date: datetime
    items: List[Item]