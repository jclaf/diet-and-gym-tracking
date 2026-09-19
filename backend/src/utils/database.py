import os
import duckdb
from dotenv import load_dotenv

load_dotenv()

# Le chemin du fichier DuckDB (pointé vers un volume persistant Docker)
DB_PATH = os.getenv("DB_PATH")


def get_db_connection():
    """Ouvre une connexion à DuckDB"""
    return duckdb.connect(DB_PATH)


def init_db():
    """Crée les tables de base si elles n'existent pas"""
    con = get_db_connection()
    con.execute("CREATE SEQUENCE IF NOT EXISTS seq_user_id START 1;")
    con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_user_id'),
                username VARCHAR UNIQUE,
                password_hash VARCHAR
            )
        """)
    con.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                age INTEGER,
                gender VARCHAR,
                height FLOAT,
                current_weight FLOAT,
                target_weight FLOAT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
    con.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY,
                date DATE,
                exercise VARCHAR,
                weight FLOAT,
                reps INTEGER
            )
        """)
    con.close()