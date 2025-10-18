# src/Config/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.Config.settings import get_settings

# Global variables to hold database objects
engine = None
SessionLocal = None
Base = declarative_base()

def init_database():
    """Initialize database engine and session factory"""
    global engine, SessionLocal
    
    settings = get_settings()
    DATABASE_URL = settings.DB_URL
    
    engine = create_engine(DATABASE_URL, pool_size = 5, max_overflow = 10, pool_timeout = 30, pool_recycle = 3600)

    with engine.connect() as connection:
        print("Database connected successfully!")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("Database engine initialized!")

def create_db_and_tables():
    """Create database tables if they don't exist"""
    if engine is None:
        raise RuntimeError("Database engine not initialized. Call init_database() first.")
    
    Base.metadata.create_all(bind=engine)
    print("Database and tables created!")

def get_db_session():
    """Dependency function to get DB session"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def close_database():
    """Close database connections gracefully"""
    global engine
    if engine:
        engine.dispose()
        print("Database connections closed!")
