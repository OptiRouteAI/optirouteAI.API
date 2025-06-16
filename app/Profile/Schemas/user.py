from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    username: str
    password: str
