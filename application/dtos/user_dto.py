from pydantic import BaseModel
from typing import List

class UserCreateDTO(BaseModel):
    username: str
    email: str
    password: str

class UserOutDTO(UserCreateDTO):
    id: int
    username: str
    email: str

class UserListDTO(BaseModel):
    users: List[UserOutDTO]

class UserUpdateDTO(BaseModel):
    username: str
    email: str
    password: str
