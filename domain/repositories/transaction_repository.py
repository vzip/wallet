from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, and_, or_, update, join
from sqlalchemy import exc as sa_exc
from domain.models import Wallet, Transaction, ExchangeRate, Currency
from application.dtos.amount_dto import AmountOutDTO  
from application.services.amount_service import round_decimal 
from decimal import Decimal
from datetime import datetime
import uuid
import logging

logging.basicConfig(level=logging.INFO)

async def handle_transaction(session, func, *args, **kwargs):
    try:
        async with session.begin():
            return await func(session, *args, **kwargs)
    except sa_exc.SQLAlchemyError as e:
        await session.rollback()
        return f"DB reject: {e}"

async def get_all_user_transaction_by_period(session, user_id: uuid.UUID):
    try:
        # Получаем все кошельки пользователя
        stmt = select(Wallet.id).where(Wallet.user_id == user_id)
        result = await session.execute(stmt)
        wallet_ids = [row[0] for row in result.fetchall()]

        # Если у пользователя нет кошельков, возвращаем пустой список
        if not wallet_ids:
            return []

        # Получаем все транзакции для этих кошельков
        stmt = select(Transaction).where(
            or_(
                Transaction.from_wallet_id.in_(wallet_ids),
                Transaction.to_wallet_id.in_(wallet_ids)
            )
        ).order_by(Transaction.timestamp.desc())

        result = await session.execute(stmt)
        transactions = result.scalars().all()

        return transactions if transactions else []
    
    except SQLAlchemyError as e:
        logging.error(f"Error while fetching transactions: {e}")
        raise e         

async def deposit_transaction(session, wallet_id: uuid.UUID, amount: Decimal, user_id: uuid.UUID):
    try:
        logging.info(f"Amount in tansaction repository: {amount}, User Id: {user_id}")
        
        stmt = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        result = await session.execute(stmt)
        wallet = result.scalar_one()

        wallet.balance += amount

        new_transaction = Transaction(
            amount=amount,
            from_wallet_id=None,
            to_wallet_id=wallet.id,
            type="deposit",
            user_id=user_id
        )

        session.add(new_transaction)
        await session.commit()

        return wallet
    
    except SQLAlchemyError as e:
            raise e  # 

async def convert_currency(session, amount: Decimal, from_currency: int, to_currency: int):
    try:
        
        # Получить курс из базы данных
        rate_obj = await session.execute(
            select(ExchangeRate).where(
                (ExchangeRate.from_currency_id == from_currency) & 
                (ExchangeRate.to_currency_id == to_currency)
            )
        )
        rate_record = rate_obj.scalar_one_or_none()
        if rate_record is None:
            raise ValueError("Rate not found in the database")
        try:
        # Конвертировать сумму
            converted_amount = amount * Decimal(rate_record.rate)
            converted_amount = round_decimal(converted_amount)
        except Exception as e:
            logging.info(f"Error in conversion: {e}")
            raise e
        logging.info(f"Amount after convertation in tansaction repository: {converted_amount}")
        result_amount = AmountOutDTO(
            from_currency=rate_record.from_currency_id,
            amount_int=amount,
            to_currency=rate_record.to_currency_id,
            rate=rate_record.rate,
            amount_ext=converted_amount
        )
        logging.info(f"Results after convertation in tansaction repository: {result_amount}")
        return result_amount
    except SQLAlchemyError as e:
        raise e

async def transfer_transaction(session, amount: Decimal, from_wallet_id: uuid.UUID, to_wallet_id: uuid.UUID, user_id: uuid.UUID):
    try:
        stmt = select(Wallet).\
            where(
                (Wallet.id == from_wallet_id) & 
                (Wallet.user_id == user_id)
            ).with_for_update()
        result = await session.execute(stmt)
        from_wallet = result.scalar_one()

        stmt = select(Wallet).where(Wallet.id == to_wallet_id).with_for_update()
        result = await session.execute(stmt)
        to_wallet = result.scalar_one()

        if from_wallet.balance < amount:
            return {"status": "insufficient_funds"}
        
        from_wallet.balance -= amount

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
            
            converted_amount = amount * exchange_rate.rate
            converted_amount = round_decimal(converted_amount)
        
        to_wallet.balance += converted_amount

        new_transaction = Transaction(
            from_wallet_id=from_wallet.id,
            from_currency_id=from_wallet.currency_id,
            amount=amount,
            to_wallet_id=to_wallet.id,
            to_currency_id=to_wallet.currency_id,
            rate=exchange_rate.rate,
            converted_amount=converted_amount,
            type="transfer",
            status="close",
            user_id=user_id
        )
        
        session.add(new_transaction)
        await session.commit()
        
        return new_transaction
    except SQLAlchemyError as e:
        raise e