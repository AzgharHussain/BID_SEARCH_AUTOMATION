import sqlite3
import os

DB_PATH = "backend/test.db"

def deduplicate_tenders():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = OFF;")

    print("=== STARTING TENDER DEDUPLICATION ===")
    initial_count = c.execute("SELECT count(*) FROM tenders").fetchone()[0]
    print(f"Initial total tenders: {initial_count}")

    # 1. State duplicates by (state_id, lower(trim(title)))
    state_dups = c.execute('''
        SELECT state_id, lower(trim(title)), count(*), group_concat(id)
        FROM tenders
        GROUP BY state_id, lower(trim(title))
        HAVING count(*) > 1
    ''').fetchall()

    print(f"Found {len(state_dups)} duplicate state groups.")
    
    deleted_tenders = []

    for state_id, title_norm, count, id_str in state_dups:
        ids = [int(x) for x in id_str.split(",")]
        # Rank candidate ids: prioritize having emails, then docs, then lowest row_id
        ranked = []
        for row_id in ids:
            email_cnt = c.execute("SELECT count(*) FROM collaboration_emails WHERE tender_id = ?", (row_id,)).fetchone()[0]
            doc_cnt = c.execute("SELECT count(*) FROM documents WHERE tender_row_id = ?", (row_id,)).fetchone()[0]
            ranked.append((email_cnt, doc_cnt, -row_id, row_id))
        ranked.sort(reverse=True)
        primary_id = ranked[0][3]
        duplicate_ids = [r[3] for r in ranked[1:]]

        print(f"Group: State {state_id} | '{title_norm[:40]}...' -> Keeping {primary_id}, Merging duplicates {duplicate_ids}")

        for dup_id in duplicate_ids:
            # Merge documents
            dup_docs = c.execute("SELECT id, file_name FROM documents WHERE tender_row_id = ?", (dup_id,)).fetchall()
            primary_doc_names = set(r[0] for r in c.execute("SELECT file_name FROM documents WHERE tender_row_id = ?", (primary_id,)).fetchall())
            for doc_id, fname in dup_docs:
                if fname not in primary_doc_names:
                    c.execute("UPDATE documents SET tender_row_id = ? WHERE id = ?", (primary_id, doc_id))
                    primary_doc_names.add(fname)
                else:
                    c.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

            # Merge tender_keywords (columns: tender_row_id, keyword_id)
            dup_kws = c.execute("SELECT keyword_id FROM tender_keywords WHERE tender_row_id = ?", (dup_id,)).fetchall()
            primary_kws = set(r[0] for r in c.execute("SELECT keyword_id FROM tender_keywords WHERE tender_row_id = ?", (primary_id,)).fetchall())
            for (kw_id,) in dup_kws:
                if kw_id not in primary_kws:
                    c.execute("UPDATE tender_keywords SET tender_row_id = ? WHERE tender_row_id = ? AND keyword_id = ?", (primary_id, dup_id, kw_id))
                    primary_kws.add(kw_id)
                else:
                    c.execute("DELETE FROM tender_keywords WHERE tender_row_id = ? AND keyword_id = ?", (dup_id, kw_id))

            # Merge tender_collaborations
            dup_collabs = c.execute("SELECT id, partner_id FROM tender_collaborations WHERE tender_id = ?", (dup_id,)).fetchall()
            primary_collab_partners = set(r[0] for r in c.execute("SELECT partner_id FROM tender_collaborations WHERE tender_id = ?", (primary_id,)).fetchall())
            for collab_id, p_id in dup_collabs:
                if p_id not in primary_collab_partners:
                    c.execute("UPDATE tender_collaborations SET tender_id = ? WHERE id = ?", (primary_id, collab_id))
                    primary_collab_partners.add(p_id)
                else:
                    c.execute("DELETE FROM tender_collaborations WHERE id = ?", (collab_id,))

            # Merge collaboration_emails
            dup_emails = c.execute("SELECT id, partner_id FROM collaboration_emails WHERE tender_id = ?", (dup_id,)).fetchall()
            primary_email_partners = set(r[0] for r in c.execute("SELECT partner_id FROM collaboration_emails WHERE tender_id = ?", (primary_id,)).fetchall())
            for email_id, p_id in dup_emails:
                if p_id not in primary_email_partners:
                    c.execute("UPDATE collaboration_emails SET tender_id = ? WHERE id = ?", (primary_id, email_id))
                    primary_email_partners.add(p_id)
                else:
                    c.execute("DELETE FROM collaboration_emails WHERE id = ?", (email_id,))

            # Delete duplicate tender
            c.execute("DELETE FROM tenders WHERE id = ?", (dup_id,))
            deleted_tenders.append(dup_id)

    # 2. Check ADB duplicates (such as ID 983 and 1212)
    adb_tenders = c.execute("SELECT id, tender_id, title FROM tenders WHERE tender_id LIKE 'ADB-%'").fetchall()
    seen_adb_titles = {}
    for row_id, tid, title in adb_tenders:
        norm_title = " ".join(title.lower().split())
        if norm_title in seen_adb_titles:
            primary_id = seen_adb_titles[norm_title]
            dup_id = row_id
            print(f"ADB Duplicate detected: Keeping {primary_id}, Merging {dup_id} ('{norm_title[:50]}...')")

            # Merge documents
            dup_docs = c.execute("SELECT id, file_name FROM documents WHERE tender_row_id = ?", (dup_id,)).fetchall()
            primary_doc_names = set(r[0] for r in c.execute("SELECT file_name FROM documents WHERE tender_row_id = ?", (primary_id,)).fetchall())
            for doc_id, fname in dup_docs:
                if fname not in primary_doc_names:
                    c.execute("UPDATE documents SET tender_row_id = ? WHERE id = ?", (primary_id, doc_id))
                    primary_doc_names.add(fname)
                else:
                    c.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

            # Merge adb_opportunity_details
            has_primary_detail = c.execute("SELECT count(*) FROM adb_opportunity_details WHERE tender_id = ?", (primary_id,)).fetchone()[0]
            if not has_primary_detail:
                c.execute("UPDATE adb_opportunity_details SET tender_id = ? WHERE tender_id = ?", (primary_id, dup_id))
            else:
                c.execute("DELETE FROM adb_opportunity_details WHERE tender_id = ?", (dup_id,))

            # Merge adb_proposal_tracks
            has_primary_track = c.execute("SELECT count(*) FROM adb_proposal_tracks WHERE tender_id = ?", (primary_id,)).fetchone()[0]
            if not has_primary_track:
                c.execute("UPDATE adb_proposal_tracks SET tender_id = ? WHERE tender_id = ?", (primary_id, dup_id))
            else:
                c.execute("DELETE FROM adb_proposal_tracks WHERE tender_id = ?", (dup_id,))

            # Delete duplicate tender
            c.execute("DELETE FROM tenders WHERE id = ?", (dup_id,))
            deleted_tenders.append(dup_id)
        else:
            seen_adb_titles[norm_title] = row_id

    conn.commit()
    final_count = c.execute("SELECT count(*) FROM tenders").fetchone()[0]
    print(f"Successfully deleted {len(deleted_tenders)} duplicate tenders.")
    print(f"Final total tenders count: {final_count} (was {initial_count})")
    
    # Verify no duplicates remain
    remaining = c.execute('''
        SELECT state_id, lower(trim(title)), count(*)
        FROM tenders
        GROUP BY state_id, lower(trim(title))
        HAVING count(*) > 1
    ''').fetchall()
    print(f"Remaining duplicate groups: {len(remaining)}")

    conn.close()

if __name__ == "__main__":
    deduplicate_tenders()
