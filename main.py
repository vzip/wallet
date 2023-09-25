from fastapi import FastAPI, Depends, HTTPException, status, Header, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.db.database import create_tables, get_db
from application.services import user_service, transaction_service, wallet_service, exchange_service, payment_service
from application.dtos.amount_dto import AmountOutDTO
from application.dtos.user_dto import UserCreateDTO, UserOutDTO, UserListDTO
from application.dtos.wallet_dto import WalletCreateDTO, WalletOutDTO, WalletListDTO, UserExtWalletCreateDTO
from application.dtos.transaction_dto import TransactionCreateDTO, TransactionListDTO, TransactionOutDTO, PendingTransactionOutDTO, CombinedTransactionListDTO
from decimal import Decimal, InvalidOperation
from typing import List
from datetime import datetime
from pydantic import ValidationError
import re
import uuid
import logging
import subprocess
import asyncio



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

####
app.mount("/tests/reports", StaticFiles(directory="tests/reports"), name="reports")

async def run_command(command: str):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        yield line.decode("utf-8").strip() + "\n"

@app.get("/run-tests/")
async def read_root():
    command = "pytest -v tests/fastapi_online.py --html=tests/reports/report.html"
    return StreamingResponse(run_command(command), media_type="text/event-stream")

@app.get("/run-tests-local/")
async def read_root():
    command = "pytest -v tests/fastapi_local.py --html=tests/reports/report.html"
    return StreamingResponse(run_command(command), media_type="text/event-stream")
####

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

# Check token and service_user   
async def get_current_service_user(token: str = Depends(get_token), session: AsyncSession = Depends(get_db)):
    try:
        logging.info(f"Token received: {token}")
        user_id = await user_service.verify_token(token)
        # Checking user existance
        current_user = await user_service.get_service_user_by_id_from_token(session, user_id)
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return current_user
    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))    

# Get user by token
@app.get("/user/get/id", response_model=UserOutDTO)
async def read_users_me(current_user: str = Depends(get_current_user)):
    try:
        return current_user
    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@app.get("/user/get/token")
async def read_current_user(credentials: HTTPBasicCredentials = Depends(security), session: AsyncSession = Depends(get_db)):
    user = await user_service.authenticate_user(session, credentials.username, credentials.password)
    if not user: # check this for False
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    logging.info(f"User id received in login: {user.id}")
    access_token = user_service.create_access_token(user.id)
    return {"access_token": access_token}

# Auth through reg
@app.post("/auth/register")
async def register(user_data: dict, session: AsyncSession = Depends(get_db)):
    exception_raised = False
    try:
        user = UserCreateDTO(**user_data)
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(f"{ve}"))
    
    try:
        user = await user_service.create_new_user(session, user)
        if not user:
            exception_raised = True
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        logging.info(f"user in main: {user}")
        if isinstance(user, dict) and 'error' in user:
            text_error = user['error']
            logging.info(f"text_error in /auth/register: {text_error}")
            exception_raised = True
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(text_error))
        else:
            
            # new_wallet = WalletCreateDTO(balance=0.000001, reserved_balance=0.000001, currency_id=1, user_id=user.id)
            wallets = await wallet_service.create_wallets_for_all_currencies(session, user.id)
            logging.info(f"User id received in register: {user.id}")
            access_token = user_service.create_access_token(user.id)
            return {"access_token": access_token} #wallets 

    except Exception as e:
        if exception_raised:
            raise e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))    

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

# Create external wallet
@app.post("/user/create/external_wallet")
async def create_new_user_ext_wallet(wallet_name: str, currency_id: int, session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    logging.info(f"User id received in /user/create/external_wallet: {current_user.id}")
    currency_id = int(currency_id)
    try:
        new_user_ext_wallet = await wallet_service.create_ext_wallet(session, wallet_name, currency_id, current_user.id)
        if new_user_ext_wallet:
            return new_user_ext_wallet
        else:
            raise HTTPException()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(f"{e}"))    



