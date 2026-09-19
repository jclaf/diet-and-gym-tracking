from datetime import datetime, timedelta, timezone
from backend.src.core.config import settings  # Contient SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from jose import jwt
from passlib.context import CryptContext

from typing import Optional

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
  return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
  return pwd_context.hash(password)


def create_access_token(
    subject: str, expires_delta: Optional[timedelta] = None
) -> str:
  """Crée un jeton d'accès JWT avec un timestamp UTC conscient."""
  if expires_delta:
    expire = datetime.now(timezone.utc) + expires_delta
  else:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

  to_encode = {
      "sub": str(subject),
      "exp": expire,
      "iat": datetime.now(timezone.utc),
  }

  return jwt.encode(
      to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
  )