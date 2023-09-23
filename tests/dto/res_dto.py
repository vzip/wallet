from pydantic import BaseModel

class UserAuthOutDTO(BaseModel):
    username: str
    password: str
    status: str
    message: str
    