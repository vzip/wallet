from pydantic import BaseModel

class UserAuthOutDTO(BaseModel):
    username: str
    password: str
    status: int
    message: str
    