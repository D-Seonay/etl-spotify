import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

# Optional: load a .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Adjust imports so `entity` package can be imported when running script from `scripts/`
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import Base and entities (importing entities registers them with Base metadata)
try:
    # import the package modules to ensure they are registered
    from entity.base import Base
    
    # import entities
    import entity.artist
    import entity.album
    import entity.track
    import entity.user
    import entity.history
    import entity.feat
except Exception as e:
    print("Failed importing entity modules:", e)
    raise

# Read DB config from environment
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

if DB_USER and DB_PASSWORD and DB_HOST and DB_PORT and DB_NAME:
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print("Using PostgreSQL at:", DATABASE_URL)
else:
    DATABASE_URL = f"sqlite:///{os.path.join(PROJECT_ROOT, 'dev.db')}"
    print("No full Postgres config found — falling back to SQLite at dev.db")

engine = create_engine(DATABASE_URL, echo=True)

def wait_for_db(engine, timeout=30):
    import time
    start = time.time()
    while True:
        try:
            with engine.connect() as conn:
                return True
        except Exception:
            if time.time() - start > timeout:
                return False
            time.sleep(1)

def create_all():
    try:
        # if using Postgres, wait briefly for the DB to be ready
        if DATABASE_URL.startswith('postgresql'):
            ok = wait_for_db(engine, timeout=30)
            if not ok:
                raise OperationalError("Database did not become available in time", None, None)

        Base.metadata.create_all(engine)
        print("Database tables created successfully.")
    except OperationalError as oe:
        print("Operational error during create_all:", oe)
        raise

if __name__ == '__main__':
    create_all()
