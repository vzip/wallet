from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import Wallet
from application.dtos.wallet_dto import WalletListDTO, WalletOutDTO, WalletCreateDTO
from domain.repositories.wallet_repository import WalletRepository
from decimal import Decimal

async def create_wallet(session: AsyncSession, new_wallet: WalletCreateDTO):
    new_wallet = Wallet(user_id=new_wallet.user_id, balance=new_wallet.balance, currency_id=new_wallet.currency_id)
    session.add(new_wallet)
    await session.flush() 
    await session.commit()
    return WalletOutDTO(
        id=new_wallet.id,
        balance=new_wallet.balance,
        currency_id=new_wallet.currency_id
    )

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

async def get_wallets_by_user_id(session: AsyncSession, user_id: int):
    wallet_repo = WalletRepository(session)
    wallets = await wallet_repo.get_user_wallets(user_id)
    
    if not wallets:
        return None
    
    wallet_dtos = [to_wallet_out_dto(wallet) for wallet in wallets]
    return WalletListDTO(wallets=wallet_dtos)

# ... More methods for updating wallet, deleting wallet, etc.
