import logging
from sqlalchemy import text, inspect
from app.db.database import engine, SessionLocal
from app.models import models

logger = logging.getLogger(__name__)

def migrate_and_init_adb_db():
    """Safely migrate database for ADB CMS integration and seed ADB state."""
    logger.info("Checking and initializing ADB CMS database schema...")
    
    # 1. Create tables if they do not exist
    models.Base.metadata.create_all(bind=engine)
    
    # 2. Check and add missing columns to documents table
    inspector = inspect(engine)
    doc_cols = [c['name'] for c in inspector.get_columns('documents')]
    
    new_doc_cols = [
        ('file_size_bytes', 'INTEGER'),
        ('sha256_hash', 'VARCHAR'),
        ('doc_category', 'VARCHAR DEFAULT "ATTACHMENT"'),
        ('doc_version', 'VARCHAR DEFAULT "1.0"'),
        ('access_status', 'VARCHAR DEFAULT "Verified"'),
        ('checksum_verified', 'BOOLEAN DEFAULT 0'),
        ('retrieval_timestamp', 'DATETIME')
    ]
    
    with engine.connect() as conn:
        for col_name, col_type in new_doc_cols:
            if col_name not in doc_cols:
                logger.info(f"Adding column '{col_name}' ({col_type}) to 'documents' table...")
                try:
                    conn.execute(text(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Could not add column {col_name}: {e}")
                    
    # 3. Ensure ADB State exists
    db = SessionLocal()
    try:
        adb_state = db.query(models.State).filter(
            (models.State.name == "ADB - Asian Development Bank") | (models.State.platform_type == "adb_cms")
        ).first()
        
        if not adb_state:
            logger.info("Seeding 'ADB - Asian Development Bank' state...")
            adb_state = models.State(
                name="ADB - Asian Development Bank",
                portal_url="https://cms.adb.org",
                platform_type="adb_cms",
                needs_login=False,
                has_captcha=False,
                status="active",
                scraper_status="working"
            )
            db.add(adb_state)
            db.commit()
            db.refresh(adb_state)
            logger.info(f"Created ADB State ID: {adb_state.id}")
        else:
            logger.info(f"ADB State exists with ID: {adb_state.id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error ensuring ADB state: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_and_init_adb_db()
