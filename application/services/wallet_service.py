from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import Wallet
from application.dtos.wallet_dto import WalletListDTO, WalletOutDTO, WalletCreateDTO, ServiceWalletOutDTO, ServiceWalletListDTO, UserExtWalletCreateDTO
from domain.repositories.wallet_repository import get_user_wallets, get_wallet_by_id, create_new_wallet, create_wallets, create_service_wallets, create_external_wallets, create_new_user_ext_wallet
from decimal import Decimal
from pydantic import parse_obj_as
from typing import List
import uuid
import logging
logging.basicConfig(level=logging.INFO)

async def create_wallet(session: AsyncSession, new_wallet: WalletCreateDTO):
    
    new_wallet = await create_new_wallet(session, new_wallet)
    if not new_wallet:
        return None
    return WalletOutDTO(
        id=new_wallet.id,
        balance=new_wallet.balance,
        currency_id=new_wallet.currency_id,
        reserved_balance=new_wallet.reserved_balance,
        user_id=new_wallet.user_id
    )

async def create_ext_wallet(session: AsyncSession, wallet_name: str, currency_id: int, user_id: uuid.UUID):
    
    new_ext_wallet = await create_new_user_ext_wallet(session, wallet_name, currency_id, user_id)
    if not new_ext_wallet:
        return None
    return new_ext_wallet

async def create_wallets_for_all_currencies(session: AsyncSession, user_id: uuid.UUID):
    new_wallets = await create_wallets(session, user_id)
    if not new_wallets:
        return None    

    return WalletListDTO(wallets=[
        WalletOutDTO(
            id=w.id,
            balance=w.balance,
            reserved_balance=w.reserved_balance,
            currency_id=w.currency_id,
            user_id=w.user_id
        ) for w in new_wallets
    ])

async def create_service_wallets_for_all_currencies(session: AsyncSession, user_id: uuid.UUID):
    new_wallets = await create_service_wallets(session, user_id)
    new_external_wallets = await create_external_wallets(session, user_id)
    if not new_wallets:
        return None    

    return ServiceWalletListDTO(wallets=[
        ServiceWalletOutDTO(
            id=w.id,
            balance=w.balance,
            reserved_balance=w.reserved_balance,
            currency_id=w.currency_id,
            commission_rate=w.commission_rate,
            user_id=w.user_id
        ) for w in new_wallets
    ])


async def get_wallet_by_wallet_id(session: AsyncSession, wallet_id: uuid.UUID, user_id: uuid.UUID):
    wallet = await get_wallet_by_id(session, wallet_id, user_id)
    logging.info(f"Wallet in service: {wallet}")
    if not wallet:
        return None
    return WalletOutDTO(
        id=wallet.id,
        balance=wallet.balance,
        reserved_balance=wallet.reserved_balance,
        currency_id=wallet.currency_id,
        user_id=wallet.user_id
    )


async def get_wallets_by_user_id(session: AsyncSession, user_id: uuid.UUID):
    
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
