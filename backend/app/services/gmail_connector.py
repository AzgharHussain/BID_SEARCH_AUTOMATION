import os
import json
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_DIR = Path(__file__).resolve().parent.parent.parent / ".gmail_credentials"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
TOKEN_PATH = CREDENTIALS_DIR / "token.json"
CLIENT_CONFIG_PATH = CREDENTIALS_DIR / "client_secret.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly"
]

class GmailConnector:
    def __init__(self):
        self.service = None
        self.auth_type = "none"
        self._initialize_credentials()

    def _initialize_credentials(self):
        """Initialize Google OAuth2 service or fallback to SMTP."""
        # 1. Try Google OAuth credentials
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            creds = None
            if TOKEN_PATH.exists():
                try:
                    with open(TOKEN_PATH, "r") as tf:
                        token_data = json.load(tf)
                    creds = Credentials.from_authorized_user_info(token_data, SCOPES)
                except Exception as e:
                    print(f"Error loading token.json: {e}")

            # Refresh token if expired
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    with open(TOKEN_PATH, "w") as tf:
                        tf.write(creds.to_json())
                except Exception as e:
                    print(f"Error refreshing OAuth token: {e}")
                    creds = None

            if creds and creds.valid:
                self.service = build("gmail", "v1", credentials=creds)
                self.auth_type = "OAuth2"
                return
        except Exception as e:
            print(f"OAuth initialization note: {e}")

        # 2. Check environment variable credentials
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")

        if client_id and client_secret and refresh_token:
            try:
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                from googleapiclient.discovery import build

                creds = Credentials(
                    token=None,
                    refresh_token=refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=SCOPES
                )
                creds.refresh(Request())
                self.service = build("gmail", "v1", credentials=creds)
                self.auth_type = "OAuth2"
                return
            except Exception as e:
                print(f"Error initializing from env OAuth: {e}")

        # 3. Check SMTP Fallback (support both SMTP_* and EMAIL_HOST_*)
        smtp_user = os.getenv("SMTP_USER") or os.getenv("EMAIL_HOST_USER") or os.getenv("GMAIL_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_HOST_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
        if smtp_user and smtp_pass:
            self.auth_type = "SMTP"
        else:
            self.auth_type = "DraftModeOnly"

    def get_status(self) -> Dict[str, Any]:
        """Return secure status without revealing passwords or access tokens."""
        sender_email = (
            os.getenv("SMTP_FROM") or
            os.getenv("GMAIL_SENDER_EMAIL") or 
            os.getenv("EMAIL_HOST_USER") or 
            "GISFY Support <support@gisfy.co.in>"
        )
        return {
            "is_connected": self.auth_type in ["OAuth2", "SMTP"],
            "auth_type": self.auth_type,
            "sender_email": sender_email,
            "cc_email": "bidding@gisfy.co.in",
            "has_oauth": self.auth_type == "OAuth2",
            "has_smtp": self.auth_type == "SMTP",
            "draft_storage_available": True,
            "token_file_present": TOKEN_PATH.exists(),
            "client_config_present": CLIENT_CONFIG_PATH.exists()
        }

    def save_client_config(self, client_id: str, client_secret: str, redirect_uri: Optional[str] = None):
        """Safely save OAuth2 client credentials."""
        data = {
            "installed": {
                "client_id": client_id.strip(),
                "client_secret": client_secret.strip(),
                "redirect_uris": [redirect_uri or "urn:ietf:wg:oauth:2.0:oob", "http://localhost:8000/api/collaboration/oauth/callback"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        with open(CLIENT_CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)
        os.chmod(CLIENT_CONFIG_PATH, 0o600)
        self._initialize_credentials()
        return {"status": "success", "message": "Client secret saved securely."}

    def save_refresh_token(self, refresh_token: str, sender_email: Optional[str] = None):
        """Save authorized refresh token."""
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if CLIENT_CONFIG_PATH.exists():
            with open(CLIENT_CONFIG_PATH, "r") as f:
                cf = json.load(f)
                client_id = cf.get("installed", {}).get("client_id", client_id)
                client_secret = cf.get("installed", {}).get("client_secret", client_secret)

        token_data = {
            "refresh_token": refresh_token.strip(),
            "client_id": client_id,
            "client_secret": client_secret,
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": SCOPES
        }
        with open(TOKEN_PATH, "w") as f:
            json.dump(token_data, f, indent=2)
        os.chmod(TOKEN_PATH, 0o600)
        self._initialize_credentials()
        return {"status": "success", "message": "OAuth credentials linked successfully."}

    def create_draft(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        sender_email: Optional[str] = None,
        cc_email: Optional[str] = "bidding@gisfy.co.in"
    ) -> Dict[str, Any]:
        """
        Create an email draft in authorized Gmail account.
        Requirement 9: Start in draft-only mode.
        """
        from_email = sender_email or os.getenv("SMTP_FROM") or os.getenv("GMAIL_SENDER_EMAIL") or "support@gisfy.co.in"
        from_header = from_email if "<" in from_email else f"GISFY Support <{from_email}>"

        msg = MIMEMultipart("alternative")
        msg["To"] = to_email
        msg["From"] = from_header
        if cc_email:
            msg["Cc"] = cc_email
        msg["Subject"] = subject
        msg["Reply-To"] = "support@gisfy.co.in"

        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        if self.service and self.auth_type == "OAuth2":
            try:
                draft = self.service.users().drafts().create(
                    userId="me",
                    body={"message": {"raw": raw_message}}
                ).execute()
                return {
                    "success": True,
                    "draft_id": draft.get("id"),
                    "message_id": draft.get("message", {}).get("id"),
                    "channel": "Gmail API (Official OAuth Draft)"
                }
            except Exception as e:
                print(f"Gmail API Draft Error: {e}")

        # Fallback local draft storage (when Gmail OAuth pending user credentials)
        local_draft_id = f"local_draft_{int(datetime.utcnow().timestamp())}"
        return {
            "success": True,
            "draft_id": local_draft_id,
            "message_id": None,
            "channel": "Local Database Draft (Awaiting User Send Authorization)"
        }

    def send_message(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        draft_id: Optional[str] = None,
        sender_email: Optional[str] = None,
        cc_email: Optional[str] = "bidding@gisfy.co.in"
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Send an email via authorized Gmail API or secure SMTP.
        Returns: (success, message_id, thread_id, error_message)
        """
        from_email = sender_email or os.getenv("SMTP_FROM") or os.getenv("GMAIL_SENDER_EMAIL") or "support@gisfy.co.in"
        from_header = from_email if "<" in from_email else f"GISFY Support <{from_email}>"

        msg = MIMEMultipart("alternative")
        msg["To"] = to_email
        msg["From"] = from_header
        if cc_email:
            msg["Cc"] = cc_email
        msg["Subject"] = subject
        msg["Reply-To"] = "support@gisfy.co.in"

        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        # Save copy to local sent_emails archive
        try:
            sent_dir = Path(__file__).resolve().parent.parent.parent / "storage" / "sent_emails"
            sent_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            clean_sub = "".join(c for c in subject if c.isalnum() or c in (" ", "-", "_")).strip()[:40].replace(" ", "_")
            out_file = sent_dir / f"{ts}_{clean_sub}.html"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(body_html)
        except Exception as exc:
            print(f"Archive write note: {exc}")

        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        # 1. Official Gmail API Send
        if self.service and self.auth_type == "OAuth2":
            try:
                if draft_id and not draft_id.startswith("local_"):
                    # Send existing draft
                    sent = self.service.users().drafts().send(
                        userId="me",
                        body={"id": draft_id}
                    ).execute()
                else:
                    sent = self.service.users().messages().send(
                        userId="me",
                        body={"raw": raw_message}
                    ).execute()

                return True, sent.get("id"), sent.get("threadId"), None
            except Exception as e:
                err_msg = f"Gmail OAuth2 Send Error: {e}"
                print(err_msg)
                return False, None, None, err_msg

        # 2. Secure SMTP fallback (support both SMTP_* and EMAIL_HOST_*)
        smtp_user = os.getenv("SMTP_USER") or os.getenv("EMAIL_HOST_USER") or os.getenv("GMAIL_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_HOST_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
        smtp_host = os.getenv("SMTP_HOST") or os.getenv("EMAIL_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT") or os.getenv("EMAIL_PORT", 587))
        use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

        if smtp_user and smtp_pass:
            try:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
                if use_tls:
                    server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()
                mock_msg_id = f"smtp_{int(datetime.utcnow().timestamp())}"
                return True, mock_msg_id, mock_msg_id, None
            except Exception as e:
                err_msg = f"SMTP Send Error: {e}"
                print(err_msg)
                return False, None, None, err_msg

        # 3. Unconfigured SMTP notice
        return False, None, None, "Email not delivered to inbox: SMTP is not configured. Please configure your SMTP server or Gmail credentials in Settings."

    def check_for_replies(self, thread_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Check Gmail thread replies using Gmail API readonly scope.
        Returns list of detected replies.
        """
        if not self.service or self.auth_type != "OAuth2":
            return []

        replies = []
        for tid in thread_ids:
            if not tid or tid.startswith("local_") or tid.startswith("simulated_"):
                continue
            try:
                thread = self.service.users().threads().get(userId="me", id=tid).execute()
                messages = thread.get("messages", [])
                if len(messages) > 1:
                    last_msg = messages[-1]
                    snippet = last_msg.get("snippet", "")
                    headers = last_msg.get("payload", {}).get("headers", [])
                    sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "")
                    internal_date = int(last_msg.get("internalDate", 0)) / 1000
                    replies.append({
                        "thread_id": tid,
                        "sender": sender,
                        "snippet": snippet,
                        "received_at": datetime.fromtimestamp(internal_date) if internal_date else datetime.utcnow()
                    })
            except Exception as e:
                print(f"Error checking replies for thread {tid}: {e}")
        return replies

gmail_connector = GmailConnector()
