from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, and_, or_, update, join
from sqlalchemy import exc as sa_exc
from domain.models import Wallet, Transaction, ExchangeRate, Currency, ServiceWallet, PendingTransaction, ServiceUser
from application.dtos.amount_dto import AmountOutDTO  
from application.services.amount_service import round_decimal 
from domain.repositories.wallet_repository import get_wallet_by_id
from decimal import Decimal
from datetime import datetime
import uuid
import logging

logging.basicConfig(level=logging.INFO)


async def mock_external_payment_api():
    # В реальной жизни здесь будет запрос к внешнему API
    return uuid.uuid4()  # Возвращаем уникальный идентификатор транзакции

async def update_transaction(session, transaction_id: uuid.UUID, new_status: str, service_user: uuid.UUID):
    try:

        # Проверка, что запрос исходит от доверенного сервисного пользователя
        service_user_stmt = select(ServiceUser).where(ServiceUser.id == service_user)
        service_user_result = await session.execute(service_user_stmt)
        service_user_record = service_user_result.scalar_one_or_none()

        if not service_user_record:
            return {"status": "unauthorized"}
        
        # Найти соответствующую запись в pending_transactions
        stmt = select(PendingTransaction).where(PendingTransaction.id == transaction_id)
        result = await session.execute(stmt)
        pending_transaction = result.scalar_one_or_none()

        if not pending_transaction:
            return {"status": "transaction_not_found"}

        # Проверить текущий и новый статус
        if pending_transaction.status != 'pending' or new_status not in ['paid', 'rejected']:
            return {"status": "invalid_status_update"}

        # Обновляем статус
        pending_transaction.status = new_status

        if new_status == 'paid':

            # Cписываем сумму с external_wallet
            external_wallet = await get_wallet_by_id(session, pending_transaction.external_wallet_id)
            external_wallet.balance += pending_transaction.amount

            # Начисляем сумму на service_wallet
            service_wallet = await get_wallet_by_id(session, pending_transaction.from_wallet_id)
            service_wallet.balance += pending_transaction.amount

            # Начисляем средства на кошелек пользователя
            to_wallet_stmt = select(Wallet).where(Wallet.id == pending_transaction.to_wallet_id)
            to_wallet_result = await session.execute(to_wallet_stmt)
            to_wallet = to_wallet_result.scalar_one_or_none()

            if not to_wallet:
                return {"status": "target_wallet_not_found"}

            to_wallet.balance += pending_transaction.converted_amount

            # Создаем новую транзакцию в основной таблице транзакций для пополнения service_wallet
            new_transaction_service = Transaction(
                from_wallet_id=pending_transaction.external_wallet_id,  # ID внешнего кошелька
                from_currency_id=pending_transaction.from_currency_id,
                amount=pending_transaction.amount,
                to_wallet_id=pending_transaction.to_wallet_id,
                to_currency_id=pending_transaction.to_currency_id,
                rate=1,  
                converted_amount=pending_transaction.converted_amount,
                type="deposit",
                status="close",
                user_id=service_wallet.user_id  # ID пользователя, владельца service_wallet
            )
            session.add(new_transaction_service)
            
            # Списываем сумму с service_wallet
            service_wallet.balance -= pending_transaction.amount

            # Создаем новую транзакцию в основной таблице транзакций для перевода на кошелек пользователя
            new_transaction_user = Transaction(
                from_wallet_id=service_wallet.id,
                from_currency_id=service_wallet.currency_id,
                amount=pending_transaction.converted_amount,
                to_wallet_id=pending_transaction.to_wallet_id,
                to_currency_id=pending_transaction.to_currency_id,
                rate=pending_transaction.rate,
                converted_amount=pending_transaction.converted_amount,
                type="transfer",
                status="close",
                user_id=service_wallet.user_id
            )
            session.add(new_transaction_user)

        elif new_status == 'rejected':
            # Здесь ваш код для обработки отклоненной транзакции
            logging.info(f"Transaction {transaction_id} was rejected.")

        await session.commit()

        return {"status": "success"}

    except SQLAlchemyError as e:
        await session.rollback()
        raise e
