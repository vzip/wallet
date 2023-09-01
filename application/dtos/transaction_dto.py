from pydantic import BaseModel
from typing import List

class TransactionCreateDTO(BaseModel):
    wallet_id: int
    amount: float
    type: str  # "debit" or "credit"

class TransactionOutDTO(TransactionCreateDTO):
    id: int
    user_id: int

class TransactionListDTO(BaseModel):
    transactions: List[TransactionOutDTO]
