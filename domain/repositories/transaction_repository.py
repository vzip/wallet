from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, and_, or_, update, join
from sqlalchemy import exc as sa_exc
from domain.models import Wallet, Transaction, ExchangeRate, Currency, ServiceWallet, PendingTransaction, ExternalWallet, UserExternalWallet
from application.dtos.amount_dto import AmountOutDTO  
from application.dtos.transaction_dto import CombinedTransactionListDTO
from application.services.amount_service import round_decimal 
from decimal import Decimal
from datetime import datetime
import uuid
import logging

logging.basicConfig(level=logging.DEBUG)

async def mock_external_payment_api():
    # В реальной жизни здесь будет запрос к внешнему API
    return uuid.uuid4()  # Возвращаем уникальный идентификатор транзакции

async def handle_transaction(session, func, *args, **kwargs):
    try:
        async with session.begin():
            return await func(session, *args, **kwargs)
    except sa_exc.SQLAlchemyError as e:
        await session.rollback()
        return f"DB reject: {e}"

async def get_all_transactions(session, user_id: uuid.UUID):
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

        
        # Получаем все pending_transactions, связанные с данным кошельком
        stmt = select(PendingTransaction).where(
                PendingTransaction.user_id == user_id,
        ).order_by(PendingTransaction.timestamp.desc())

        result = await session.execute(stmt)
        pending_transactions = result.scalars().all()


        return CombinedTransactionListDTO(transactions=transactions, pending_transactions=pending_transactions)
    
    
    except SQLAlchemyError as e:
        logging.error(f"Error while fetching transactions: {e}")
        raise e         

async def get_transactions_by_wallet_id(session, wallet_id: uuid.UUID, user_id: uuid.UUID):
    try:
        # Проверяем, принадлежит ли кошелек заданному пользователю
        stmt = select(Wallet).where(
            and_(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id
            )
        )
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()

        if not wallet:
            logging.warning(f"Wallet ID {wallet_id} does not belong to User ID {user_id}")
            return None

        # Получаем все транзакции, связанные с данным кошельком
        stmt = select(Transaction).where(
            or_(
                Transaction.from_wallet_id == wallet_id,
                Transaction.to_wallet_id == wallet_id
            )
        ).order_by(Transaction.timestamp.desc())

        result = await session.execute(stmt)
        transactions = result.scalars().all()

        # Получаем все pending_transactions, связанные с данным кошельком
        stmt = select(PendingTransaction).where(
            and_(
                PendingTransaction.user_id == user_id,
                PendingTransaction.to_wallet_id == wallet_id, 

            )
        ).order_by(PendingTransaction.timestamp.desc())

        result = await session.execute(stmt)
        pending_transactions = result.scalars().all()


        return CombinedTransactionListDTO(transactions=transactions, pending_transactions=pending_transactions)
    
    except SQLAlchemyError as e:
        logging.error(f"Error while fetching transactions: {e}")
        raise e


async def create_pending_deposit(session, wallet_id: uuid.UUID, amount: Decimal, user_id: uuid.UUID, service_user_id: uuid.UUID):
    try:
        # Найти кошелек пользователя
        stmt = select(Wallet).where(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id
            )
        result = await session.execute(stmt)
        user_wallet = result.scalar_one_or_none()

        if not user_wallet:
            return {"error": "wallet_not_found"}

        # Найти сервисный кошелек с той же валютой
        stmt = select(ServiceWallet).where(
            ServiceWallet.currency_id == user_wallet.currency_id,
            ServiceWallet.user_id == service_user_id  # Добавлено условие
        )
        result = await session.execute(stmt)
        service_wallet = result.scalar_one_or_none()

        if not service_wallet:
            return {"error": "service_wallet_not_found"}
        
        # Найти сервисный кошелек с той же валютой
        stmt = select(ExternalWallet).where(
            ExternalWallet.currency_id == user_wallet.currency_id,
            ExternalWallet.user_id == service_user_id  # Добавлено условие
        )
        result = await session.execute(stmt)
        external_wallet = result.scalar_one_or_none()

        if not external_wallet:
            return {"error": "service_external_wallet_not_found"}

        # Получаем идентификатор от "внешнего" API
        external_transaction_id = await mock_external_payment_api()

        if not external_transaction_id:
            return {"error": "service_wallet_not_responding"}

        # Создать запись в pending_transactions
        pending_transaction = PendingTransaction(
            from_wallet_id=service_wallet.id,
            from_currency_id=service_wallet.currency_id,
            amount=amount,
            to_wallet_id=user_wallet.id,
            to_currency_id=user_wallet.currency_id,
            rate=1.0,
            converted_amount=amount,
            type="deposit",
            status="pending",
            user_id=user_id,
            external_wallet_id=external_wallet.id,
            external_transaction_id=external_transaction_id
        )
        session.add(pending_transaction)
        await session.commit()

        return pending_transaction

    except SQLAlchemyError as e:
        await session.rollback()
        raise e

