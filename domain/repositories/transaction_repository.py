from sqlalchemy.ext.asyncio import AsyncSession
from domain.models import Transaction

class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create_transaction(self, transaction: Transaction):
        self.session.add(transaction)
        await self.session.commit()
        
    async def get_transaction_by_id(self, transaction_id: int):
        return await self.session.query(Transaction).filter(Transaction.id == transaction_id).first()
