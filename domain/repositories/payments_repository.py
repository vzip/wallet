from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, and_, or_, update, join
from sqlalchemy import exc as sa_exc
from domain.models import Wallet, Transaction, ExchangeRate, Currency, ServiceWallet, PendingTransaction, ServiceUser, ServiceTransaction, ExternalWallet, UserExternalWallet
from application.dtos.amount_dto import AmountOutDTO  
from application.services.amount_service import round_decimal 
from domain.repositories.wallet_repository import get_wallet_by_id, get_service_wallet_by_id
from decimal import Decimal
from datetime import datetime
import uuid
import logging

logging.basicConfig(level=logging.INFO)


async def update_deposit_transaction(session, transaction_id: uuid.UUID, new_status: str, service_user: uuid.UUID):
    try:

        # Проверка, что запрос исходит от доверенного сервисного пользователя
        service_user_stmt = select(ServiceUser).where(ServiceUser.id == service_user)
        service_user_result = await session.execute(service_user_stmt)
        service_user_record = service_user_result.scalar_one_or_none()

        if not service_user_record:
            return {"error": "unauthorized"}
        
        # Найти соответствующую запись в pending_transactions
        stmt = select(PendingTransaction).where(PendingTransaction.id == transaction_id)
        result = await session.execute(stmt)
        pending_transaction = result.scalar_one_or_none()

        if not pending_transaction:
            return {"error": "transaction_not_found"}

        # Проверить текущий и новый статус
        if pending_transaction.status != 'pending' or new_status not in ['paid', 'rejected']:
            return {"error": "invalid_status_update"}
        
        # Проверить тип транзакции 
        if pending_transaction.type != 'deposit':
            return {"error": "invalid_type_transaction"}

        # Обновляем статус
        pending_transaction.status = new_status

        if new_status == 'paid':

            # Достаем external_wallet
            # external_wallet = await get_wallet_by_id(session, pending_transaction.external_wallet_id)

            # Начисляем сумму на service_wallet
            service_wallet_stmt = select(ServiceWallet).where(ServiceWallet.id == pending_transaction.from_wallet_id)
            service_wallet_result = await session.execute(service_wallet_stmt)
            service_wallet = service_wallet_result.scalar_one_or_none()
            
            if not service_wallet:
                return {"error": "service_wallet_not_found"}
            
            service_wallet.balance += pending_transaction.converted_amount
            
             # Вычисляем комиссию:
            commission_amount = pending_transaction.converted_amount * service_wallet.commission_rate

            # Начисляем средства на кошелек пользователя
            to_wallet_stmt = select(Wallet).where(Wallet.id == pending_transaction.to_wallet_id)
            to_wallet_result = await session.execute(to_wallet_stmt)
            to_wallet = to_wallet_result.scalar_one_or_none()

            if not to_wallet:
                return {"error": "target_wallet_not_found"}

            # Создаем новую транзакцию в cервисных транзакциях для фиксирования перевода с external на service_wallet
            new_transaction_service = ServiceTransaction(
                from_wallet_id=pending_transaction.external_wallet_id,  # ID внешнего кошелька
                from_currency_id=pending_transaction.from_currency_id,
                amount=pending_transaction.amount,
                to_wallet_id=pending_transaction.from_wallet_id,
                to_currency_id=pending_transaction.from_currency_id,
                rate=1,  
                converted_amount=pending_transaction.converted_amount,
                type="deposit",
                status="close",
                user_id=service_wallet.user_id  # ID пользователя, владельца service_wallet
            )
            session.add(new_transaction_service)
            
            # Списываем сумму с service_wallet
            service_wallet.balance -= pending_transaction.converted_amount

            # Создаем новую транзакцию в основных транзакциях для перевода на кошелек пользователя
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

            # Начисляем сумму на target wallet
            to_wallet.balance += pending_transaction.converted_amount

            # Создаем транзакцию комиссии:
            commission_transaction = Transaction(
                from_wallet_id=pending_transaction.to_wallet_id,
                from_currency_id=pending_transaction.to_currency_id,
                amount=commission_amount,
                to_wallet_id=service_wallet.id,
                to_currency_id=service_wallet.currency_id,
                rate=1,
                converted_amount=commission_amount,
                type="commission",
                status="close",
                user_id=service_wallet.user_id
            )
            session.add(commission_transaction)

            # Вычитаем сумму комиссии c target wallet и начисляем ее на сервисный кошелек:
            to_wallet.balance -= commission_amount
            service_wallet.balance += commission_amount


        elif new_status == 'rejected':
            # Здесь ваш код для обработки отклоненной транзакции
            logging.info(f"Transaction {transaction_id} was rejected.")

        await session.commit()

        return new_transaction_service

    except SQLAlchemyError as e:
        await session.rollback()
        raise e
    
    

