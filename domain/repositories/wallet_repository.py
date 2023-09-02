from sqlalchemy.ext.asyncio import AsyncSession
from domain.models import Wallet
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

class WalletRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create_wallet(self, wallet: Wallet):
        self.session.add(wallet)
        await self.session.commit()
        
    async def get_wallet_by_id(self, wallet_id: int):
        return await self.session.query(Wallet).filter(Wallet.id == wallet_id).first()

    async def get_user_wallets(self, user_id: int):
        return await self.session.query(Wallet).filter(Wallet.user_id == user_id).all()
    
    async def get_user_wallets(self, user_id: str):
        try:
            stmt = select(Wallet).where(Wallet.user_id == user_id)
            result = await self.session.execute(stmt)
            wallet = result.scalar_one_or_none()
            return wallet        
        except SQLAlchemyError as e:
                raise e  # 
        