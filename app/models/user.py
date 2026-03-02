from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserInDB(BaseModel):
    username:      str
    hashed_password: str
    is_active:     bool = True


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int  # seconds


class TokenData(BaseModel):
    username: Optional[str] = None