async def update_withdraw_transaction(session, transaction_id: uuid.UUID, new_status: str, service_user_id: uuid.UUID):
    try:

        # Проверка, что запрос исходит от доверенного сервисного пользователя
        service_user_stmt = select(ServiceUser).where(ServiceUser.id == service_user_id)
        service_user_result = await session.execute(service_user_stmt)
        service_user_record = service_user_result.scalar_one_or_none()

        if not service_user_record:
            return {"error": "unauthorized"}
        
        # Найти соответствующую запись в pending_transactions
        stmt = select(PendingTransaction).where(PendingTransaction.id == transaction_id)
        result = await session.execute(stmt)
        pending_transaction = result.scalar_one_or_none()

        if not pending_transaction:
            return {"error": "transaction_not_found"}

        # Проверить текущий и новый статус
        if pending_transaction.status != 'pending' or new_status not in ['paid', 'rejected']:
            return {"error": "invalid_status_of_pending_transaction_or_wrong_new_status"}
        
        # Проверить тип транзакции
        if pending_transaction.type != 'withdraw':
            return {"error": "invalid_type_transaction"}

        # Обновляем статус
        pending_transaction.status = new_status

        if new_status == 'paid':

            # Получаем подходящий service_wallet
            service_wallet_stmt = select(ServiceWallet).where(
                ServiceWallet.user_id == service_user_id,
                ServiceWallet.currency_id == pending_transaction.from_currency_id
                )
            service_wallet_result = await session.execute(service_wallet_stmt)
            service_wallet = service_wallet_result.scalar_one_or_none()
            
            if not service_wallet:
                return {"error": "service_wallet_not_found"}
            
            # Найти сервисный кошелек с той же валютой
            user_external_wallet_stmt = select(UserExternalWallet).where(
                UserExternalWallet.id == pending_transaction.to_wallet_id,
                UserExternalWallet.user_id == pending_transaction.user_id
            )
            result = await session.execute(user_external_wallet_stmt)
            user_ext_wallet = result.scalar_one_or_none()
            
            if not user_ext_wallet:
                return {"error": "user_ext_wallet_not_found"}
            logging.info(f"User external wallet: {user_ext_wallet}")

            
            # Найти внешний сервисный кошелек с той же валютой
            external_wallet_stmt = select(ExternalWallet).where(
                ExternalWallet.currency_id == pending_transaction.from_currency_id,
                ExternalWallet.user_id == service_user_id 
            )
            result = await session.execute(external_wallet_stmt)
            external_wallet = result.scalar_one_or_none()

            logging.info(f"External wallet: {external_wallet}")

            if not external_wallet:
                return {"error": "external_wallet_not_found"}

             # Вычисляем комиссию согласно rate на внешнем кошелькке с которого вывод:
            commission_amount = pending_transaction.converted_amount * external_wallet.commission_rate
            
            # Вычисляем cумму перевода за вычетом комиссии:
            new_amount = pending_transaction.converted_amount - commission_amount

            # Начисляем комиссию на сервисный кошелек 
            service_wallet.balance += commission_amount

            # Фиксируем сумму вывода во внешнем пользовательском кошельке для учета общей суммы вывода 
            # Будет использовано для лимитов вывода 
            user_ext_wallet.amount_withdraw += new_amount

            # Получаем необходимый кошелек пользователя
            user_wallet_stmt = select(Wallet).where(
                Wallet.id == pending_transaction.from_wallet_id,
                Wallet.user_id == pending_transaction.user_id,
                )
            user_wallet_result = await session.execute(user_wallet_stmt)
            user_wallet = user_wallet_result.scalar_one_or_none()

            if not user_wallet:
                return {"error": "user_wallet_not_found"}
            
            user_wallet.reserved_balance -= pending_transaction.converted_amount

            # Создаем новую транзакцию в основных транзакциях отражающую вывод за минусом комисиии с кошелька на внешний аккаунт пользователя
            new_transaction_user = Transaction(
                from_wallet_id=pending_transaction.from_wallet_id,
                from_currency_id=pending_transaction.from_currency_id,
                amount=new_amount,
                to_wallet_id=pending_transaction.to_wallet_id,
                to_currency_id=pending_transaction.to_currency_id,
                rate=pending_transaction.rate,
                converted_amount=new_amount,
                type="withdraw",
                status="close",
                user_id=service_wallet.user_id
            )
            session.add(new_transaction_user)

            # Создаем транзакцию комиссии:
            commission_transaction = Transaction(
                from_wallet_id=pending_transaction.from_wallet_id,
                from_currency_id=pending_transaction.from_currency_id,
                amount=commission_amount,
                to_wallet_id=service_wallet.id,
                to_currency_id=service_wallet.currency_id,
                rate=1,
                converted_amount=commission_amount,
                type="commission",
                status="close",
                user_id=service_wallet.user_id
            )
            session.add(commission_transaction)

            # Создаем новую транзакцию в cервисных транзакциях для фиксирования перевода с service_external_wallet на user_external_wallet
            new_transaction_service = ServiceTransaction(
                from_wallet_id=pending_transaction.external_wallet_id,  # ID сервисного внешнего кошелька
                from_currency_id=pending_transaction.from_currency_id,
                amount=new_amount,
                to_wallet_id=pending_transaction.to_wallet_id,
                to_currency_id=pending_transaction.to_currency_id,
                rate=1,  
                converted_amount=new_amount,
                type="withdraw",
                status="close",
                user_id=service_wallet.user_id  # ID сервиисного пользователя, владельца service_wallet
            )
            session.add(new_transaction_service)


        elif new_status == 'rejected':
            # Здесь ваш код для обработки отклоненной транзакции
            logging.info(f"Transaction {transaction_id} was rejected.")
            
            # Надо возвратить с reserved_balance средства на баланс:
            # Получаем необходимый кошелек пользователя
            user_wallet_stmt = select(Wallet).where(
                Wallet.id == pending_transaction.from_wallet_id,
                Wallet.user_id == pending_transaction.user_id,
                )
            user_wallet_result = await session.execute(user_wallet_stmt)
            user_wallet = user_wallet_result.scalar_one_or_none()

            if not user_wallet:
                return {"error": "user_wallet_not_found"}
            
            user_wallet.reserved_balance -= pending_transaction.converted_amount
            user_wallet.balance += pending_transaction.converted_amount
            
            await session.commit()
            
            return {"error": f"Pending transaction {pending_transaction.id} succesfuly changed status on rejected"}
            
        await session.commit()

        return new_transaction_service

    except SQLAlchemyError as e:
        await session.rollback()
        raise str(e)
