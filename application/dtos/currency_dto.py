from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal


class CurrencyCreateDTO(BaseModel):
    id: int
    name: str
    symbol: str

class CurrencyOutDTO(BaseModel):
    id: int
    name: str
    symbol: str

class CurrencyListDTO(BaseModel):
    currencies: List[CurrencyOutDTO]
