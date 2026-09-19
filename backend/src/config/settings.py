"""
Configuration de l'application.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

# Récupère le chemin absolu du dossier racine du projet (au-dessus de 'src')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Crée le dossier logs s'il n'existe pas
os.makedirs(LOG_DIR, exist_ok=True)

class Config:
    """Configuration de base."""
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


# def setup_logging():
#     """Configure le système de logging."""
#     log_file_path = os.path.join(LOG_DIR, "diet_app.log")
#     logging.basicConfig(
#         level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
#         format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#         handlers=[
#             logging.FileHandler(log_file_path),
#             logging.StreamHandler()
#         ]
#     )

def setup_logging():
    """Configure le système de logging avec rotation des fichiers et double sortie (Console + Fichier)."""
    log_level = getattr(logging, Config.LOG_LEVEL, logging.INFO)

    # Récupérateur racine des logs
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Évite d'ajouter plusieurs handlers si la fonction est appelée plusieurs fois
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Format commun des logs (plus lisible avec le nom du module / fichier)
    formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Handler pour la console (Docker logs)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # 2. Handler pour le fichier avec ROTATION (ex: max 5 Mo par fichier, garde 3 archives)
    log_file_path = os.path.join(LOG_DIR, "diet_app.log")
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=5 * 1024 * 1024,  # 5 Mo
        backupCount=3,  # diet_app.log.1, diet_app.log.2, etc.
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.info(
        f"Système de logging initialisé. Niveau : {Config.LOG_LEVEL}"
    )