import sqlite3
import os

DB_PATH = 'backend/test.db'

def deduplicate_tenders():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Enable foreign keys
    c.execute("PRAGMA foreign_keys = OFF")

    # Find duplicate groups by (state_id, title)
    c.execute("""
        SELECT state_id, title, count(*)
        FROM tenders
        GROUP BY state_id, title
        HAVING count(*) > 1
    """)
    dup_groups = c.fetchall()
    print(f"Found {len(dup_groups)} duplicate title groups in database.")

    total_deleted = 0
    total_docs_reassigned = 0
    total_docs_deleted = 0

    for state_id, title, cnt in dup_groups:
        # Fetch tenders in this group ordered by number of downloaded docs desc, total docs desc, id asc
        c.execute("""
            SELECT t.id, t.tender_id,
                   (SELECT count(*) FROM documents d WHERE d.tender_row_id = t.id AND d.download_status = 'downloaded') as dl_count,
                   (SELECT count(*) FROM documents d WHERE d.tender_row_id = t.id) as doc_count
            FROM tenders t
            WHERE t.state_id = ? AND t.title = ?
            ORDER BY dl_count DESC, doc_count DESC, t.id ASC
        """, (state_id, title))
        tenders = c.fetchall()
        canonical = tenders[0]
        canonical_id = canonical[0]
        duplicates = tenders[1:]

        # Get existing document file_names and keywords for canonical
        c.execute("SELECT file_name FROM documents WHERE tender_row_id = ?", (canonical_id,))
        canonical_files = set(r[0] for r in c.fetchall())

        c.execute("SELECT keyword_id FROM tender_keywords WHERE tender_row_id = ?", (canonical_id,))
        canonical_kws = set(r[0] for r in c.fetchall())

        for dup in duplicates:
            dup_id = dup[0]

            # 1. Documents
            c.execute("SELECT id, file_name FROM documents WHERE tender_row_id = ?", (dup_id,))
            dup_docs = c.fetchall()
            for doc_id, fn in dup_docs:
                if fn in canonical_files:
                    c.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                    total_docs_deleted += 1
                else:
                    c.execute("UPDATE documents SET tender_row_id = ? WHERE id = ?", (canonical_id, doc_id))
                    canonical_files.add(fn)
                    total_docs_reassigned += 1

            # 2. Keywords
            c.execute("SELECT keyword_id FROM tender_keywords WHERE tender_row_id = ?", (dup_id,))
            dup_kws = c.fetchall()
            for kw_row in dup_kws:
                kw_id = kw_row[0]
                if kw_id not in canonical_kws:
                    c.execute("INSERT INTO tender_keywords (tender_row_id, keyword_id) VALUES (?, ?)", (canonical_id, kw_id))
                    canonical_kws.add(kw_id)
            c.execute("DELETE FROM tender_keywords WHERE tender_row_id = ?", (dup_id,))

            # 3. Tender collaborations
            c.execute("SELECT id, partner_id FROM tender_collaborations WHERE tender_id = ?", (dup_id,))
            for tc_id, pid in c.fetchall():
                c.execute("SELECT id FROM tender_collaborations WHERE tender_id = ? AND partner_id = ?", (canonical_id, pid))
                if c.fetchone():
                    c.execute("DELETE FROM tender_collaborations WHERE id = ?", (tc_id,))
                else:
                    c.execute("UPDATE tender_collaborations SET tender_id = ? WHERE id = ?", (canonical_id, tc_id))

            # 4. Collaboration emails
            c.execute("SELECT id, partner_id FROM collaboration_emails WHERE tender_id = ?", (dup_id,))
            for ce_id, pid in c.fetchall():
                c.execute("SELECT id FROM collaboration_emails WHERE tender_id = ? AND partner_id = ?", (canonical_id, pid))
                if c.fetchone():
                    c.execute("DELETE FROM collaboration_emails WHERE id = ?", (ce_id,))
                else:
                    c.execute("UPDATE collaboration_emails SET tender_id = ? WHERE id = ?", (canonical_id, ce_id))

            # 5. ADB tables
            c.execute("SELECT id FROM adb_opportunity_details WHERE tender_id = ?", (canonical_id,))
            if c.fetchone():
                c.execute("DELETE FROM adb_opportunity_details WHERE tender_id = ?", (dup_id,))
            else:
                c.execute("UPDATE adb_opportunity_details SET tender_id = ? WHERE tender_id = ?", (canonical_id, dup_id))

            c.execute("SELECT id FROM adb_proposal_tracks WHERE tender_id = ?", (canonical_id,))
            if c.fetchone():
                c.execute("DELETE FROM adb_proposal_tracks WHERE tender_id = ?", (dup_id,))
            else:
                c.execute("UPDATE adb_proposal_tracks SET tender_id = ? WHERE tender_id = ?", (canonical_id, dup_id))

            # Delete the duplicate tender
            c.execute("DELETE FROM tenders WHERE id = ?", (dup_id,))
            total_deleted += 1

    conn.commit()

    # Re-enable foreign keys and check integrity
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA foreign_key_check")
    fk_errors = c.fetchall()
    print("Foreign key check errors:", fk_errors)

    # Verification: check remaining duplicate titles
    c.execute("""
        SELECT state_id, title, count(*)
        FROM tenders
        GROUP BY state_id, title
        HAVING count(*) > 1
    """)
    remaining = c.fetchall()
    print(f"Remaining duplicate groups: {len(remaining)}")

    c.execute("SELECT count(*) FROM tenders")
    total_tenders = c.fetchone()[0]
    print(f"Total tenders remaining in database: {total_tenders}")
    print(f"Total duplicate tenders removed: {total_deleted}")
    print(f"Total documents reassigned: {total_docs_reassigned}, deleted: {total_docs_deleted}")

    conn.close()

if __name__ == '__main__':
    deduplicate_tenders()
