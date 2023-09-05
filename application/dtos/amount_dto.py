from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal

class AmountOutDTO(BaseModel):
    from_currency: int
    amount_int: Decimal
    to_currency: int
    rate: Decimal
    amount_ext: Decimal
    
    class Config:
        json_encoders = {Decimal: lambda v: str(v)}
