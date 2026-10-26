import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.models import State, Tender, CollaborationEmail, Partner
from app.services.collaboration_email_service import collaboration_email_service

def run_pipeline():
    db = SessionLocal()
    try:
        # Verify partners count
        partners_count = db.query(Partner).count()
        print(f"Total verified genuine partners in DB: {partners_count}")
        assert partners_count >= 100, f"Expected at least 100 partners, found {partners_count}"

        # Select candidate tenders across all 29 states and ADB
        states = db.query(State).order_by(State.name.asc()).all()
        selected_tenders = []
        for st in states:
            t_limit = 100 if 'ADB' in st.name else 10
            state_tenders = (
                db.query(Tender)
                .filter(Tender.state_id == st.id, Tender.status.in_(["active", "new"]))
                .order_by(Tender.last_date.desc(), Tender.id.asc())
                .limit(t_limit)
                .all()
            )
            if not state_tenders:
                state_tenders = (
                    db.query(Tender)
                    .filter(Tender.state_id == st.id)
                    .order_by(Tender.id.asc())
                    .limit(10)
                    .all()
                )
            selected_tenders.extend(state_tenders)

        print(f"Selected {len(selected_tenders)} candidate tenders across {len(states)} states & ADB.")

        total_created = 0
        total_skipped = 0

        for idx, tender in enumerate(selected_tenders, 1):
            # Check how many drafts already exist for this tender
            existing_count = db.query(CollaborationEmail).filter(CollaborationEmail.tender_id == tender.id).count()
            if existing_count >= 10:
                total_skipped += existing_count
                continue

            # Generate drafts with top 10 genuine partner matches
            new_drafts = collaboration_email_service.generate_drafts_for_tender(
                db=db,
                tender_id=tender.id,
                min_match_score=40.0,
                max_partners_per_tender=10
            )

            # If still less than 10, try with min_match_score=0.0 to fill all 10 slots
            curr_count = db.query(CollaborationEmail).filter(CollaborationEmail.tender_id == tender.id).count()
            if curr_count < 10:
                extra_drafts = collaboration_email_service.generate_drafts_for_tender(
                    db=db,
                    tender_id=tender.id,
                    min_match_score=0.0,
                    max_partners_per_tender=10
                )
                new_drafts.extend(extra_drafts)

            total_created += len(new_drafts)
            if idx % 25 == 0 or idx == len(selected_tenders):
                current_total = db.query(CollaborationEmail).count()
                print(f"Progress: [{idx}/{len(selected_tenders)}] tenders processed. Current total drafts in DB: {current_total}")

        final_drafts_count = db.query(CollaborationEmail).count()
        print(f"\n==========================================")
        print(f"SUCCESS: Pipeline generation complete!")
        print(f"Total Genuine Partners: {partners_count}")
        print(f"Total Outreach Drafts in DB: {final_drafts_count}")
        print(f"==========================================")

    finally:
        db.close()

if __name__ == "__main__":
    run_pipeline()
