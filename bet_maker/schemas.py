import datetime
import decimal
import enum
from typing import Optional

from pydantic import BaseModel, ValidationError, field_validator


class Bet(BaseModel):
    event_id: str
    amount: float

    @field_validator('amount')
    def amount_validator(cls, v):
        if v < 0:
            raise ValidationError
        else:
            return round(v, 2)

    class Config:
        from_attributes=True


class EventState(enum.Enum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class Event(BaseModel):
    event_id: str
    coefficient: Optional[decimal.Decimal] = None
    deadline: Optional[int] = None
    state: Optional[EventState] = None

    class Config:
        from_attributes=True