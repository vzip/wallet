from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from domain.models import User, ServiceUser
from sqlalchemy import select
import uuid
import logging

logging.basicConfig(level=logging.INFO)

    
async def create_user(session: AsyncSession, user_dto, hashed_password):
        try:
            logging.info(f"User name received to repository: {user_dto.username}")
            new_user = User(username=user_dto.username, hashed_password=hashed_password, email=user_dto.email)
            session.add(new_user)
            await session.flush()  # Getting ID befoe commit
            await session.commit()
            return new_user
        except SQLAlchemyError as e:
            #raise e  # 
            return {"error": str(e)}

async def create_service_user(session: AsyncSession, user_dto, hashed_password):
        try:
            logging.info(f"User name received to repository: {user_dto.username}")
            new_user = ServiceUser(username=user_dto.username, hashed_password=hashed_password, email=user_dto.email)
            session.add(new_user)
            await session.flush()  # Getting ID befoe commit
            await session.commit()
            return new_user
        except SQLAlchemyError as e:
            raise e  #         

    
async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID):
        try:
            logging.info(f"User_id received to repository: {user_id}")
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return user        
        except SQLAlchemyError as e:
            raise e  # 

async def get_service_user_by_id(session: AsyncSession, user_id: uuid.UUID):
        try:
            logging.info(f"User_id received to repository: {user_id}")
            stmt = select(ServiceUser).where(ServiceUser.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return user        
        except SQLAlchemyError as e:
            raise e  #         
        
async def get_user_by_username(session: AsyncSession, username: str):
    try:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user        
    except SQLAlchemyError as e:
            raise e  # 
    
async def get_service_user_by_username(session: AsyncSession, username: str):
    try:
        stmt = select(ServiceUser).where(ServiceUser.username == username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user        
    except SQLAlchemyError as e:
            raise e  # 