# Get transactions
@app.get("/user/transactions", response_model=CombinedTransactionListDTO)
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
@app.get("/wallet/transactions", response_model=CombinedTransactionListDTO)
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
@app.post("/wallet/deposit", response_model=PendingTransactionOutDTO)
async def deposit_wallet(service_user_id: uuid.UUID, wallet_id: uuid.UUID, amount: Decimal = Query(..., alias="amount"),  session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    amount = ensure_decimal_places(amount, 10)
    logging.info(f"Serialized amount: {amount}")
    if amount <= Decimal(0.0000000001):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")    
    if not isinstance(amount, Decimal):
        raise HTTPException(status_code=400, detail="Amount must be a decimal number")
    exception_raised = False
    try:
        pending_transaction = await transaction_service.deposit_funds(session, wallet_id, amount, current_user.id, service_user_id)
        logging.info(f"pending_transaction in main: {pending_transaction}")
        if isinstance(pending_transaction, dict) and 'error' in pending_transaction:
            text_error = pending_transaction['error']
            logging.info(f"text_error in main: {text_error}")
            exception_raised = True
            raise HTTPException(status_code=400, detail=str(text_error))
        else:
            return pending_transaction
        
    except Exception as e:
        if exception_raised:
            raise e
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
    exception_raised = False
    try:
        transfer_transaction = await transaction_service.transfer_funds_with_convertation(session, amount, source_wallet_id, target_wallet_id, user_id)
        logging.info(f"Tansfer transaction in main: {transfer_transaction}")
        if isinstance(transfer_transaction, dict) and 'error' in transfer_transaction:
            text_error = transfer_transaction['error']
            logging.info(f"text_error in main: {text_error}")
            exception_raised = True
            raise HTTPException(status_code=400, detail=str(text_error))
        else:
            return transfer_transaction
    except Exception as e:
        if exception_raised:
            raise e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(f"Rejected by {e}"))

@app.post("/wallet/withdraw", response_model=PendingTransactionOutDTO)
async def withdraw_funds(service_user_id: uuid.UUID, from_wallet_id: uuid.UUID, amount: Decimal = Query(..., alias="amount"),  session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    amount = ensure_decimal_places(amount, 10)
    logging.info(f"Serialized amount: {amount}")
    if amount <= Decimal(0.0000000001):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")
    if not isinstance(amount, Decimal):
        raise HTTPException(status_code=400, detail="Amount must be a decimal number")
    exception_raised = False
    try:
        pending_transaction = await transaction_service.withdraw_funds(session, from_wallet_id, amount, current_user.id, service_user_id)
        logging.info(f"pending_transaction in main: {pending_transaction}")
        if isinstance(pending_transaction, dict) and 'error' in pending_transaction:
            text_error = pending_transaction['error']
            logging.info(f"text_error in main: {text_error}")
            exception_raised = True
            raise HTTPException(status_code=400, detail=str(text_error))
        else:
            return pending_transaction
        
    except Exception as e:
        if exception_raised:
            raise e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(f"Rejected by {e}"))

# Service user methods

# Auth through reg
@app.post("/auth/register_service")
async def register_service(user: UserCreateDTO, session: AsyncSession = Depends(get_db)):
    user = await user_service.create_new_service_user(session, user)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    # new_wallet = WalletCreateDTO(balance=0.000001, reserved_balance=0.000001, currency_id=1, user_id=user.id)
    wallets = await wallet_service.create_service_wallets_for_all_currencies(session, user.id)
    logging.info(f"User id received in register_service: {user.id}")
    access_token = user_service.create_access_token(user.id)
    return {"access_token": access_token, "user_id": user.id} #wallets 

# Get service user token by login and password
@app.get("/service/auth/login")
async def service_login(username: str, password: str, session: AsyncSession = Depends(get_db)):
    user = await user_service.authenticate_service_user(session, username, password)
    if not user: # check this for False
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    logging.info(f"User id received in login: {user.id}")
    access_token = user_service.create_access_token(user.id)
    return {"access_token": access_token, "user_id": user.id}

# Update deposit transaction by service user
@app.put("/service/transaction/deposit", response_model=TransactionOutDTO)
async def update_service_deposit_transaction_status(transaction_id: uuid.UUID, new_status: str, session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_service_user)):
    exception_raised = False
    try:
        new_transaction_service = await payment_service.update_service_deposit_transaction(session, transaction_id, new_status, current_user.id)
        logging.info(f"pending_transaction in main: {new_transaction_service}")
        if isinstance(new_transaction_service, dict) and 'error' in new_transaction_service:
            text_error = new_transaction_service['error']
            logging.info(f"text_error in main: {text_error}")
            exception_raised = True
            raise HTTPException(status_code=400, detail=str(text_error))
        else:
            return new_transaction_service
    except Exception as e:
        if exception_raised:
            raise e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  

# Update withdraw transaction by service user
@app.put("/service/transaction/withdraw", response_model=TransactionOutDTO)
async def update_service_withdraw_transaction_status(transaction_id: uuid.UUID, new_status: str, session: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_service_user)):
    exception_raised = False
    try:
        new_transaction_service = await payment_service.update_service_withdraw_transaction(session, transaction_id, new_status, current_user.id)
        logging.info(f"pending_transaction in main: {new_transaction_service}")
        if isinstance(new_transaction_service, dict) and 'error' in new_transaction_service:
            text_error = new_transaction_service['error']
            logging.info(f"text_error in main: {text_error}")
            exception_raised = True
            raise HTTPException(status_code=400, detail=str(text_error))
        else:
            return new_transaction_service
    except Exception as e:
        if exception_raised:
            raise e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  


# ... next methods transactions

async def init():
    await create_tables()
    logging.info("DB structure updated")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True, lifespan="on", on_startup=[init])    


