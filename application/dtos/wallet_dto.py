from pydantic import BaseModel
from typing import List
from decimal import Decimal

class WalletCreateDTO(BaseModel):
    balance: Decimal
    currency_id: int
    user_id: int

class WalletOutDTO(BaseModel):
    id: int
    balance: Decimal
    currency_id: int

class WalletListDTO(BaseModel):
    wallets: List[WalletOutDTO]
