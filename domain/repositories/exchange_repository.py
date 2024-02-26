from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from domain.models import Currency, ExchangeRate
from decimal import Decimal
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG)

async def add_or_update_currency(session: AsyncSession, name: str, symbol: str): # code: str
    try:
        # Проверяем, существует ли валюта с данным кодом
        stmt = select(Currency).where(Currency.symbol == symbol)
        result = await session.execute(stmt)
        currency = result.scalar_one_or_none()

        # Если валюта не найдена, создаем новую
        if not currency:
            currency = Currency(name=name, symbol=symbol)
            session.add(currency)
            await session.commit()
            logging.info(f"Created new currency: {name} ({symbol})")
        else:
            # Если валюта найдена, проверяем, нужно ли обновить имя или символ
            if currency.symbol != symbol:
                currency.name = name
                currency.symbol = symbol
                await session.commit()
                logging.info(f"Updated currency: {name} ({symbol})")

        return True
    except SQLAlchemyError as e:
        await session.rollback()
        logging.error(f"Error while getting or creating currency: {e}")
        raise e


async def update_or_create_exchange_rate(session: AsyncSession, base_currency_symbol: str, rates: dict, timestamp: datetime):
    # Получаем все валюты из базы данных
    currencies_stmt = select(Currency)
    currencies_result = await session.execute(currencies_stmt)
    currencies = {currency.symbol: currency for currency in currencies_result.scalars().all()}

    # Получаем базовую валюту
    base_currency = currencies.get(base_currency_symbol)
    if not base_currency:
        logging.error(f"Base currency {base_currency_symbol} not found in database.")
        return False

    try:
        # Обновляем курсы валют
        for symbol, rate in rates.items():
            target_currency = currencies.get(symbol)
            if not target_currency:
                logging.error(f"Target currency {symbol} not found in database.")
                continue

            exchange_rate_stmt = select(ExchangeRate).where(
                ExchangeRate.from_currency_id == base_currency.id,
                ExchangeRate.to_currency_id == target_currency.id
            )
            exchange_rate_result = await session.execute(exchange_rate_stmt)
            exchange_rate = exchange_rate_result.scalar_one_or_none()

            if not exchange_rate:
                exchange_rate = ExchangeRate(
                    from_currency_id=base_currency.id,
                    to_currency_id=target_currency.id,
                    rate=rate,
                    last_updated=timestamp
                )
                session.add(exchange_rate)
            else:
                exchange_rate.rate = rate
                exchange_rate.last_updated = timestamp

        await session.commit()
        logging.info("Exchange rates updated successfully.")
        return True
    except SQLAlchemyError as e:
        await session.rollback()
        logging.error(f"Error while updating exchange rates: {e}")
        return False
    


async def get_last_exchange_rate_update(session: AsyncSession) -> dict:
    try:
        stmt = select(func.max(ExchangeRate.last_updated))
        result = await session.execute(stmt)
        last_update = result.scalar_one_or_none()
        # Возвращаем словарь с двумя форматами даты
        return {
            'iso': last_update.isoformat() if last_update else None,
            'datetime': last_update if last_update else None
        }
    except SQLAlchemyError as e:
        print(f"Error fetching last update time: {e}")
        return None



async def get_exchange_rate(session: AsyncSession, from_currency_code: str, to_currency_code: str) -> Decimal:
    try:
        # Создаем алиасы для каждой валюты
        FromCurrency = aliased(Currency)
        ToCurrency = aliased(Currency)

        stmt = (
            select(ExchangeRate.rate)
            .join(FromCurrency, FromCurrency.id == ExchangeRate.from_currency_id)
            .where(FromCurrency.symbol == from_currency_code)
            .join(ToCurrency, ToCurrency.id == ExchangeRate.to_currency_id)
            .where(ToCurrency.symbol == to_currency_code)
        )
        result = await session.execute(stmt)
        rate = result.scalar_one_or_none()
        return rate
    except SQLAlchemyError as e:
        print(f"Error fetching exchange rate: {e}")
        return None