async def create_pending_withdraw(session, wallet_id: uuid.UUID, amount: Decimal, user_id: uuid.UUID, service_user_id: uuid.UUID):
    try:
        # Найти кошелек пользователя
        stmt = select(Wallet).where(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id
            )
        result = await session.execute(stmt)
        user_wallet = result.scalar_one_or_none()
        
        if not user_wallet:
            return {"error": "wallet_not_found"}
        logging.info(f"User wallet: {user_wallet}")

        if user_wallet.balance <= amount:
            return {"error": "wallet_do_not_have_enough_funds"}
        
        user_wallet.balance -= amount
        user_wallet.reserved_balance += amount

        # Найти сервисный кошелек с той же валютой
        stmt2 = select(UserExternalWallet).where(
            UserExternalWallet.currency_id == user_wallet.currency_id,
            UserExternalWallet.user_id == user_id  
        )
        result = await session.execute(stmt2)
        user_ext_wallet = result.scalar_one_or_none()
        
        if not user_ext_wallet:
            return {"error": "user_ext_wallet_not_found"}
        logging.info(f"User external wallet: {user_ext_wallet}")

        # Найти внешний сервисный кошелек с той же валютой
        stmt3 = select(ExternalWallet).where(
            ExternalWallet.currency_id == user_wallet.currency_id,
            ExternalWallet.user_id == service_user_id 
        )
        result = await session.execute(stmt3)
        external_wallet = result.scalar_one_or_none()

        

        if not external_wallet:
            return {"error": "external_wallet_not_found"}
        
        logging.info(f"External wallet: {external_wallet}")
        logging.info(f"Amount: {amount}")
        logging.info(f"external_wallet.balance: {external_wallet.balance}")

        if amount >= external_wallet.balance:
            return {"error": "external_wallet_balance_lower_than_withdraw_amount"}
        
        logging.info(f"external_wallet.commission_rate: {external_wallet.commission_rate}")
        # Вычисляем комиссию:
        commission_amount = amount * external_wallet.commission_rate

        logging.info(f"commission_amount: {commission_amount}")
        
        # Получаем идентификатор от "внешнего" API
        external_transaction_id = await mock_external_payment_api()
        
        if not external_transaction_id:
            return {"error": "external_wallet_not_responding"}
        
        logging.info(f"external_transaction_id in tansaction repository: {external_transaction_id}")

        # Создать запись в pending_transactions
        pending_transaction = PendingTransaction(
            from_wallet_id=user_wallet.id,
            from_currency_id=user_wallet.currency_id,
            amount=amount,
            to_wallet_id=user_ext_wallet.id,
            to_currency_id=user_ext_wallet.currency_id,
            rate=1.0,
            converted_amount=amount,
            type="withdraw",
            status="pending",
            user_id=user_id,
            external_wallet_id=external_wallet.id,
            external_transaction_id=external_transaction_id
        )

        logging.info(f"Pending transaction details: {pending_transaction}")

        session.add(pending_transaction)
        await session.commit()
        return pending_transaction

    except SQLAlchemyError as sae:
        await session.rollback()
        return str(sae)   
        

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
        from_wallet = result.scalar_one_or_none()
        
        if not from_wallet:
            logging.info(f"source_wallet_id have different owner")
            return {"error": "source_wallet_id have different owner"}
        

        stmt = select(Wallet).where(Wallet.id == to_wallet_id).with_for_update()
        result = await session.execute(stmt)
        to_wallet = result.scalar_one_or_none()

        if not to_wallet:
            logging.info(f"target_wallet_id does not exist")
            return {"error": "target_wallet_id does not exist"}
        
        if from_wallet.balance < amount:
            return {"error": "insufficient_funds"}

        from_wallet.balance -= amount

        converted_amount = amount  # Инициализация
        rate = Decimal('1.0')  # Initialize rate

        if from_wallet.currency_id != to_wallet.currency_id:
            stmt = select(ExchangeRate).\
                where(
                    (ExchangeRate.from_currency_id == from_wallet.currency_id) & 
                    (ExchangeRate.to_currency_id == to_wallet.currency_id)
                )
            result = await session.execute(stmt)
            exchange_rate = result.scalar_one_or_none()
            
            if not exchange_rate:
                logging.info(f"NO exchange rate for curencies: {from_wallet.currency_id} and {to_wallet.currency_id}")
                return {"error": "exchange_rate_not_found"}
            
            converted_amount = amount * exchange_rate.rate
            converted_amount = round_decimal(converted_amount)
            rate = exchange_rate.rate
        
        to_wallet.balance += converted_amount
        logging.info(f"to_wallet.balance:  {to_wallet.balance}")

        new_transaction = Transaction(
            from_wallet_id=from_wallet.id,
            from_currency_id=from_wallet.currency_id,
            amount=amount,
            to_wallet_id=to_wallet.id,
            to_currency_id=to_wallet.currency_id,
            rate=rate,
            converted_amount=converted_amount,
            type="transfer",
            status="close",
            user_id=from_wallet.user_id
        )
        logging.info(f"new_transaction:  {new_transaction}")

        session.add(new_transaction)
        await session.flush()
        await session.commit()
        logging.info(f"new_transaction:  {new_transaction}")

        return new_transaction
    except SQLAlchemyError as e:
        logging.info(f"SQLAlchemyError:  {e}")
        await session.rollback()
        raise e