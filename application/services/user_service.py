from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from domain.models import User, Wallet
from domain.repositories.user_repository import UserRepository
from application.dtos.user_dto import UserCreateDTO, UserOutDTO, UserUpdateDTO
from decimal import Decimal

# Initialize password hashing utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create user
async def create_user(session: AsyncSession, user_dto: UserCreateDTO):
    hashed_password = pwd_context.hash(user_dto.password)
    new_user = User(username=user_dto.username, hashed_password=hashed_password, email=user_dto.email)
    session.add(new_user)
    await session.commit()
    return UserOutDTO(id=new_user.id, username=new_user.username, email=new_user.email)

# Authenticate user
async def authenticate_user(session: AsyncSession, username: str, password: str):
    user = UserRepository.get_user_by_username(session, username)
    if not user or not pwd_context.verify(password, user.hashed_password):
        return False
    return UserOutDTO(id=user.id, username=user.username, email=user.email)

# Get user by ID
async def get_user_by_id(session: AsyncSession, user_id: int):
    user = await UserRepository(session).get_user_by_id(user_id)
    if not user:
        return None
    return UserOutDTO(id=user.id, username=user.username, email=user.email)

# Update user
async def update_user(session: AsyncSession, user_id: int, user_dto: UserUpdateDTO):
    user_repo = UserRepository(session)
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        return None

    if user_dto.username:
        user.username = user_dto.username
    if user_dto.email:
        user.email = user_dto.email
    if user_dto.password:
        user.hashed_password = pwd_context.hash(user_dto.password)

    await session.commit()
    return UserOutDTO(id=user.id, username=user.username, email=user.email)

# ... More methods for update, delete, etc.
