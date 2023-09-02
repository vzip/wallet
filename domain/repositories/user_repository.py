from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from domain.models import User
from sqlalchemy import select


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create_user(self, user: User):
        try:
            self.session.add(user)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e  # 


    async def get_user_by_username(session: AsyncSession, username: str):
        try:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return user        
        except SQLAlchemyError as e:
                raise e  # 
    
async def get_user_by_id(session: AsyncSession, user_id: int):
        try:
            stmt = select(User).where(User.id == user_id)
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