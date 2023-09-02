from pydantic import BaseModel
from typing import List

class UserCreateDTO(BaseModel):
    username: str
    email: str
    password: str

class UserOutDTO(BaseModel):
    id: int

class UserListDTO(BaseModel):
    users: List[UserOutDTO]

class UserUpdateDTO(BaseModel):
    username: str = None
    
