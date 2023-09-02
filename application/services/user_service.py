
from sqlalchemy import or_
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from domain.models import User, Wallet
from domain.repositories.user_repository import UserRepository, get_user_by_username
from application.dtos.user_dto import UserCreateDTO, UserOutDTO, UserUpdateDTO
from decimal import Decimal
import jwt


# Initialize password hashing utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token configuration
SECRET_KEY = "YourSecretKey"  
ALGORITHM = "HS256"

def create_access_token(user_id: str):
    to_encode = {"sub": str(user_id)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



async def create_user(session: AsyncSession, user_dto: UserCreateDTO):
    
    # Проверка на существующего пользователя
    
    user = await get_user_by_username(session, user_dto.username)
    if user:
        return False
    
    # Если такого пользователя нет, продолжаем создание
    hashed_password = pwd_context.hash(user_dto.password)
    new_user = User(username=user_dto.username, hashed_password=hashed_password, email=user_dto.email)
    
    session.add(new_user)
    await session.flush()  # Получение ID до коммита
    await session.commit()
    
    return UserOutDTO(id=new_user.id, username=new_user.username, email=new_user.email)


# Authenticate user
async def authenticate_user(session: AsyncSession, username: str, password: str):
   
    exist_user = await get_user_by_username(session, username)
    if not exist_user or not pwd_context.verify(password, exist_user.hashed_password):
        return False
    return UserOutDTO(id=exist_user.id)

# Get user by ID
async def get_user_by_id(session: AsyncSession, user_id: int):
    user = await UserRepository(session).get_user_by_id(user_id)
    if not user:
        return None
    return UserOutDTO(id=user.id, username=user.username)

# Verify token
async def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:  # 
        return None
# ... More methods for update, delete, etc.
