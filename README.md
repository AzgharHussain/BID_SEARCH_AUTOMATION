# GISFY Automated Proposals — Full Intelligence & Document Extraction System

An automated procurement intelligence platform that monitors **all 29 Indian State e-Procurement Portals**, scrapes live tenders and authentic RFP/BOQ/ZIP documents, provides deep-linked state and keyword search, generates master Excel spreadsheets, and dispatches real-time email alerts.

---

## 🌟 Key Features

1. **Pan-India Coverage across 29 States**:
   - Monitored official state portals (Andhra Pradesh, Maharashtra, Delhi, Karnataka, Uttar Pradesh, Tamil Nadu, etc.).
   - Targeted GIS and technology keywords (*GIS, Remote Sensing, Drone LiDAR, Satellite Imagery, Survey, Smart City, Water Resources*).
2. **Authentic Proposal Documents**:
   - Downloads original tender documents directly (PDF notices, Technical RFPs, Financial BOQ Excel sheets, and ZIP bundles).
   - One-click direct downloads with proper attachment headers.
3. **Master Excel Spreadsheet Generation**:
   - Generates formatted `.xlsx` workbooks containing state data, keywords, tenders, deadlines, and clickable `=HYPERLINK()` download links for every attached document.
   - Available via API endpoint: `http://127.0.0.1:8000/api/reports/proposals-excel`.
   - In-browser interactive spreadsheet grid: `http://127.0.0.1:8000/api/reports/excel-view`.
4. **Automated Real-Time Email Alerts**:
   - 15-minute background monitoring daemon polls state portals for newly published tenders.
   - Instantly compiles and dispatches proposal alerts and comprehensive state digests with attached Excel workbooks.
5. **Tender-Specific Collaboration Partners & Joint Venture Engine**:
   - Searches and matches specialized collaboration partners (Consortium / Joint Venture / Subcontracting) for every tender.
   - Intelligent compatibility scoring (0-100%) based on tender RFP scope, keywords, state, department, and mandatory certifications (DGCA Drone, Maxar/Planet Satellite Imagery, MeitY GovCloud, Survey of India Class-A DGPS, CWC Water SCADA, MoHUA Smart Cities).
   - Dynamic **"Why Needed for this Tender"** and **"Synergy Scope Split"** rationale.
   - Comprehensive Partner Dossiers: company profile, annual turnover, workforce/pilot count, empanelments, and past government project track record.
   - 1-Click Joint Venture Proposal & Letter of Intent (LOI) generator with direct email dispatch.
   - Partner registration form to add verified enterprises to the database.
6. **Interactive Single-Page React Web App**:
   - Search by state, keyword, department, or reference ID.
   - "🤝 Collaboration Partners" action button on every tender card and top header.
   - Deep-linking support via query parameters (`?state=...&keyword=...&tender=...`).
   - Integrated terminal log streaming and team recipient management.

---

## 📁 Project Structure

```text
Automated Proposals/
├── backend/
│   ├── app/
│   │   ├── db/              # SQLAlchemy database engine and session
│   │   ├── models/          # Data models (State, Keyword, Tender, Document, ScrapeRun, Partner, TenderCollaboration)
│   │   ├── routers/         # API endpoints (tenders, states, keywords, reports, email, partners)
│   │   ├── services/        # Business logic:
│   │   │   ├── partner_service.py         # Tender matching engine, seed data & JV proposal generator
│   │   │   ├── email_service.py           # Email generation & SMTP dispatch
│   │   │   ├── excel_service.py           # Master .xlsx generation
│   │   │   ├── live_sync_service.py       # 15-min automated portal polling daemon
│   │   │   ├── document_service.py        # PDF & BOQ storage and extraction
│   │   │   └── pdf_compression_service.py # Large PDF optimizer
│   │   └── main.py          # FastAPI application entry point

│   ├── storage/             # Tender documents, reports, and dispatched HTML emails
│   ├── test.db              # Pre-populated SQLite database with 29 states & tenders
│   ├── team_members.json    # Registered email recipients
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment template
│   └── .env                 # Local configuration
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React application & dashboard
│   │   ├── main.jsx         # React DOM root with Error Boundary
│   │   └── index.css        # Comprehensive styling system
│   ├── public/              # Logos and static assets
│   ├── package.json         # Frontend dependencies (React 19, Vite)
│   └── vite.config.js       # Vite build configuration
├── start.sh                 # Unified 1-click startup script
└── README.md                # System documentation
```

---

## 🚀 Quick Start (Automated Launcher)

To start both the Backend (Port 8000) and Frontend (Port 5173) together:

```bash
chmod +x start.sh
./start.sh
```

The script will launch the servers and open `http://localhost:5173` in your default browser.

---

## 🛠️ Manual Setup & Execution

### 1. Backend Setup (FastAPI & Python 3.10+)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# Install required packages
pip install --upgrade pip
pip install -r requirements.txt

# Create .env from template
cp .env.example .env

# Run FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

* API Documentation: `http://127.0.0.1:8000/docs`
* Health / Status: `http://127.0.0.1:8000/api/sync/status`

### 2. Frontend Setup (React & Vite)

In a separate terminal:

```bash
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```

* Frontend Dashboard: `http://localhost:5173/`

---

## ✉️ Email Configuration (SMTP Setup)

By default, the backend operates in **local archive mode**, automatically saving all dispatched HTML emails and attachments in `backend/storage/sent_emails/` without requiring external credentials.

To enable **live inbox delivery** to Gmail or other mail services:

1. Open `backend/.env`.
2. Add your SMTP credentials:

```env
DATABASE_URL=sqlite:///./test.db

# Gmail SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # 16-character Google App Password
SMTP_FROM=GISFY Procurement System <your_email@gmail.com>
```

> **Note on Gmail App Passwords**:
> To generate an App Password: Go to your **Google Account** → **Security** → **2-Step Verification** → **App Passwords** → Name it "GISFY Proposals" → Copy the 16-character code into `SMTP_PASSWORD`.

---

## 📊 Excel Export & Document Download APIs

- **Download Master Excel (.xlsx)**:
  `GET http://127.0.0.1:8000/api/reports/proposals-excel`
- **Interactive Spreadsheet View (Browser)**:
  `GET http://127.0.0.1:8000/api/reports/excel-view`
- **Download Specific Tender Document**:
  `GET http://127.0.0.1:8000/api/documents/download?id=<DOC_ID>&attachment=true`
- **Full State-Keyword Report JSON**:
  `GET http://127.0.0.1:8000/api/reports/state-keyword`
- **View Dispatched Email Archive**:
  `GET http://127.0.0.1:8000/api/email/view/<FILENAME>`

---

## 👥 Managing Email Recipients

Team recipients are stored in `backend/team_members.json`. You can manage recipients directly from the web interface (**Email Team** button in the header) or via API:

- `GET /api/email/team-members` - List registered recipients
- `POST /api/email/team-members` - Add a new recipient (`{"email": "name@example.com", "name": "...", "role": "..."}`)
- `DELETE /api/email/team-members?email=name@example.com` - Remove a recipient

---

## 🛡️ License & Confidentiality
Confidential and proprietary to GISFY Private Limited. Developed for Automated Proposal Intelligence and Tender Automation.
