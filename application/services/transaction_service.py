from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import Wallet, Transaction, ExchangeRate
from sqlalchemy import update
from decimal import Decimal
from sqlalchemy import exc as sa_exc

async def handle_transaction(session: AsyncSession, func, *args, **kwargs):
    try:
        async with session.begin():
            return await func(session, *args, **kwargs)
    except sa_exc.SQLAlchemyError:
        await session.rollback()
        return {"status": "database_error"}

async def transfer_funds(session: AsyncSession, from_wallet_id: int, to_wallet_id: int, amount: Decimal):
    try:
        stmt = select(Wallet).where(Wallet.id == from_wallet_id).with_for_update()
        result = await session.execute(stmt)
        from_wallet = result.scalar_one()

        stmt = select(Wallet).where(Wallet.id == to_wallet_id).with_for_update()
        result = await session.execute(stmt)
        to_wallet = result.scalar_one()

        if from_wallet.balance < amount:
            return {"status": "insufficient_funds"}
        
        if from_wallet.currency_id != to_wallet.currency_id:
            stmt = select(ExchangeRate).\
                where(
                    (ExchangeRate.from_currency_id == from_wallet.currency_id) & 
                    (ExchangeRate.to_currency_id == to_wallet.currency_id)
                )
            result = await session.execute(stmt)
            exchange_rate = result.scalar_one()
            
            if not exchange_rate:
                return {"status": "exchange_rate_not_found"}
            
            amount = amount * exchange_rate.rate
        
        from_wallet.balance -= amount
        to_wallet.balance += amount

        new_transaction = Transaction(
            amount=amount,
            from_wallet_id=from_wallet.id,
            to_wallet_id=to_wallet.id,
            type="transfer"
        )
        
        session.add(new_transaction)
        await session.commit()
        
        return {"status": "success"}
    
    except sa_exc.SQLAlchemyError:
        await session.rollback()
        return {"status": "database_error"}

async def deposit_funds(session: AsyncSession, wallet_id: int, amount: Decimal):
    try:
        async with session.begin():
            stmt = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
            result = await session.execute(stmt)
            wallet = result.scalar_one()
            
            if wallet.balance < amount:
                return {"status": "insufficient_funds"}

            wallet.balance += amount

            new_transaction = Transaction(
                amount=amount,
                from_wallet_id=None,
                to_wallet_id=wallet.id,
                type="deposit"
            )

            session.add(new_transaction)
            await session.commit()

        return {"status": "success"}
    
    except sa_exc.SQLAlchemyError:
        await session.rollback()

        return {"status": "database_error"}
    
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


