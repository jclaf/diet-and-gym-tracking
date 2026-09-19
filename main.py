import logging
from config.settings import setup_logging

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from io import BytesIO
# from pypdf import PdfReader
import os
from database import get_db_connection, init_db
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

# from utils.api_call import call_rag_openrouter

setup_logging()
logger = logging.getLogger(__name__)

init_db()

app = FastAPI(title="Fitness App", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🔒 Configuration de Passlib avec Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DOCS_DIR = os.path.join(BASE_DIR, "docs")

# class QueryRequest(BaseModel):
#     query: str
#     api_key: str | None = None
#     file_name: str | None = Form(None)
#     file: UploadFile | None = File(None)  # Nom du fichier à utiliser comme contexte, si fourni
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

@app.get("/")
def read_root() -> dict[str, str]:
    """Point d'entrée racine de l'API."""
    return {"message": "Bienvenue sur l'API de l'Application de Suivi Alimentaire et d'Entretien !"}

@app.post("/api/register")
def register_user(user: UserAuthRequest):  
    """Enregistre un nouvel utilisateur avec un mot de passe haché."""
    hashed_password = pwd_context.hash(user.password)
    con = get_db_connection()
    try:
        con.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", [user.username, hashed_password])
        return {"message": "Utilisateur enregistré avec succès."}
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'utilisateur: {e}")
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà utilisé.")
    finally:
        con.close()

@app.post("/api/login")
def login_user(user: UserAuthRequest):
    """Vérifie les informations d'identification de l'utilisateur."""
    con = get_db_connection()
    try:
        result = con.execute("SELECT password_hash FROM users WHERE username = ?", [user.username]).fetchone()
        if result and pwd_context.verify(user.password, result[0]):
            profile_check = con.execute(
                """
                    SELECT 1 FROM user_profiles up
                    JOIN users u ON up.user_id = u.id
                    WHERE u.username = ?
                """,[user.username],
            ).fetchone()
            return {"message": "Connexion réussie.", "has_profile": profile_check is not None}
        else:
            raise HTTPException(status_code=401, detail="Nom d'utilisateur ou mot de passe incorrect.")
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Erreur lors de la connexion de l'utilisateur: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")
    finally:
        con.close()

@app.post("/api/profile")
def create_or_update_profile(profile: ProfileRequest):
    """Crée ou met à jour le profil de l'utilisateur."""
    con = get_db_connection()
    try:
        # Vérifie si l'utilisateur existe
        user = con.execute("SELECT id FROM users WHERE username = ?", [profile.username]).fetchone()
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
    except Exception as e:
        logger.error(f"Erreur lors de la création ou de la mise à jour du profil: {e}")
        raise HTTPException(status_code=400, detail="Erreur lors de la création ou de la mise à jour du profil.")
    finally:
        con.close()
        return {"message": "Profil enregistré avec succès !"}

@app.get("/api/profile/check/{username}")
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
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")
    finally:
        con.close()

@app.get("/api/profile/{username}")
def get_profile(username: str):
    """Récupère le profil de l'utilisateur."""
    con = get_db_connection()
    try:
        user = con.execute("SELECT id FROM users WHERE username = ?", [username]).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
        
        user_id = user[0]
        profile = con.execute("SELECT * FROM user_profiles WHERE user_id = ?", [user_id]).fetchone()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profil non trouvé.")
        
        return {
            "age": profile[1],
            "gender": profile[2],
            "height": profile[3],
            "current_weight": profile[4],
            "target_weight": profile[5]
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du profil: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")
    finally:
        con.close()

@app.post("/ask", response_model=QueryResponse)
async def ask_rag():
   pass 


