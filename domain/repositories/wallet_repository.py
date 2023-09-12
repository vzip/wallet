from sqlalchemy.ext.asyncio import AsyncSession
from domain.models import Wallet, Currency, ServiceWallet, ExternalWallet
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, and_
from decimal import Decimal
import uuid
import logging
logging.basicConfig(level=logging.INFO)

async def create_wallets(session, user_id):
        try:
            logging.info(f"User ID received to wallet repository: {user_id}")
            # Получаем все уникальные ID валют
            currency_objs = await session.execute(select(Currency.id))
            currency_ids = [c for c in currency_objs.scalars().all()]  

            new_wallets = []
            for currency_id in currency_ids:
                new_wallet = Wallet(user_id=user_id, balance=Decimal("0.000001"), reserved_balance=Decimal("0.000001"), currency_id=currency_id)
                session.add(new_wallet)
                new_wallets.append(new_wallet)

            await session.flush()  # Получаем ID перед commit
            await session.commit()
            return new_wallets
        except SQLAlchemyError as e:
            logging.error(f"Error while creating wallets: {e}")
            raise e

async def create_service_wallets(session, user_id):
        try:
            logging.info(f"User ID received to wallet repository: {user_id}")
            # Получаем все уникальные ID валют
            currency_objs = await session.execute(select(Currency.id))
            currency_ids = [c for c in currency_objs.scalars().all()]  

            new_wallets = []
            for currency_id in currency_ids:
                new_wallet = ServiceWallet(user_id=user_id, balance=Decimal("0.000001"), reserved_balance=Decimal("0.000001"), currency_id=currency_id)
                session.add(new_wallet)
                new_wallets.append(new_wallet)

            await session.flush()  # Получаем ID перед commit
            await session.commit()
            return new_wallets
        except SQLAlchemyError as e:
            logging.error(f"Error while creating wallets: {e}")
            raise e    

async def create_external_wallets(session, user_id):
    try:
        logging.info(f"User ID received to wallet repository: {user_id}")
        # Получаем все уникальные ID валют
        currency_objs = await session.execute(select(Currency.id))
        currency_ids = [c for c in currency_objs.scalars().all()]  

        new_wallets = []
        for currency_id in currency_ids:
            new_wallet = ExternalWallet(user_id=user_id, balance=Decimal("0.000001"), reserved_balance=Decimal("0.000001"), currency_id=currency_id)
            session.add(new_wallet)
            new_wallets.append(new_wallet)

        await session.flush()  # Получаем ID перед commit
        await session.commit()
        return new_wallets
    except SQLAlchemyError as e:
        logging.error(f"Error while creating external wallets: {e}")
        raise e

    
async def create_new_wallet(session, new_wallet):
        try:
            logging.info(f"User ID received to wallet repository: {new_wallet.user_id}")
            new_wallet = Wallet(user_id=new_wallet.user_id, balance=new_wallet.balance, reserved_balance=new_wallet.reserved_balance, currency_id=new_wallet.currency_id)
            session.add(new_wallet)
            await session.flush()  # Getting ID befoe commit
            await session.commit()
            return new_wallet
        except SQLAlchemyError as e:
            raise e  # 

        
async def get_wallet_by_id(session, wallet_id: uuid.UUID, user_id: uuid.UUID):
    try:
        logging.info(f"Wallet Id in wallet repository: {wallet_id}, User Id: {user_id}")
        stmt = select(Wallet).where(
            and_(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id
            )
        )
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()
        return wallet
    except SQLAlchemyError as e:
            raise e  # 
            

    
async def get_user_wallets(session, user_id: uuid.UUID):
    try:
        logging.info(f"User_id in wallet rerository: {user_id}")
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        result = await session.execute(stmt)
        wallets = result.scalars().all()
        logging.info(f"Wallets in rerository: {wallets}")
        return wallets if wallets else []      
    except SQLAlchemyError as e:
            raise e  # 
        