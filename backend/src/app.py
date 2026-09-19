from fastapi import FastAPI
from backend.src.core.config import settings
from backend.src.routers import auth, users, profile
from fastapi.middleware.cors import CORSMiddleware
import logging
from backend.src.config.settings import setup_logging
from backend.src.utils.database import get_db_connection, init_db

setup_logging()
logger = logging.getLogger(__name__)

init_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profile.router)


@app.get("/")
def root():
    return {"message": "Welcome to FastAPI JWT Auth Example"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.src.app:app", host="0.0.0.0", port=8000, reload=True)