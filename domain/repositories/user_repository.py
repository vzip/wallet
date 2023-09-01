from sqlalchemy.ext.asyncio import AsyncSession
from domain.models import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create_user(self, user: User):
        self.session.add(user)
        await self.session.commit()

    async def get_user_by_id(self, user_id: int):
        return await self.session.query(User).filter(User.id == user_id).first()

    async def get_user_by_username(self, username: str):
        return await self.session.query(User).filter(User.username == username).first()

        