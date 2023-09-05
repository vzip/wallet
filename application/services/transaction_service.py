from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import Wallet, Transaction, ExchangeRate
from application.dtos.wallet_dto import WalletOutDTO
from domain.repositories.transaction_repository import deposit_transaction, convert_currency, transfer_transaction
from sqlalchemy import update
from decimal import Decimal
from sqlalchemy import exc as sa_exc
import logging
logging.basicConfig(level=logging.INFO)


async def transfer_funds_with_convertation(session: AsyncSession, from_wallet_id: int, to_wallet_id: int, amount: Decimal, user_id):
    transaction_res = await transfer_transaction(session, amount, from_wallet_id, to_wallet_id)
    logging.info(f"Exchange results in exchange service: {amount}")
    if not transaction_res:
        return None
    return transaction_res

async def deposit_funds(session: AsyncSession, wallet_id: int, amount: Decimal, user_id):
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


    
async def withdraw_funds(session: AsyncSession, wallet_id: int, amount: Decimal):
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


async def reserve_funds(session: AsyncSession, wallet_id: int, amount: Decimal):
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


async def release_reserved_funds(session: AsyncSession, wallet_id: int, amount: Decimal):
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


