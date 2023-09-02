from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.db.database import create_tables, get_db
from application.services import user_service, transaction_service
from application.dtos.user_dto import UserCreateDTO, UserOutDTO, UserListDTO
from application.dtos.wallet_dto import WalletCreateDTO, WalletOutDTO, WalletListDTO
from application.dtos.transaction_dto import TransactionCreateDTO, TransactionListDTO, TransactionOutDTO
from domain.repositories.user_repository import UserRepository, get_user_by_username
from domain.repositories.wallet_repository import WalletRepository
from decimal import Decimal
import logging


# Инициализация FastAPI
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init()

# Конфигурация для токенов
SECRET_KEY = "YourSecretKey"  
ALGORITHM = "HS256"

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Класс для обработки ошибок
class ErrorResponse(BaseModel):
    status: int
    message: str

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": exc.status_code, "message": exc.detail},
    )

# Проверка токена и пользователя
async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)):
    try:
        # Верифицируем токен и получаем user_id
        user_id = user_service.verify_token(token)
        
        # Проверяем, существует ли пользователь в базе данных
        current_user = await user_service.get_user_by_id(session, user_id)
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        return current_user

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

# Пользователи
@app.get("/users/me", response_model=UserOutDTO)
async def read_users_me(current_user: str = Depends(get_current_user)):
    return current_user

# Аутентификация и Регистрация
@app.post("/auth/register")
async def register(user: UserCreateDTO, session: AsyncSession = Depends(get_db)):
    user = await user_service.create_user(session, user)
    if not user: # check this for False
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = user_service.create_access_token(user.id)
    return {"access_token": access_token}

@app.post("/auth/login")
async def login(username: str, password: str, session: AsyncSession = Depends(get_db)):
    user_id = await user_service.authenticate_user(session, username, password)
    if not user_id: # check this for False
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = user_service.create_access_token(user_id)
    return {"access_token": access_token}


# Кошельки и дальнейшие методы

@app.post("/wallet/deposit", response_model=WalletOutDTO)
async def deposit_wallet(wallet_id: int, amount: Decimal, current_user: str = Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")
    try:
        return await transaction_service.deposit_funds(current_user.id, wallet_id, amount)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/wallet/transfer", response_model=WalletOutDTO)
async def transfer_funds(source_wallet_id: int, target_wallet_id: int, amount: Decimal, current_user: str = Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")
    try:
        return await transaction_service.transfer_funds(current_user.id, source_wallet_id, target_wallet_id, amount)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/wallet/withdraw", response_model=WalletOutDTO)
async def withdraw_funds(wallet_id: int, amount: Decimal, current_user: str = Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")
    try:
        return await transaction_service.withdraw_funds(current_user.id, wallet_id, amount)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# ... код для работы с кошельками и транзакциями

async def init():
    await create_tables()
    logging.info("DB structure updated")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True, lifespan="on", on_startup=[init])    


