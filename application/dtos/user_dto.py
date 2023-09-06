from pydantic import BaseModel
from typing import List
import uuid

class UserCreateDTO(BaseModel):
    username: str
    email: str
    password: str

class UserOutDTO(BaseModel):
    id: uuid.UUID

class UserListDTO(BaseModel):
    users: List[UserOutDTO]

class UserUpdateDTO(BaseModel):
    username: str = None
    
