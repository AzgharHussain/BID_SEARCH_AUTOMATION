import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ap_live_downloader import APEProcurementLiveClient

client = APEProcurementLiveClient()
if client.init_session():
    cands = client.scrape_active_tender_candidates()
    print("Found active candidates:", len(cands))
    for c in cands:
        pid = c["proc_id"]
        tnum = c["tender_id"]
        det = client.get_tender_details(pid)
        if det:
            docs = client.get_attached_document_list(pid, det["indent_id"])
            doc_names = [f"{d['file_name']} ({d.get('size_mb')}MB)" for d in docs]
            dept = det.get("department", "Govt of AP")
            title = det.get("title", "")[:50]
            print(f"[{pid} / {tnum}] {dept} | {title}... | Docs ({len(docs)}): {doc_names}")
