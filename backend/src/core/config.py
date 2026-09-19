import secrets
import os
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = Field(env="API_V1_STR")
    PROJECT_NAME: str = Field(env="PROJECT_NAME")
    # Security settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(env="TOKEN", default=30)  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = Field(env="ALGORITHM")
    
    class Config:
        env_file = ".env"
        extra = "ignore"
settings = Settings()