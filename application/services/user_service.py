
from sqlalchemy import or_
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from domain.models import User, Wallet
from domain.repositories.user_repository import get_user_by_id, get_user_by_username, create_user, get_service_user_by_username, create_service_user, get_service_user_by_id
from application.dtos.user_dto import UserCreateDTO, UserOutDTO, UserUpdateDTO
from decimal import Decimal
import jwt
import uuid
import logging

logging.basicConfig(level=logging.INFO)

# Initialize password hashing utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token configuration
SECRET_KEY = "YourSecretKey"  
ALGORITHM = "HS256"

def create_access_token(user_id: uuid.UUID):
    logging.info(f"Create Token, user_id recieved to service: {user_id}")
    to_encode = {"sub": str(user_id)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def create_new_user(session: AsyncSession, user_dto: UserCreateDTO):

    # Check user exist
    user = await get_user_by_username(session, user_dto.username)
    if user:
        return False
    # If not exist, continue create new
    hashed_password = pwd_context.hash(user_dto.password)

    new_user = await create_user(session, user_dto, hashed_password)
    if not new_user:
        return None
    return UserOutDTO(id=new_user.id, username=new_user.username, email=new_user.email)


async def create_new_service_user(session: AsyncSession, user_dto: UserCreateDTO):

    # Check user exist
    user = await get_service_user_by_username(session, user_dto.username)
    if user:
        return False
    # If not exist, continue create new
    hashed_password = pwd_context.hash(user_dto.password)

    new_user = await create_service_user(session, user_dto, hashed_password)
    if not new_user:
        return None
    return UserOutDTO(id=new_user.id, username=new_user.username, email=new_user.email)


# Authenticate user
async def authenticate_user(session: AsyncSession, username: str, password: str):
   
    exist_user = await get_user_by_username(session, username)
    if not exist_user or not pwd_context.verify(password, exist_user.hashed_password):
        return False
    return UserOutDTO(id=exist_user.id)

# Get user by ID
async def get_user_by_id_from_token(session: AsyncSession, user_id: uuid.UUID):
    user = await get_user_by_id(session, user_id)
    if not user:
        return None
    return UserOutDTO(id=user.id, username=user.username)

# Get service user by ID
async def get_service_user_by_id_from_token(session: AsyncSession, user_id: uuid.UUID):
    user = await get_service_user_by_id(session, user_id)
    if not user:
        return None
    return UserOutDTO(id=user.id, username=user.username)

# Verify token
async def verify_token(token: str):
    if token.startswith("Bearer "):
        token = token[7:]  # Cut 'Bearer '
    try:
        logging.info(f"Token received to sevice: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM) # []
        user_id = payload.get("sub")
        logging.info(f"User_id extract from token: {user_id}")
        if user_id is None:
            return None
        user_id_int = uuid.UUID(user_id)
        return user_id_int
    except jwt.ExpiredSignatureError as jE:
        logging.info(f"ExpiredSignatureError: {jE}")
        return None
    except jwt.InvalidTokenError as jI:  # 
        logging.info(f"InvalidTokenErro: {jI}")
        return None
# ... More methods for update, delete, etc.
