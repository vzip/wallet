from pydantic import BaseModel
from typing import List

class WalletCreateDTO(BaseModel):
    name: str
    balance: float

class WalletOutDTO(WalletCreateDTO):
    id: int
    balance: float
    currency_id: int

class WalletListDTO(BaseModel):
    wallets: List[WalletOutDTO]
