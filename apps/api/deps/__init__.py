from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings  # wherever your DB settings live

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_engine():
    return engine
