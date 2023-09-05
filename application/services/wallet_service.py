from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import Wallet
from application.dtos.wallet_dto import WalletListDTO, WalletOutDTO, WalletCreateDTO
from domain.repositories.wallet_repository import get_user_wallets, get_wallet_by_id
from decimal import Decimal
from pydantic import parse_obj_as
from typing import List
import logging
logging.basicConfig(level=logging.INFO)

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

async def get_wallet_by_wallet_id(session: AsyncSession, wallet_id: int, user_id: int):
    wallet = await get_wallet_by_id(session, wallet_id, user_id)
    logging.info(f"Wallet in service: {wallet}")
    if not wallet:
        return None
    return WalletOutDTO(
        id=wallet.id,
        balance=wallet.balance,
        reserved_balance=wallet.reserved_balance,
        currency_id=wallet.currency_id,
        user_id=wallet.user_id,
    )


async def get_wallets_by_user_id(session: AsyncSession, user_id: int):
    
    wallets = await get_user_wallets(session, user_id)
    logging.info(f"Wallets in service: {wallets}")
    if not wallets:
        return None
    # Преобразование объектов SQLAlchemy в словари 
    wallet_dicts = [{key: value for key, value in wallet.__dict__.items() if not key.startswith('_sa_')} for wallet in wallets]

    # Преобразование словарей в объекты WalletOutDTO
    wallet_dtos = parse_obj_as(List[WalletOutDTO], wallet_dicts)

    return WalletListDTO(wallets=wallet_dtos)

# ... More methods for updating wallet, deleting wallet, etc.
