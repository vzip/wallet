from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import uuid


class TransactionCreateDTO(BaseModel):
    wallet_id: uuid.UUID
    amount: Decimal
    type: str  # "debit" or "credit"

class TransactionOutDTO(TransactionCreateDTO):
    id: uuid.UUID
    from_wallet_id: Optional[uuid.UUID] = Field(None, allow_none=True)
    from_currency_id: Optional[int] = Field(None, allow_none=True)
    amount: Decimal
    to_wallet_id: Optional[uuid.UUID] = Field(None, allow_none=True)
    to_currency_id: Optional[int] = Field(None, allow_none=True)
    rate: Optional[Decimal]= Field(None, allow_none=True)
    converted_amount: Optional[Decimal] = Field(None, allow_none=True)
    type: str
    status: Optional[str] = Field(None, allow_none=True)
    timestamp: datetime
    user_id: uuid.UUID
    wallet_id: Optional[uuid.UUID] = Field(None, allow_none=True)

    class Config:
        orm_mode = True
        json_encoders = {Decimal: lambda v: str(v)}

class TransactionListDTO(BaseModel):
    transactions: List[TransactionOutDTO]
