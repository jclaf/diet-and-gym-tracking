import logging
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from backend.src.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from backend.src.utils.security import verify_password, get_password_hash
from backend.src.models.token import Token, RefreshToken
from backend.src.core.config import settings
from backend.src.models.user import User, UserAuthRequest
from backend.src.utils.database import get_db_connection
# For demonstration purposes - in a real app, you'd use a database
# fake_users_db = {
#     "john@example.com": {
#         "id": 1,
#         "email": "john@example.com",
#         "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
#         "full_name": "John Doe",
#         "roles": ["user"],
#         "is_active": True
#     },
#     "admin@example.com": {
#         "id": 2,
#         "email": "admin@example.com",
#         "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
#         "full_name": "Admin User",
#         "roles": ["user", "admin"],
#         "is_active": True
#     }
# }
router = APIRouter(prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
logger = logging.getLogger(__name__)

@router.post("/login", response_model=Token)
def login_for_access_token(user: UserAuthRequest) -> Any:
    """
    OAuth2 compatible token login, returns an access token
    """
    con = get_db_connection()
    try:
        result = con.execute(
            "SELECT id, password_hash FROM users WHERE username = ?", [user.username]
        ).fetchone()
        if not result or not verify_password(user.password, result[1]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        profile_check = con.execute(
                        """
                            SELECT 1 FROM user_profiles up
                            JOIN users u ON up.user_id = u.id
                            WHERE u.username = ?
                        """,[user.username],
                    ).fetchone()
        has_profile = profile_check is not None
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.username,
            roles=["user"],
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(subject=user.username)
        return {
            "message": "Connexion réussie.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "has_profile": has_profile
        }
    except Exception as e:
        logger.error(f"Erreur lors de la tentative de login : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")
    finally:
        con.close()

    
@router.post("/refresh", response_model=Token)
def refresh_token(body: RefreshToken) -> Any:
    """
    Refresh token endpoint
    """
    token_str = body.refresh_token
    try:
        payload = decode_token(token_str)
        # Verify this is a refresh token
        if "token_type" not in payload or payload["token_type"] != "refresh":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        con = get_db_connection()
        try:
            user_row = con.execute(
                """
                    SELECT id, username, roles, is_active 
                    FROM users WHERE username = ?
                """,
                [username],
            ).fetchone()
            if user_row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Utilisateur non trouvé",
                )

            is_active = user_row[3] if len(user_row) > 3 else True
            if not is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur inactif"
                )

            user_roles = user_row[2] if user_row[2] else ["user"]

            access_token_expires = timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            access_token = create_access_token(
                subject=username, roles=user_roles, expires_delta=access_token_expires
            )
            new_refresh_token = create_refresh_token(subject=username)

            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
            }
        finally:
            con.close()
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserAuthRequest):
    """Enregistre un nouvel utilisateur avec un mot de passe haché."""
    hashed_password = get_password_hash(user.password)
    con = get_db_connection()
    try:
        con.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            [user.username, hashed_password],
        )
        con.commit()  # Important pour valider l'insertion dans DuckDB/SQLite
        return {"message": "Utilisateur enregistré avec succès."}
    except Exception as e:
        logger.error(f"Erreur d'enregistrement: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nom d'utilisateur déjà utilisé ou erreur de données.",
        )
    finally:
        con.close()

# @app.post("/api/login")
# def login_user(user: UserAuthRequest):
#     """Vérifie les informations d'identification de l'utilisateur."""
#     con = get_db_connection()
#     try:
#         result = con.execute("SELECT password_hash FROM users WHERE username = ?", [user.username]).fetchone()
#         if result and pwd_context.verify(user.password, result[0]):
#             profile_check = con.execute(
#                 """
#                     SELECT 1 FROM user_profiles up
#                     JOIN users u ON up.user_id = u.id
#                     WHERE u.username = ?
#                 """,[user.username],
#             ).fetchone()
#             return {"message": "Connexion réussie.", "has_profile": profile_check is not None}
#         else:
#             raise HTTPException(status_code=401, detail="Nom d'utilisateur ou mot de passe incorrect.")
#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         logger.error(f"Erreur lors de la connexion de l'utilisateur: {e}")
#         raise HTTPException(status_code=500, detail="Erreur interne du serveur.")
#     finally:
#         con.close()
