from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal

class WalletCreateDTO(BaseModel):
    balance: Decimal
    currency_id: int
    user_id: int

class WalletOutDTO(BaseModel):
    id: int
    balance: Decimal
    reserved_balance: Decimal
    currency_id: int
    user_id: int

    class Config:
        json_encoders = {Decimal: lambda v: str(v)}

class WalletListDTO(BaseModel):
    wallets: List[WalletOutDTO]
