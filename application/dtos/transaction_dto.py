from pydantic import BaseModel
from typing import List
from decimal import Decimal
class TransactionCreateDTO(BaseModel):
    wallet_id: int
    amount: Decimal
    type: str  # "debit" or "credit"

class TransactionOutDTO(TransactionCreateDTO):
    id: int
    user_id: int

class TransactionListDTO(BaseModel):
    transactions: List[TransactionOutDTO]
