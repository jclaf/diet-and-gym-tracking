import logging
from backend.src.auth.jwt_bearer import get_current_user
from backend.src.utils.database import get_db_connection
from fastapi import APIRouter, Depends, HTTPException, status
from backend.src.models.user import User
from backend.src.core.config import settings

router = APIRouter(prefix=f"{settings.API_V1_STR}", tags=["Users & Profiles"])
logger = logging.getLogger(__name__)


@router.get("/me", response_model=User)
def read_users_me(
    current_username: str = Depends(get_current_user),
):
    """Récupère les informations de l'utilisateur connecté via son token JWT."""
    con = get_db_connection()
    try:
        user = con.execute(
            "SELECT id, username FROM users WHERE username = ?", [current_username]
        ).fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé"
            )
        return User(id=user[0], username=user[1])
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du profil /me : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")
    finally:
        con.close()