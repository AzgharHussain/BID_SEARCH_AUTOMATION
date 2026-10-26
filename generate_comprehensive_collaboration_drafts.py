import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.db.database import SessionLocal
from app.models import models
from app.services.collaboration_email_service import collaboration_email_service

def generate_all_drafts():
    db = SessionLocal()
    try:
        states = db.query(models.State).order_by(models.State.name.asc()).all()
        print(f"=== GENERATING COLLABORATION DRAFTS ACROSS ALL {len(states)} STATES & ADB ===")

        total_created = 0

        for st in states:
            is_adb = "ADB" in st.name
            t_limit = 12 if is_adb else 4
            
            # Select active/new tenders for this state
            tenders = (
                db.query(models.Tender)
                .filter(models.Tender.state_id == st.id, models.Tender.status.in_(["active", "new"]))
                .order_by(models.Tender.last_date.desc(), models.Tender.id.asc())
                .limit(t_limit)
                .all()
            )
            if not tenders:
                tenders = (
                    db.query(models.Tender)
                    .filter(models.Tender.state_id == st.id)
                    .order_by(models.Tender.id.asc())
                    .limit(3)
                    .all()
                )

            state_drafts = 0
            for tender in tenders:
                # Generate drafts for top recommended partners for this tender
                max_p = 3 if is_adb else 2
                drafts = collaboration_email_service.generate_drafts_for_tender(
                    db=db,
                    tender_id=tender.id,
                    min_match_score=70.0,
                    max_partners_per_tender=max_p
                )
                state_drafts += len(drafts)
                total_created += len(drafts)

            print(f"[{st.name}] Analyzed {len(tenders)} proposals -> Created {state_drafts} new collaboration drafts.")

        print(f"\n=== FINISHED: Created {total_created} new drafts. ===")
        total_in_db = db.query(models.CollaborationEmail).count()
        print(f"Total collaboration emails in database: {total_in_db}")

    finally:
        db.close()

if __name__ == "__main__":
    generate_all_drafts()
