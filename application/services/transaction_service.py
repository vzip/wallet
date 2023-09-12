from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import Wallet, Transaction, ExchangeRate
from application.dtos.wallet_dto import WalletOutDTO
from application.dtos.transaction_dto import TransactionOutDTO, TransactionListDTO, PendingTransactionOutDTO
from domain.repositories.transaction_repository import create_pending_deposit, transfer_transaction, get_all_transactions, get_transactions_by_wallet_id
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

async def deposit_funds(session: AsyncSession, wallet_id: uuid.UUID, amount: Decimal, user_id, service_user_id):
    pending_transaction = await create_pending_deposit(session, wallet_id, amount, user_id, service_user_id)
    logging.info(f"pending_transaction in service: {pending_transaction.id}")
    if not pending_transaction:
        return None
    return PendingTransactionOutDTO(
        id=pending_transaction.id,
        from_wallet_id=pending_transaction.from_wallet_id,
        from_currency_id=pending_transaction.from_currency_id,
        amount=pending_transaction.amount,
        to_wallet_id=pending_transaction.to_wallet_id,
        to_currency_id=pending_transaction.to_currency_id,
        rate=pending_transaction.rate,
        converted_amount=pending_transaction.converted_amount,
        type=pending_transaction.type,
        status=pending_transaction.status,
        timestamp=pending_transaction.timestamp,
        user_id=pending_transaction.user_id,
        external_wallet_id=pending_transaction.external_wallet_id,
        external_transaction_id=pending_transaction.external_transaction_id
        
    )

async def get_all_user_transactions(session: AsyncSession, user_id):
    transactions = await get_all_transactions(session, user_id)
    logging.info(f"User ID in transaction service: {user_id}")
    if not transactions:
        return None
    return transactions 

async def get_user_transactions_by_wallet_id(session: AsyncSession, wallet_id, user_id):
    transactions = await get_transactions_by_wallet_id(session, wallet_id, user_id)
    logging.info(f"User ID in transaction service: {user_id}")
    if not transactions:
        return None
    return transactions 

    
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


