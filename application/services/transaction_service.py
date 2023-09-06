from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import Wallet, Transaction, ExchangeRate
from application.dtos.wallet_dto import WalletOutDTO
from application.dtos.transaction_dto import TransactionOutDTO, TransactionListDTO
from domain.repositories.transaction_repository import deposit_transaction, convert_currency, transfer_transaction, get_all_transactions, get_transactions_by_wallet_id
from sqlalchemy import update
from decimal import Decimal
from pydantic import parse_obj_as
from typing import List
from sqlalchemy import exc as sa_exc
import uuid
import logging
logging.basicConfig(level=logging.INFO)


async def transfer_funds_with_convertation(session: AsyncSession, amount: Decimal, from_wallet_id: uuid.UUID, to_wallet_id: uuid.UUID, user_id: uuid.UUID):
    transaction_res = await transfer_transaction(session, amount, from_wallet_id, to_wallet_id, user_id)
    logging.info(f"Exchange results in exchange service: {amount}")
    if not transaction_res:
        return None
    return transaction_res

async def deposit_funds(session: AsyncSession, wallet_id: uuid.UUID, amount: Decimal, user_id):
    wallet = await deposit_transaction(session, wallet_id, amount, user_id)
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

async def get_all_user_transactions(session: AsyncSession, user_id):
    transactions = await get_all_transactions(session, user_id)
    logging.info(f"User ID in transaction service: {user_id}")
    if not transactions:
        return None
    # Преобразование объектов SQLAlchemy в словари 
    transaction_dicts = [
        {key: value for key, value in transaction.__dict__.items() if not key.startswith('_sa_')}
        for transaction in transactions
    ]
    logging.info(f"Tansaction Dicts in transaction service: {transaction_dicts}")
    
    try:
        # Преобразование словарей в объекты TransactionOutDTO
        # transaction_dtos = parse_obj_as(List[TransactionOutDTO], transaction_dicts)
        # Преобразование объектов SQLAlchemy в объекты Pydantic
        transaction_dtos = []
        for transaction in transactions:
            dto = TransactionOutDTO.from_orm(transaction)
            dto_dict = dto.dict(exclude={'wallet_id'})
            transaction_dtos.append(TransactionOutDTO(**dto_dict))  
    except Exception as e:
        print(f"Error during parsing: {e}")
    return TransactionListDTO(transactions=transaction_dtos)

async def get_user_transactions_by_wallet_id(session: AsyncSession, wallet_id, user_id):
    transactions = await get_transactions_by_wallet_id(session, wallet_id, user_id)
    logging.info(f"User ID in transaction service: {user_id}")
    if not transactions:
        return None
    # Преобразование объектов SQLAlchemy в словари 
    transaction_dicts = [
        {key: value for key, value in transaction.__dict__.items() if not key.startswith('_sa_')}
        for transaction in transactions
    ]
    logging.info(f"Tansaction Dicts in transaction service: {transaction_dicts}")
    
    try:
        # Преобразование словарей в объекты TransactionOutDTO
        transaction_dtos = parse_obj_as(List[TransactionOutDTO], transaction_dicts)   
    except Exception as e:
        print(f"Error during parsing: {e}")
    return TransactionListDTO(transactions=transaction_dtos)

    
async def withdraw_funds(session: AsyncSession, wallet_id: uuid.UUID, amount: Decimal):
    try:
        stmt = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        result = await session.execute(stmt)
        wallet = result.scalar_one()

        if wallet.balance < amount:
            return {"status": "insufficient_funds"}
            
        wallet.balance -= amount

        new_transaction = Transaction(
            amount=amount,
            from_wallet_id=wallet.id,
            to_wallet_id=None,
            type="withdraw"
        )

        session.add(new_transaction)
        await session.commit()

        return {"status": "success"}
    
    except sa_exc.SQLAlchemyError:
        await session.rollback()
        return {"status": "database_error"}


async def reserve_funds(session: AsyncSession, wallet_id: uuid.UUID, amount: Decimal):
    try:
        stmt = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        result = await session.execute(stmt)
        wallet = result.scalar_one()

        if wallet.balance < amount:
            return {"status": "insufficient_funds"}
            
        wallet.balance -= amount
        wallet.reserved_balance += amount

        new_transaction = Transaction(
            amount=amount,
            from_wallet_id=wallet.id,
            to_wallet_id=None,
            type="reserve"
        )

        session.add(new_transaction)
        await session.commit()

        return {"status": "success"}
    
    except sa_exc.SQLAlchemyError:
        await session.rollback()
        return {"status": "database_error"}


async def release_reserved_funds(session: AsyncSession, wallet_id: uuid.UUID, amount: Decimal):
    try:
        stmt = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        result = await session.execute(stmt)
        wallet = result.scalar_one()

        if wallet.reserved_balance < amount:
            return {"status": "insufficient_reserved_funds"}
            
        wallet.reserved_balance -= amount

        new_transaction = Transaction(
            amount=amount,
            from_wallet_id=None,
            to_wallet_id=wallet.id,
            type="release"
        )

        session.add(new_transaction)
        await session.commit()

        return {"status": "success"}
    
    except sa_exc.SQLAlchemyError:
        await session.rollback()
        return {"status": "database_error"}


