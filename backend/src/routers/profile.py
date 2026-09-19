import logging
from backend.src.auth.jwt_bearer import get_current_user
from backend.src.core.config import settings 
from backend.src.utils.database import get_db_connection
from fastapi import APIRouter, Depends, HTTPException, status
from backend.src.models.user import ProfileRequest

router = APIRouter(prefix=f"{settings.API_V1_STR}/profile", tags=["Users & Profiles"])
logger = logging.getLogger(__name__)


@router.post("/")
def create_or_update_profile(profile: ProfileRequest, current_username: str = Depends(get_current_user)):
    """Crée ou met à jour le profil de l'utilisateur."""
    con = get_db_connection()
    try:
        # Vérifie si l'utilisateur existe
        user = con.execute("SELECT id FROM users WHERE username = ?", [current_username]).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
        
        user_id = user[0]
        
        # Vérifie si le profil existe déjà
        existing_profile = con.execute("SELECT * FROM user_profiles WHERE user_id = ?", [user_id]).fetchone()
        
        if existing_profile:
            # Met à jour le profil existant
            con.execute("""
                UPDATE user_profiles
                SET age = ?, gender = ?, height = ?, current_weight = ?, target_weight = ?
                WHERE user_id = ?
            """, [profile.age, profile.gender, profile.height, profile.current_weight, profile.target_weight, user_id])
        else:
            # Crée un nouveau profil
            con.execute("""
                INSERT INTO user_profiles (user_id, age, gender, height, current_weight, target_weight)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [user_id, profile.age, profile.gender, profile.height, profile.current_weight, profile.target_weight])
        con.commit()  # TRÈS IMPORTANT pour enregistrer dans DuckDB
        return {"message": "Profil enregistré avec succès !"}
    except Exception as e:
        logger.error(f"Erreur lors de la création ou de la mise à jour du profil: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erreur lors de la création ou de la mise à jour du profil.")
    finally:
        con.close()
        # return {"message": "Profil enregistré avec succès !"}

@router.get("/check/{username}")
def check_profile(username: str):
    """Vérifie si un profil utilisateur existe."""
    con = get_db_connection()
    try:
        user = con.execute("SELECT id FROM users WHERE username = ?", [username]).fetchone()
        if not user:
            return {"exists": False}
        
        user_id = user[0]
        profile = con.execute("SELECT * FROM user_profiles WHERE user_id = ?", [user_id]).fetchone()
        
        return {"exists": bool(profile)}
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du profil: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")
    finally:
        con.close()

@router.get("/{username}")
def get_profile(username: str):
    """Récupère le profil de l'utilisateur."""
    con = get_db_connection()
    try:
        user = con.execute("SELECT id FROM users WHERE username = ?", [username]).fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé.")
        
        user_id = user[0]
        profile = con.execute("SELECT * FROM user_profiles WHERE user_id = ?", [user_id]).fetchone()
        
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil non trouvé.")
        
        return {
            "age": profile[1],
            "gender": profile[2],
            "height": profile[3],
            "current_weight": profile[4],
            "target_weight": profile[5]
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du profil: {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")
    finally:
        con.close()