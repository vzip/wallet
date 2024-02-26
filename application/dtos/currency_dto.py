from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class CurrencyCreateDTO(BaseModel):
    name: str
    symbol: str 
    # code: str 

class CurrencyOutDTO(BaseModel):
    id: int
    name: str
    symbol: str 
    # code: str 

class CurrencyListDTO(BaseModel):
    currencies: List[CurrencyOutDTO]
