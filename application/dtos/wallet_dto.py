from pydantic import BaseModel
from typing import List
from decimal import Decimal

class WalletCreateDTO(BaseModel):
    name: str
    balance: Decimal

class WalletOutDTO(WalletCreateDTO):
    id: int
    balance: Decimal
    currency_id: int

class WalletListDTO(BaseModel):
    wallets: List[WalletOutDTO]
