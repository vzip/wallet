from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import Wallet
from application.dtos.wallet_dto import WalletListDTO, WalletOutDTO
from domain.repositories.wallet_repository import WalletRepository

async def create_wallet(session: AsyncSession, user_id: int, balance: float, currency_id: int):
    new_wallet = Wallet(user_id=user_id, balance=balance, currency_id=currency_id)
    session.add(new_wallet)
    await session.commit()

async def get_wallet_by_user_id(session: AsyncSession, user_id: int):
    stmt = select(Wallet).where(Wallet.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()

# Get user wallets
def to_wallet_out_dto(wallet):
    return WalletOutDTO(
        id=wallet.id,
        balance=wallet.balance,
        currency_id=wallet.currency_id
    )

async def get_user_wallets(session: AsyncSession, user_id: int):
    wallet_repo = WalletRepository(session)
    wallets = await wallet_repo.get_user_wallets(user_id)
    
    if not wallets:
        return None
    
    wallet_dtos = [to_wallet_out_dto(wallet) for wallet in wallets]
    return WalletListDTO(wallets=wallet_dtos)

# ... More methods for updating wallet, deleting wallet, etc.
