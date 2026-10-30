import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from app.db.database import engine, SessionLocal, Base
from app.models import models

def run_migration():
    print("Running migration for Devex Global Procurement tables...")
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)
    print("Tables created / verified successfully.")

    db = SessionLocal()
    try:
        # Check if Devex state exists
        devex_state = db.query(models.State).filter(
            (models.State.name == "Devex - Global Procurement Intelligence") | 
            (models.State.platform_type == "devex")
        ).first()

        if not devex_state:
            devex_state = models.State(
                name="Devex - Global Procurement Intelligence",
                portal_url="https://www.devex.com/funding/r",
                platform_type="devex",
                needs_login=True,
                has_captcha=False,
                status="active",
                scraper_status="business_alert_ingestion"
            )
            db.add(devex_state)
            db.commit()
            db.refresh(devex_state)
            print(f"Created Devex State row with ID: {devex_state.id}")
        else:
            print(f"Devex State row already exists with ID: {devex_state.id}")
    except Exception as e:
        print(f"Error checking/creating Devex state: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
