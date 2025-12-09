"""
Database setup and configuration with connection pooling
"""
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ainfluencer.db")

# Connection pool configuration
POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "20"))
MAX_OVERFLOW = int(os.getenv("MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("POOL_RECYCLE", "3600"))  # 1 hour

# Create engine with connection pooling
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
        pool_pre_ping=True  # Verify connections before using
    )
else:
    # PostgreSQL with connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=True,  # Verify connections before using
        echo=False
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata
metadata = MetaData()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database (create tables and indexes)"""
    Base.metadata.create_all(bind=engine)
    migrate_character_table()
    create_indexes()

def migrate_character_table():
    """Migrate Character table to add new Character Management System fields"""
    from sqlalchemy import inspect, text
    from sqlalchemy.exc import OperationalError
    
    try:
        inspector = inspect(engine)
        if 'characters' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('characters')]
            
            # Add new columns if they don't exist
            with engine.connect() as conn:
                if 'age' not in columns:
                    conn.execute(text("ALTER TABLE characters ADD COLUMN age INTEGER"))
                    logger.info("Added 'age' column to characters table")
                
                if 'persona' not in columns:
                    conn.execute(text("ALTER TABLE characters ADD COLUMN persona JSON DEFAULT '{}'"))
                    logger.info("Added 'persona' column to characters table")
                
                if 'appearance' not in columns:
                    conn.execute(text("ALTER TABLE characters ADD COLUMN appearance JSON DEFAULT '{}'"))
                    logger.info("Added 'appearance' column to characters table")
                
                if 'style' not in columns:
                    conn.execute(text("ALTER TABLE characters ADD COLUMN style JSON DEFAULT '{}'"))
                    logger.info("Added 'style' column to characters table")
                
                if 'content_preferences' not in columns:
                    conn.execute(text("ALTER TABLE characters ADD COLUMN content_preferences JSON DEFAULT '{}'"))
                    logger.info("Added 'content_preferences' column to characters table")
                
                if 'consistency_rules' not in columns:
                    conn.execute(text("ALTER TABLE characters ADD COLUMN consistency_rules JSON DEFAULT '{}'"))
                    logger.info("Added 'consistency_rules' column to characters table")
                
                conn.commit()
    except OperationalError as e:
        # Table might not exist yet, which is fine - create_all will handle it
        if "no such table" not in str(e).lower():
            logger.warning(f"Migration warning: {e}")
    except Exception as e:
        logger.warning(f"Migration error (non-critical): {e}")

def create_indexes():
    """Create database indexes for performance optimization"""
    from sqlalchemy import text, Index
    
    # Only create indexes if using PostgreSQL
    if not DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                # Indexes for media_items table
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_media_character_id 
                    ON media_items(character_id) 
                    WHERE deleted_at IS NULL
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_media_created_at 
                    ON media_items(created_at DESC) 
                    WHERE deleted_at IS NULL
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_media_type 
                    ON media_items(type) 
                    WHERE deleted_at IS NULL
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_media_status 
                    ON media_items(source) 
                    WHERE deleted_at IS NULL
                """))
                
                # Indexes for generation_jobs table
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_jobs_status 
                    ON generation_jobs(status)
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_jobs_character_id 
                    ON generation_jobs(character_id) 
                    WHERE character_id IS NOT NULL
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_jobs_created_at 
                    ON generation_jobs(created_at DESC)
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_jobs_type 
                    ON generation_jobs(type)
                """))
                
                # Indexes for characters table
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_characters_deleted 
                    ON characters(deleted_at) 
                    WHERE deleted_at IS NULL
                """))
                
                # Indexes for face_references table
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_face_refs_character 
                    ON face_references(character_id) 
                    WHERE deleted_at IS NULL
                """))
                
                # Indexes for detection_tests table
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_detection_media_id 
                    ON detection_tests(media_id)
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_detection_created_at 
                    ON detection_tests(created_at DESC)
                """))
                
                conn.commit()
                logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
            # Continue without indexes for SQLite
