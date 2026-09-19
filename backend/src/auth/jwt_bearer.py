from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from typing import Optional, List
from backend.src.models.token import TokenPayload, TokenData
from backend.src.core.config import settings
from backend.src.auth.jwt_handler import decode_token
from datetime import datetime, timezone

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Validates token and returns the username
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
        token_data = TokenPayload(**payload)
        # Check token expiration
        if token_data.exp:
            if datetime.fromtimestamp(token_data.exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expiré",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        return token_data.sub
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de valider les identifiants",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
def get_current_user_with_roles(
    required_roles: Optional[List[str]] = None
) -> callable:
    """
    Creates a dependency that checks if the current user has the required roles
    """
    if required_roles is None:
        required_roles = []
    def _inner(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        token = credentials.credentials
        try:
            payload = decode_token(token)
            token_data = TokenPayload(**payload)
            # Check token expiration
            if token_data.exp:
                if datetime.fromtimestamp(token_data.exp, tz=timezone.utc) < datetime.now(timezone.utc):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token expiré",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            # If no specific roles required, just authentication is enough
            if not required_roles:
                return token_data.sub
            # Check if user has at least one of the required roles
            user_roles = set(token_data.roles)
            if not any(role in user_roles for role in required_roles) and "admin" not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permissions insuffisantes",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return token_data.sub
        except (JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Impossible de valider les identifiants",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return _inner