from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal


class RateCreateDTO(BaseModel):
    id: int
    from_currency_id: int
    to_currency_id: int
    rate: Decimal
    reverse_rate: Decimal


class RateOutDTO(BaseModel):
    id: int
    from_currency_id: int
    to_currency_id: int
    rate: Decimal
    reverse_rate: Decimal

    class Config:
        json_encoders = {Decimal: lambda v: str(v)}

class RateListDTO(BaseModel):
    rates: List[RateOutDTO]
