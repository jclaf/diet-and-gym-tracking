from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
  username: str  # Indispensable pour ton système de login actuel
  is_active: bool = True


class UserCreate(UserBase):
  password: str
  full_name: Optional[str] = None


class UserInDB(UserBase):
  id: int
  hashed_password: str
  full_name: Optional[str] = None
  class Config:
    from_attributes = True  # Pydantic v2 (ou orm_mode = True si v1)


class User(UserBase):
  id: int
  full_name: Optional[str] = None

  class Config:
    from_attributes = True
    
    
class UserAuthRequest(BaseModel):
    username: str
    password: str

class ProfileRequest(BaseModel):
    username: str
    age: int
    gender: str
    height: float
    current_weight: float
    target_weight: float

class QueryResponse(BaseModel):
    response: str
    source_used: str