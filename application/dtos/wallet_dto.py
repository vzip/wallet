from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal
import uuid

class WalletCreateDTO(BaseModel):
    balance: Decimal
    currency_id: int
    reserved_balance: Decimal
    user_id: uuid.UUID

class WalletOutDTO(BaseModel):
    id: uuid.UUID
    balance: Decimal
    reserved_balance: Decimal
    currency_id: int
    user_id: uuid.UUID

    class Config:
        json_encoders = {Decimal: lambda v: str(v)}

class WalletListDTO(BaseModel):
    wallets: List[WalletOutDTO]
    
    class Config:
        json_encoders = {Decimal: lambda v: str(v)}