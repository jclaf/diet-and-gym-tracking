from pydantic import BaseModel
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    message: Optional[str] = None
    has_profile: Optional[bool] = None
    
class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    roles: List[str] = []
    
class TokenData(BaseModel):
    username: Optional[str] = None
    roles: List[str] = ["user"]
    
class RefreshToken(BaseModel):
    refresh_token : str