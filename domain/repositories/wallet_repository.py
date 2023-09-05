from sqlalchemy.ext.asyncio import AsyncSession
from domain.models import Wallet
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, and_
import logging
logging.basicConfig(level=logging.INFO)

class WalletRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create_wallet(self, wallet: Wallet):
        self.session.add(wallet)
        await self.session.commit()
        
async def get_wallet_by_id(session, wallet_id: int, user_id: int):
    try:
        logging.info(f"Wallet Id in wallet repository: {wallet_id}, User Id: {user_id}")
        stmt = select(Wallet).where(
            and_(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id
            )
        )
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()
        return wallet
    except SQLAlchemyError as e:
            raise e  # 

    
async def get_user_wallets(session, user_id: int):
    try:
        logging.info(f"User_id in wallet rerository: {user_id}")
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        result = await session.execute(stmt)
        wallets = result.scalars().all()
        logging.info(f"Wallets in rerository: {wallets}")
        return wallets if wallets else []      
    except SQLAlchemyError as e:
            raise e  # 
        