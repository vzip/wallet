from pydantic import BaseModel, EmailStr, Field, validator
from typing import List
import re
import uuid

class UserCreateDTO(BaseModel):
    username: str = Field(..., description="Minimum 3 characters, alphanumeric and underscores only.")
    email: EmailStr
    password: str = Field(..., description=(
            "Must be at least 8 characters long, contain at least one digit, one uppercase letter, and one special character."
        ))
    
    @validator("password")
    def validate_password(cls, password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Password must contain at least one special character")
        return password
    
    @validator("username")
    def validate_username(cls, username):
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not re.match("^[a-zA-Z0-9_]+$", username):
            raise ValueError("Username can only contain alphanumeric characters and underscores")
        return username
    
class UserOutDTO(BaseModel):
    id: uuid.UUID
    

class UserListDTO(BaseModel):
    users: List[UserOutDTO]

class UserUpdateDTO(BaseModel):
    username: str = None
    
