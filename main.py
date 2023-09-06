from fastapi import FastAPI, Depends, HTTPException, status, Header, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.db.database import create_tables, get_db
from application.services import user_service, transaction_service, wallet_service, exchange_service
from application.dtos.amount_dto import AmountOutDTO
from application.dtos.user_dto import UserCreateDTO, UserOutDTO, UserListDTO
from application.dtos.wallet_dto import WalletCreateDTO, WalletOutDTO, WalletListDTO
from application.dtos.transaction_dto import TransactionCreateDTO, TransactionListDTO, TransactionOutDTO
from decimal import Decimal, InvalidOperation
from typing import List
from datetime import datetime
import re
import uuid
import logging


logging.basicConfig(level=logging.INFO)

# Init FastAPI
app = FastAPI()

security = HTTPBasic()

@app.on_event("startup")
async def startup_event():
    await init()

# Error Class
class ErrorResponse(BaseModel):
    status: int
    message: str

# Conveter str to decimal
def ensure_decimal_places(d: Decimal, n: int) -> Decimal:
    try:
        d_str = format(d, f".{n}f")
        
        return Decimal(d_str)
    except InvalidOperation:
        raise ValueError("Invalid decimal operation")
    except Exception as e:
        raise ValueError(f"An error occurred: {e}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": exc.status_code, "message": exc.detail},
    )

async def get_token(token: str = Header()):
    logging.info(f"Token received: {token}")
    if not token:
        raise HTTPException(status_code=401, detail="Bad token")
    return token

# Check token and user
async def get_current_user(token: str = Depends(get_token), session: AsyncSession = Depends(get_db)):
    try:
        logging.info(f"Token received: {token}")
        user_id = await user_service.verify_token(token)
        # Checking user existance
        current_user = await user_service.get_user_by_id_from_token(session, user_id)
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return current_user
    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

# Get user by token
@app.get("/users/me", response_model=UserOutDTO)
async def read_users_me(current_user: str = Depends(get_current_user)):
    try:
        return current_user
    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@app.get("/users/me2")
async def read_current_user(credentials: HTTPBasicCredentials = Depends(security), session: AsyncSession = Depends(get_db)):
    user = await user_service.authenticate_user(session, credentials.username, credentials.password)
    if not user: # check this for False
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    logging.info(f"User id received in login: {user.id}")
    access_token = user_service.create_access_token(user.id)
    return {"access_token": access_token}

# Auth through reg
@app.post("/auth/register")
async def register(user: UserCreateDTO, session: AsyncSession = Depends(get_db)):
    user = await user_service.create_new_user(session, user)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    # new_wallet = WalletCreateDTO(balance=0.000001, reserved_balance=0.000001, currency_id=1, user_id=user.id)
    wallets = await wallet_service.create_wallets_for_all_currencies(session, user.id)
    logging.info(f"User id received in register: {user.id}")
    access_token = user_service.create_access_token(user.id)
    return {"access_token": access_token} #wallets 

# Auth through login
@app.post("/auth/login")
async def login(username: str, password: str, session: AsyncSession = Depends(get_db)):
    user = await user_service.authenticate_user(session, username, password)
    if not user: # check this for False
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    logging.info(f"User id received in login: {user.id}")
    access_token = user_service.create_access_token(user.id)
    return {"access_token": access_token}


# Get wallets
@app.get("/user/wallets", response_model=WalletListDTO)
async def get_wallets(session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    wallets = await wallet_service.get_wallets_by_user_id(session, current_user.id)
    return wallets

# Get wallet
@app.get("/user/wallet", response_model=WalletOutDTO)
async def get_wallet(wallet_id: uuid.UUID, session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    logging.info(f"Wallet_id received in /wallet: {wallet_id}")
    try:
        wallet = await wallet_service.get_wallet_by_wallet_id(session, wallet_id, current_user.id)
        if wallet:
            return wallet
        else:
            raise HTTPException()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str("Wrong wallet ID or it is not your wallet ID"))

# Get transactions
@app.get("/user/transactions", response_model=TransactionListDTO)
async def get_user_transactions(session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    
    logging.info(f"User_id received in /user/transactions: {current_user.id}")
    try:
        transactions = await transaction_service.get_all_user_transactions(session, current_user.id)
        if transactions:
            return transactions
        else:
            raise HTTPException()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str("No transactions"))

# Get transactions
@app.get("/wallet/transactions", response_model=TransactionListDTO)
async def get_wallet_transactions(wallet_id: uuid.UUID, session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    
    logging.info(f"User_id received in /wallet/transactions: {current_user.id}")
    try:
        transactions = await transaction_service.get_user_transactions_by_wallet_id(session, wallet_id, current_user.id)
        if transactions:
            return transactions
        else:
            raise HTTPException()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str("No transactions"))

# Make deposit
@app.post("/wallet/deposit", response_model=WalletOutDTO)
async def deposit_wallet(wallet_id: uuid.UUID, amount: Decimal = Query(..., alias="amount"),  session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    amount = ensure_decimal_places(amount, 10)
    logging.info(f"Serialized amount: {amount}")
    if amount <= Decimal(0.0000000001):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")    
    if not isinstance(amount, Decimal):
        raise HTTPException(status_code=400, detail="Amount must be a decimal number")
    try:
        return await transaction_service.deposit_funds(session, wallet_id, amount, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/wallet/exchange", response_model=AmountOutDTO)
async def exchange_amount(from_currency: int, to_currency: int, amount: Decimal = Query(..., alias="amount"),  session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    amount = ensure_decimal_places(amount, 10)
    logging.info(f"Serialized amount: {amount}")
    if amount <= Decimal(0.0000000001):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")    
    if not isinstance(amount, Decimal):
        raise HTTPException(status_code=400, detail="Amount must be a decimal number")
    try:
        return await exchange_service.convert_funds(session, amount, from_currency, to_currency)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/wallet/transfer")
async def transfer_funds(source_wallet_id: uuid.UUID, target_wallet_id: uuid.UUID, amount: Decimal, session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    amount = ensure_decimal_places(amount, 10)
    logging.info(f"Serialized amount: {amount}")
    logging.info(f"User id: {current_user.id}")
    user_id = current_user.id
    if amount <= Decimal(0.0000000001):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")
    if not isinstance(amount, Decimal):
        raise HTTPException(status_code=400, detail="Amount must be a decimal number")
    try:
        return await transaction_service.transfer_funds_with_convertation(session, amount, source_wallet_id, target_wallet_id, user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(f"Rejected, source_wallet_id have different owner. {e}"))


@app.post("/wallet/withdraw", response_model=WalletOutDTO)
async def withdraw_funds(wallet_id: uuid.UUID, amount: Decimal, current_user: str = Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")
    if not isinstance(amount, Decimal):
        raise HTTPException(status_code=400, detail="Amount must be a decimal number")
    try:
        return await transaction_service.withdraw_funds(current_user.id, wallet_id, amount)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# ... next methods transactions

async def init():
    await create_tables()
    logging.info("DB structure updated")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True, lifespan="on", on_startup=[init])    


