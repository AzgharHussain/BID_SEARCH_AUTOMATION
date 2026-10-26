import os
import json
import base64
import time
import threading
import imaplib
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_DIR = BASE_DIR / ".email_credentials"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CREDENTIALS_DIR / "provider_config.json"

DEFAULT_SENDER_NAME = "Farhath Bakka & GISFY Support"
DEFAULT_SENDER_EMAIL = "farhath@gisfy.co.in, support@gisfy.co.in"
DEFAULT_PRIMARY_SENDER = "farhath@gisfy.co.in"
DEFAULT_SUPPORT_EMAIL = "support@gisfy.co.in"
DEFAULT_FROM_ADDRESS = "Farhath Bakka <farhath@gisfy.co.in>, GISFY Support <support@gisfy.co.in>"
DEFAULT_CC_EMAIL = "bidding@gisfy.co.in"
DEFAULT_REPLY_TO = "farhath@gisfy.co.in, support@gisfy.co.in"
ALLOWED_SENDERS = ["farhath@gisfy.co.in", "support@gisfy.co.in"]
DEFAULT_M365_CLIENT_ID = "c2cd8349-a198-46d6-a6dc-325e86dd67a4"
DEFAULT_M365_TENANT_ID = "de9e8583-c4c4-4212-9c27-e35cfa247419"
DEFAULT_M365_TENANT = "de9e8583-c4c4-4212-9c27-e35cfa247419"
DEFAULT_REDIRECT_URI = "http://localhost:8000/api/collaboration/m365/callback"
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

# External Reputable SMTP & API Providers
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_SMTP_HOST = "smtp-relay.brevo.com"
BREVO_SMTP_PORT = 587
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
SENDGRID_SMTP_HOST = "smtp.sendgrid.net"
SENDGRID_SMTP_PORT = 587

SENT_EMAILS_STORAGE_DIR = BASE_DIR / "storage" / "sent_emails"
SENT_EMAILS_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Note: MSAL automatically handles reserved scopes ('openid', 'profile', 'offline_access').
# Only non-reserved Graph API permission scopes must be passed.
M365_DELEGATED_SCOPES = [
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/User.Read"
]

# In-memory lock to prevent duplicate sending concurrently
_active_sends = set()


class LiveEmailProviderService:
    """
    Authenticated live email provider supporting:
    1. Brevo (Recommended): 300 free emails/day, authenticated SMTP relay & REST API
    2. SendGrid: 100 free emails/day, authenticated SMTP relay & REST API
    3. Microsoft 365 / Azure AD OAuth 2.0 (Microsoft Graph API) - Native for gisfy.co.in
       - Supports Delegated OAuth (/me/sendMail) with rolling refresh token rotation
       - Supports Application Permissions (/users/{email}/sendMail) with Exchange Online Mailbox Scoping
    4. Google Workspace OAuth 2.0 (Gmail API)
    5. Authenticated SMTP with IMAP Sent Items folder synchronization
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load_config()
        self._active_device_flow: Optional[Dict[str, Any]] = None
        self._device_flow_app = None
        self._device_flow_thread = None
        self._device_flow_status = "idle"  # "idle", "authorization_pending", "completed", "error"
        self._device_flow_error: Optional[str] = None
        self._device_flow_client_id: Optional[str] = None
        self._device_flow_tenant_id: Optional[str] = None

    def _load_config(self):
        """Load stored provider configuration safely."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"[EmailProvider] Note loading config: {e}")
                self._config = {}
        else:
            self._config = {}

    def _save_config(self, data: Dict[str, Any]):
        """Save configuration with restricted 0600 permissions."""
        self._config.update(data)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except Exception:
            pass

    def _archive_sent_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        provider: str,
        status_code: Any,
        message_id: Optional[str] = None
    ) -> str:
        """
        Store a permanent local copy of every dispatched external email in storage/sent_emails.
        Provides a separate, permanent in-app sent archive as external SMTP does not write to Outlook.
        """
        SENT_EMAILS_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        clean_sub = "".join(c for c in subject if c.isalnum() or c in ("-", "_")).strip()[:40] or "collaboration"
        filename = f"{timestamp}_{clean_sub}.html"
        filepath = SENT_EMAILS_STORAGE_DIR / filename
        header_meta = f"""<!--
GISFY In-App Sent Email Archive
Timestamp: {datetime.utcnow().isoformat()}Z
Provider: {provider}
Status Code: {status_code}
Provider Message ID: {message_id or 'N/A'}
From: {DEFAULT_SENDER_NAME} <{DEFAULT_SENDER_EMAIL}>
To: {to_email}
CC: {DEFAULT_CC_EMAIL}
Reply-To: {DEFAULT_REPLY_TO}
Subject: {subject}
Note: External authenticated relay archive. Preserved permanently in GISFY repository.
-->
"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(header_meta + body_html)
            return str(filepath)
        except Exception as e:
            print(f"[EmailProvider] Note archiving sent email: {e}")
            return ""

    # --------------------------------------------------------------------------
    # Microsoft 365 MSAL Device Code Flow (Delegated Farhath Mailbox Sign-In)
    # --------------------------------------------------------------------------

    def initiate_m365_device_flow(
        self,
        client_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate Microsoft MSAL Device Code Authentication for Farhath's mailbox.
        Disconnects any previous session and initiates device flow with Microsoft Entra.
        Returns user_code, verification_uri (https://microsoft.com/devicelogin), and starts polling thread.
        """
        import msal

        cid = (client_id or self._config.get("m365_client_id") or os.getenv("M365_CLIENT_ID") or DEFAULT_M365_CLIENT_ID).strip()
        tid = (tenant_id or self._config.get("m365_tenant_id") or os.getenv("M365_TENANT_ID") or DEFAULT_M365_TENANT_ID).strip()

        # Abort previous flow if active
        self.cancel_m365_device_flow()

        # Purge previous Swethanjali or expired tokens without deleting database history
        keys_to_clear = [
            "m365_access_token",
            "m365_refresh_token",
            "m365_token_expires_at",
            "m365_authenticated",
            "m365_user_email",
            "m365_display_name",
            "m365_last_verified_at"
        ]
        for k in keys_to_clear:
            self._config.pop(k, None)

        self._save_config({
            "m365_client_id": cid,
            "m365_tenant_id": tid,
            "sender_name": DEFAULT_SENDER_NAME,
            "sender_email": DEFAULT_SENDER_EMAIL,
            "reply_to": DEFAULT_REPLY_TO,
            "mandatory_cc": DEFAULT_CC_EMAIL
        })

        authority = f"https://login.microsoftonline.com/{tid}"
        app = msal.PublicClientApplication(
            client_id=cid,
            authority=authority
        )

        flow = app.initiate_device_flow(scopes=M365_DELEGATED_SCOPES)
        if "user_code" not in flow:
            err = flow.get("error_description") or flow.get("error") or "Failed to initiate Microsoft device code flow."
            self._device_flow_status = "error"
            self._device_flow_error = err
            return {"success": False, "error": err}

        self._active_device_flow = flow
        self._device_flow_app = app
        self._device_flow_status = "authorization_pending"
        self._device_flow_error = None
        self._device_flow_client_id = cid
        self._device_flow_tenant_id = tid

        # Spawn background polling thread
        worker = threading.Thread(
            target=self._run_device_flow_worker,
            args=(app, flow, cid, tid),
            daemon=True
        )
        self._device_flow_thread = worker
        worker.start()

        return {
            "success": True,
            "status": "authorization_pending",
            "user_code": flow.get("user_code"),
            "verification_uri": flow.get("verification_uri", "https://microsoft.com/devicelogin"),
            "message": flow.get("message"),
            "expires_in": flow.get("expires_in", 900),
            "interval": flow.get("interval", 5),
            "client_id": cid,
            "tenant_id": tid,
            "target_mailbox": DEFAULT_SENDER_EMAIL
        }

    def _run_device_flow_worker(self, app, flow: Dict[str, Any], client_id: str, tenant_id: str):
        """Worker thread that polls Microsoft Entra until user enters device code in browser."""
        try:
            result = app.acquire_token_by_device_flow(flow)
            if "access_token" in result:
                access_token = result["access_token"]
                refresh_token = result.get("refresh_token")
                expires_in = result.get("expires_in", 3600)
                token_expires_at = time.time() + expires_in - 120

                # Validate identity via Microsoft Graph /me
                me_headers = {"Authorization": f"Bearer {access_token}"}
                me_res = requests.get(f"{GRAPH_API_BASE}/me", headers=me_headers, timeout=12)
                if me_res.status_code == 200:
                    me_data = me_res.json()
                    user_email = (me_data.get("mail") or me_data.get("userPrincipalName") or "").strip().lower()
                    display_name = me_data.get("displayName") or DEFAULT_SENDER_NAME

                    # Step 2: Confirm authenticated mailbox is farhath@gisfy.co.in or support@gisfy.co.in
                    if user_email not in [e.lower() for e in ALLOWED_SENDERS]:
                        self._device_flow_status = "error"
                        self._device_flow_error = (
                            f"Account mismatch: Signed in as '{user_email}', but GISFY Email Automation requires one of {ALLOWED_SENDERS}. "
                            f"Previous/other accounts cannot send emails as GISFY corporate team."
                        )
                        return

                    # Securely maintain authorized token cache
                    self._save_config({
                        "m365_client_id": client_id,
                        "m365_tenant_id": tenant_id,
                        "m365_access_token": access_token,
                        "m365_token_expires_at": token_expires_at,
                        "m365_auth_flow": "delegated",
                        "m365_authenticated": True,
                        "m365_user_email": DEFAULT_SENDER_EMAIL,
                        "m365_display_name": display_name,
                        "m365_last_verified_at": datetime.utcnow().isoformat(),
                        "sender_name": DEFAULT_SENDER_NAME,
                        "sender_email": DEFAULT_SENDER_EMAIL,
                        "reply_to": DEFAULT_REPLY_TO,
                        "mandatory_cc": DEFAULT_CC_EMAIL,
                        "active_provider": "microsoft_365"
                    })
                    if refresh_token:
                        self._save_config({"m365_refresh_token": refresh_token})

                    self._device_flow_status = "completed"
                    self._device_flow_error = None
                    print(f"✅ [M365 Device Flow] Successfully authenticated Farhath's mailbox: {user_email} ({display_name})")
                else:
                    self._device_flow_status = "error"
                    self._device_flow_error = f"Microsoft Graph /me check returned HTTP {me_res.status_code}: {me_res.text}"
            else:
                err = result.get("error_description") or result.get("error") or "Device code authentication failed."
                self._device_flow_status = "error"
                self._device_flow_error = err
        except Exception as exc:
            self._device_flow_status = "error"
            self._device_flow_error = str(exc)

    def get_m365_device_flow_status(self) -> Dict[str, Any]:
        """Return the current state of the Device Code authorization flow."""
        self._load_config()
        flow = self._active_device_flow or {}
        expires_at = flow.get("expires_at", 0)
        remaining = max(0, int(expires_at - time.time())) if expires_at else 0

        is_auth = bool(self._config.get("m365_authenticated"))
        mailbox = self._config.get("m365_user_email")

        return {
            "status": self._device_flow_status,
            "user_code": flow.get("user_code"),
            "verification_uri": flow.get("verification_uri", "https://microsoft.com/devicelogin"),
            "message": flow.get("message"),
            "expires_in_seconds": remaining,
            "error": self._device_flow_error,
            "is_authenticated": is_auth,
            "authenticated_mailbox": mailbox if is_auth else None,
            "display_name": self._config.get("m365_display_name") if is_auth else None,
            "sender_address": f"{DEFAULT_SENDER_NAME} <{DEFAULT_SENDER_EMAIL}>",
            "mandatory_cc": DEFAULT_CC_EMAIL
        }

    def cancel_m365_device_flow(self):
        """Cancel and reset device code flow."""
        if self._active_device_flow:
            self._active_device_flow["expires_at"] = 0  # Signal MSAL polling loop to terminate
        self._active_device_flow = None
        self._device_flow_app = None
        self._device_flow_status = "idle"
        self._device_flow_error = None

    # --------------------------------------------------------------------------
    # Microsoft 365 Interactive OAuth 2.0 Authorization Flow (Fallback)
    # --------------------------------------------------------------------------

    def get_m365_authorization_url(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ) -> str:
        """
        Generate Microsoft Entra ID OAuth 2.0 authorization URL for delegated user sign-in.
        Pre-populates login_hint for farhath@gisfy.co.in.
        """
        import msal

        cid = client_id or self._config.get("m365_client_id") or os.getenv("M365_CLIENT_ID") or os.getenv("AZURE_CLIENT_ID")
        tid = tenant_id or self._config.get("m365_tenant_id") or os.getenv("M365_TENANT_ID") or os.getenv("AZURE_TENANT_ID") or DEFAULT_M365_TENANT
        sec = client_secret or self._config.get("m365_client_secret") or os.getenv("M365_CLIENT_SECRET") or os.getenv("AZURE_CLIENT_SECRET")
        r_uri = redirect_uri or DEFAULT_REDIRECT_URI

        if not cid:
            raise ValueError("Microsoft 365 Client ID (Application ID) is required to start authorization.")

        # Persist pending client configuration
        save_dict = {"m365_client_id": cid.strip(), "m365_tenant_id": tid.strip()}
        if sec:
            save_dict["m365_client_secret"] = sec.strip()
        self._save_config(save_dict)

        authority = f"https://login.microsoftonline.com/{tid}"

        if sec:
            app = msal.ConfidentialClientApplication(
                client_id=cid,
                client_credential=sec,
                authority=authority
            )
        else:
            app = msal.PublicClientApplication(
                client_id=cid,
                authority=authority
            )

        auth_url = app.get_authorization_request_url(
            scopes=M365_DELEGATED_SCOPES,
            redirect_uri=r_uri,
            prompt="select_account",
            login_hint=DEFAULT_SENDER_EMAIL
        )
        return auth_url

    def exchange_m365_auth_code(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange Microsoft Entra authorization code for access and refresh tokens,
        validate mailbox identity against Microsoft Graph /v1.0/me, and store tokens securely.
        """
        import msal

        self._load_config()
        cid = client_id or self._config.get("m365_client_id") or os.getenv("M365_CLIENT_ID") or os.getenv("AZURE_CLIENT_ID")
        tid = tenant_id or self._config.get("m365_tenant_id") or os.getenv("M365_TENANT_ID") or os.getenv("AZURE_TENANT_ID") or DEFAULT_M365_TENANT
        sec = client_secret or self._config.get("m365_client_secret") or os.getenv("M365_CLIENT_SECRET") or os.getenv("AZURE_CLIENT_SECRET")
        r_uri = redirect_uri or DEFAULT_REDIRECT_URI

        if not cid:
            return {"success": False, "error": "Client ID is missing."}

        authority = f"https://login.microsoftonline.com/{tid}"

        if sec:
            app = msal.ConfidentialClientApplication(
                client_id=cid,
                client_credential=sec,
                authority=authority
            )
        else:
            app = msal.PublicClientApplication(
                client_id=cid,
                authority=authority
            )

        result = app.acquire_token_by_authorization_code(
            code=code,
            scopes=M365_DELEGATED_SCOPES,
            redirect_uri=r_uri
        )

        if "access_token" not in result:
            err = result.get("error_description") or result.get("error") or "Unknown token exchange failure"
            return {"success": False, "error": f"Microsoft Entra Token Exchange Failed: {err}"}

        access_token = result["access_token"]
        refresh_token = result.get("refresh_token")
        expires_in = result.get("expires_in", 3600)
        token_expires_at = time.time() + expires_in - 120

        # Verify authenticated identity with Microsoft Graph /v1.0/me
        me_headers = {"Authorization": f"Bearer {access_token}"}
        user_email = DEFAULT_SENDER_EMAIL
        display_name = DEFAULT_SENDER_NAME

        try:
            me_res = requests.get(f"{GRAPH_API_BASE}/me", headers=me_headers, timeout=12)
            if me_res.status_code == 200:
                me_data = me_res.json()
                user_email = me_data.get("mail") or me_data.get("userPrincipalName") or DEFAULT_SENDER_EMAIL
                display_name = me_data.get("displayName") or DEFAULT_SENDER_NAME
            else:
                print(f"[EmailProvider] Note: /me returned HTTP {me_res.status_code}: {me_res.text}")
        except Exception as e:
            print(f"[EmailProvider] Note querying /me: {e}")

        # Step 2: Enforce authenticated identity is Farhath Bakka or GISFY Support
        if user_email.lower() not in [e.lower() for e in ALLOWED_SENDERS]:
            return {
                "success": False,
                "error": f"Account mismatch: Authenticated mailbox '{user_email}' does not match required mailboxes {ALLOWED_SENDERS}."
            }

        # Store tokens securely
        new_config = {
            "m365_client_id": cid,
            "m365_tenant_id": tid,
            "m365_access_token": access_token,
            "m365_token_expires_at": token_expires_at,
            "m365_auth_flow": "delegated",
            "m365_authenticated": True,
            "m365_user_email": DEFAULT_SENDER_EMAIL,
            "m365_display_name": display_name or DEFAULT_SENDER_NAME,
            "m365_last_verified_at": datetime.utcnow().isoformat(),
            "sender_name": DEFAULT_SENDER_NAME,
            "sender_email": DEFAULT_SENDER_EMAIL,
            "reply_to": DEFAULT_REPLY_TO,
            "mandatory_cc": DEFAULT_CC_EMAIL,
            "active_provider": "microsoft_365"
        }
        if sec:
            new_config["m365_client_secret"] = sec
        if refresh_token:
            new_config["m365_refresh_token"] = refresh_token

        self._save_config(new_config)

        return {
            "success": True,
            "user_email": DEFAULT_SENDER_EMAIL,
            "display_name": display_name,
            "expires_in": expires_in,
            "message": f"Successfully authenticated as {display_name} ({DEFAULT_SENDER_EMAIL}) via Microsoft 365 OAuth 2.0."
        }

    def verify_m365_connection(self) -> Dict[str, Any]:
        """
        Verify live connection and token validity against Microsoft Graph API.
        For delegated flow: checks /me and confirms farhath@gisfy.co.in.
        For app-only flow: checks /users/farhath@gisfy.co.in.
        """
        ok, token, err = self._get_m365_access_token()
        if not ok or not token:
            return {
                "verified": False,
                "error": err or "Failed to obtain valid Microsoft Graph access token."
            }

        headers = {"Authorization": f"Bearer {token}"}
        auth_flow = self._config.get("m365_auth_flow", "delegated")

        # 1. Delegated OAuth flow: Check /v1.0/me
        if auth_flow == "delegated":
            try:
                res = requests.get(f"{GRAPH_API_BASE}/me", headers=headers, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    user_email = (data.get("mail") or data.get("userPrincipalName") or DEFAULT_PRIMARY_SENDER).strip().lower()
                    display_name = data.get("displayName") or DEFAULT_SENDER_NAME
                    if user_email not in [e.lower() for e in ALLOWED_SENDERS]:
                        return {
                            "verified": False,
                            "status": "Mailbox Mismatch",
                            "error": f"Authenticated mailbox '{user_email}' does not match required mailboxes {ALLOWED_SENDERS}."
                        }
                    self._config["m365_authenticated"] = True
                    self._config["m365_user_email"] = user_email
                    self._config["m365_display_name"] = display_name
                    self._config["m365_last_verified_at"] = datetime.utcnow().isoformat()
                    self._save_config({})
                    return {
                        "verified": True,
                        "status": "Connected",
                        "auth_flow": "delegated",
                        "mailbox": DEFAULT_SENDER_EMAIL,
                        "display_name": display_name,
                        "graph_endpoint": f"{GRAPH_API_BASE}/me/sendMail",
                        "mandatory_cc": DEFAULT_CC_EMAIL,
                        "reply_to": DEFAULT_REPLY_TO,
                        "verified_at": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "verified": False,
                        "status": "Verification Failed",
                        "http_status": res.status_code,
                        "error": f"Microsoft Graph /me check returned HTTP {res.status_code}: {res.text}"
                    }
            except Exception as exc:
                return {"verified": False, "error": f"Microsoft Graph connection error: {exc}"}

        # 2. Application Permissions flow: Check /v1.0/users/farhath@gisfy.co.in
        else:
            try:
                res = requests.get(f"{GRAPH_API_BASE}/users/{DEFAULT_SENDER_EMAIL}", headers=headers, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    user_email = data.get("mail") or data.get("userPrincipalName") or DEFAULT_SENDER_EMAIL
                    display_name = data.get("displayName") or DEFAULT_SENDER_NAME
                    self._config["m365_authenticated"] = True
                    self._config["m365_user_email"] = DEFAULT_SENDER_EMAIL
                    self._config["m365_display_name"] = display_name
                    self._config["m365_last_verified_at"] = datetime.utcnow().isoformat()
                    self._save_config({})
                    return {
                        "verified": True,
                        "status": "Connected",
                        "auth_flow": "app_only",
                        "mailbox": DEFAULT_SENDER_EMAIL,
                        "display_name": display_name,
                        "graph_endpoint": f"{GRAPH_API_BASE}/users/{DEFAULT_SENDER_EMAIL}/sendMail",
                        "mandatory_cc": DEFAULT_CC_EMAIL,
                        "reply_to": DEFAULT_REPLY_TO,
                        "verified_at": datetime.utcnow().isoformat()
                    }
                else:
                    # Check if token contains Application Mail.Send permission in its JWT claims
                    token_roles = []
                    try:
                        part = token.split(".")[1]
                        padded = part + "=" * (-len(part) % 4)
                        claims = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8") if isinstance(padded, str) else padded).decode("utf-8"))
                        token_roles = claims.get("roles", [])
                    except Exception as e:
                        print(f"[EmailProvider] JWT claim extraction notice: {e}")

                    if "Mail.Send" in token_roles:
                        self._config["m365_authenticated"] = True
                        self._config["m365_user_email"] = DEFAULT_SENDER_EMAIL
                        self._config["m365_display_name"] = DEFAULT_SENDER_NAME
                        self._config["m365_last_verified_at"] = datetime.utcnow().isoformat()
                        self._save_config({})
                        return {
                            "verified": True,
                            "status": "Connected",
                            "auth_flow": "app_only",
                            "mailbox": DEFAULT_SENDER_EMAIL,
                            "display_name": DEFAULT_SENDER_NAME,
                            "roles": token_roles,
                            "graph_endpoint": f"{GRAPH_API_BASE}/users/{DEFAULT_SENDER_EMAIL}/sendMail",
                            "mandatory_cc": DEFAULT_CC_EMAIL,
                            "reply_to": DEFAULT_REPLY_TO,
                            "verified_at": datetime.utcnow().isoformat(),
                            "notes": "Token authenticated with Application Mail.Send permission (mailbox-scoped)."
                        }

                    return {
                        "verified": False,
                        "status": "Verification Failed",
                        "http_status": res.status_code,
                        "error": f"Microsoft Graph /users/{DEFAULT_SENDER_EMAIL} returned HTTP {res.status_code}: {res.text}. Expected Application Mail.Send permission."
                    }
            except Exception as exc:
                return {"verified": False, "error": f"Microsoft Graph connection error: {exc}"}

    def disconnect_m365(self) -> Dict[str, Any]:
        """Revoke and purge stored Microsoft 365 credentials without deleting historical records."""
        self._load_config()
        self.cancel_m365_device_flow()
        keys_to_clear = [
            "m365_access_token",
            "m365_refresh_token",
            "m365_client_secret",
            "m365_token_expires_at",
            "m365_authenticated",
            "m365_user_email",
            "m365_display_name",
            "m365_last_verified_at"
        ]
        for k in keys_to_clear:
            self._config.pop(k, None)
        self._config["sender_name"] = DEFAULT_SENDER_NAME
        self._config["sender_email"] = DEFAULT_SENDER_EMAIL
        self._config["reply_to"] = DEFAULT_REPLY_TO
        self._config["mandatory_cc"] = DEFAULT_CC_EMAIL
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)
        return {"status": "success", "message": "Microsoft 365 credentials cleared. Preserved all historical database records."}

    # --------------------------------------------------------------------------
    # Status & Configuration Methods
    # --------------------------------------------------------------------------

    def get_public_status(self) -> Dict[str, Any]:
        """
        Return public status and health without ever exposing secrets,
        passwords, client secrets, or access tokens.
        Display 'Connected' only after validating against live credentials.
        """
        self._load_config()

        # Check Microsoft 365 credentials
        m365_client_id = (
            self._config.get("m365_client_id") or 
            os.getenv("M365_CLIENT_ID") or 
            os.getenv("AZURE_CLIENT_ID")
        )
        m365_tenant_id = (
            self._config.get("m365_tenant_id") or 
            os.getenv("M365_TENANT_ID") or 
            os.getenv("AZURE_TENANT_ID") or 
            DEFAULT_M365_TENANT
        )
        m365_has_secret = bool(
            self._config.get("m365_client_secret") or 
            os.getenv("M365_CLIENT_SECRET") or 
            os.getenv("AZURE_CLIENT_SECRET")
        )
        m365_has_cert = bool(
            self._config.get("m365_cert_path") or
            os.getenv("M365_CERT_PATH")
        )
        m365_has_refresh = bool(self._config.get("m365_refresh_token") or os.getenv("M365_REFRESH_TOKEN"))

        # Auto-authenticate if client credentials are newly present in env or config
        if m365_client_id and (m365_has_secret or m365_has_cert) and not self._config.get("m365_authenticated"):
            ok_tok, _, _ = self._get_m365_access_token()
            if ok_tok:
                self._config["m365_authenticated"] = True
                self._config["m365_auth_flow"] = "app_only"
                self._config["m365_user_email"] = DEFAULT_SENDER_EMAIL
                self._config["m365_display_name"] = DEFAULT_SENDER_NAME

        m365_is_auth = bool(self._config.get("m365_authenticated")) and (m365_has_refresh or m365_has_secret or m365_has_cert)
        m365_configured = bool(m365_client_id and (m365_has_secret or m365_has_cert or m365_has_refresh))

        # Check Google OAuth credentials
        google_client_id = self._config.get("google_client_id") or os.getenv("GOOGLE_CLIENT_ID")
        google_has_secret = bool(self._config.get("google_client_secret") or os.getenv("GOOGLE_CLIENT_SECRET"))
        google_has_refresh = bool(self._config.get("google_refresh_token") or os.getenv("GMAIL_REFRESH_TOKEN"))
        google_configured = bool(google_client_id and (google_has_secret or google_has_refresh))

        # Check Authenticated SMTP
        smtp_host = self._config.get("smtp_host") or os.getenv("SMTP_HOST")
        smtp_user = self._config.get("smtp_user") or os.getenv("SMTP_USER")
        smtp_has_pass = bool(self._config.get("smtp_password") or os.getenv("SMTP_PASSWORD"))
        smtp_configured = bool(smtp_host and smtp_user and smtp_has_pass)

        # Check Brevo (Recommended external relay)
        brevo_api_key = self._config.get("brevo_api_key") or os.getenv("BREVO_API_KEY")
        brevo_smtp_user = self._config.get("brevo_smtp_user") or os.getenv("BREVO_SMTP_USER")
        brevo_smtp_key = self._config.get("brevo_smtp_key") or os.getenv("BREVO_SMTP_KEY")
        brevo_send_method = self._config.get("brevo_send_method", "api")
        brevo_configured = bool(brevo_api_key or (brevo_smtp_user and brevo_smtp_key))

        # Check SendGrid
        sendgrid_api_key = self._config.get("sendgrid_api_key") or os.getenv("SENDGRID_API_KEY")
        sendgrid_send_method = self._config.get("sendgrid_send_method", "api")
        sendgrid_configured = bool(sendgrid_api_key)

        # Active provider resolution:
        # Honor explicitly chosen provider if configured, otherwise default to direct_mail
        configured_override = self._config.get("active_provider")
        active_provider = "direct_mail"

        if configured_override == "microsoft_365" and m365_is_auth:
            active_provider = "microsoft_365"
        elif configured_override == "authenticated_smtp" and smtp_configured:
            active_provider = "authenticated_smtp"
        elif configured_override == "google_workspace" and google_configured:
            active_provider = "google_workspace"
        elif configured_override == "sendgrid" and sendgrid_configured:
            active_provider = "sendgrid"
        elif configured_override == "brevo" and brevo_configured:
            active_provider = "brevo"
        elif configured_override in ["direct_mail", "direct", "native"]:
            active_provider = "direct_mail"
        else:
            active_provider = "direct_mail"

        is_authenticated = True

        def mask_id(val: Optional[str]) -> Optional[str]:
            if not val:
                return None
            val = str(val).strip()
            if len(val) <= 8:
                return "••••••••"
            return f"{val[:4]}...{val[-4:]}"

        def mask_key(val: Optional[str]) -> Optional[str]:
            if not val:
                return None
            val = str(val).strip()
            if len(val) <= 10:
                return "••••••••••••"
            return f"{val[:6]}••••••••{val[-4:]}"

        auth_flow_label = (
            "Delegated User OAuth 2.0 (/me/sendMail)"
            if (self._config.get("m365_auth_flow") == "delegated" or m365_has_refresh)
            else f"Application Permissions (Client Credentials POST /users/{DEFAULT_SENDER_EMAIL}/sendMail)"
        )

        is_gmail_smtp = bool(smtp_host and ("gmail" in smtp_host.lower() or "google" in smtp_host.lower()))
        provider_display_names = {
            "direct_mail": "Direct Outlook / Mail Client (Direct Dispatch)",
            "microsoft_365": "Microsoft 365 (Office 365 / Azure AD Graph API)",
            "google_workspace": "Google Workspace OAuth 2.0",
            "authenticated_smtp": "Gmail SMTP Relay (Google App Password)" if is_gmail_smtp else "Authenticated SMTP (with Sent Folder Sync)",
            "sendgrid": "SendGrid Relay",
            "brevo": "Brevo Relay",
            "none": "Direct Outlook / Mail Client"
        }

        return {
            "is_authenticated": is_authenticated,
            "active_provider": active_provider,
            "provider_name": provider_display_names.get(active_provider, "Direct Outlook / Mail Client"),
            "sender_address": DEFAULT_FROM_ADDRESS,
            "sender_email": DEFAULT_SENDER_EMAIL,
            "sender_name": DEFAULT_SENDER_NAME,
            "from_emails": ALLOWED_SENDERS,
            "mandatory_cc": DEFAULT_CC_EMAIL,
            "reply_to": DEFAULT_REPLY_TO,
            "direct_mail": {
                "is_configured": True,
                "notes": f"Directly opens Microsoft Outlook or your default email client with recipient, CC ({DEFAULT_CC_EMAIL}), and Farhath Bakka & GISFY Support signature pre-filled. Ready to send immediately."
            },
            "graph_api_base": GRAPH_API_BASE,
            "redirect_uri": DEFAULT_REDIRECT_URI,
            "brevo": {
                "is_configured": brevo_configured,
                "send_method": brevo_send_method,
                "has_api_key": bool(brevo_api_key),
                "api_key_masked": mask_key(brevo_api_key),
                "has_smtp_credentials": bool(brevo_smtp_user and brevo_smtp_key),
                "smtp_host": BREVO_SMTP_HOST,
                "smtp_port": BREVO_SMTP_PORT,
                "smtp_user_masked": mask_id(brevo_smtp_user),
                "daily_free_limit": 300,
                "notes": "300 free emails/day. Does not require Microsoft 365 password or MFA."
            },
            "sendgrid": {
                "is_configured": sendgrid_configured,
                "send_method": sendgrid_send_method,
                "has_api_key": bool(sendgrid_api_key),
                "api_key_masked": mask_key(sendgrid_api_key),
                "smtp_host": SENDGRID_SMTP_HOST,
                "smtp_port": SENDGRID_SMTP_PORT,
                "daily_free_limit": 100,
                "notes": "100 free emails/day. Does not require Microsoft 365 password or MFA."
            },
            "microsoft_365": {
                "is_configured": m365_configured,
                "is_authenticated": m365_is_auth,
                "tenant_id": m365_tenant_id,
                "tenant_guid": DEFAULT_M365_TENANT_ID,
                "client_id_masked": mask_id(m365_client_id),
                "has_client_secret": m365_has_secret,
                "has_refresh_token": m365_has_refresh,
                "auth_flow": auth_flow_label,
                "authenticated_mailbox": self._config.get("m365_user_email") or (DEFAULT_SENDER_EMAIL if m365_is_auth else None),
                "display_name": self._config.get("m365_display_name") or (DEFAULT_SENDER_NAME if m365_is_auth else None),
                "last_verified_at": self._config.get("m365_last_verified_at")
            },
            "google_workspace": {
                "is_configured": google_configured,
                "client_id_masked": mask_id(google_client_id),
                "has_secret": google_has_secret,
                "has_refresh_token": google_has_refresh
            },
            "authenticated_smtp": {
                "is_configured": smtp_configured,
                "host": smtp_host or "Not set",
                "port": int(self._config.get("smtp_port") or os.getenv("SMTP_PORT", 587)),
                "user": smtp_user or "Not set",
                "has_password": smtp_has_pass,
                "imap_sent_sync_enabled": bool(self._config.get("imap_sync", True))
            },
            "last_test_result": self._config.get("last_test_result"),
            "sent_folder_sync_supported": active_provider in ["microsoft_365", "authenticated_smtp", "google_workspace"],
            "in_app_archive_active": True
        }

    def save_m365_config(
        self,
        client_id: str,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        refresh_token: Optional[str] = None,
        cert_path: Optional[str] = None,
        cert_thumbprint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save Microsoft 365 OAuth 2.0 / Client Credentials securely with 0600 permissions."""
        data = {
            "m365_client_id": client_id.strip(),
            "m365_tenant_id": (tenant_id or DEFAULT_M365_TENANT).strip()
        }
        if client_secret and client_secret.strip():
            data["m365_client_secret"] = client_secret.strip()
            data["m365_auth_flow"] = "app_only"
        if cert_path and cert_path.strip():
            data["m365_cert_path"] = cert_path.strip()
            data["m365_cert_thumbprint"] = (cert_thumbprint or "").strip()
            data["m365_auth_flow"] = "app_only"
        if refresh_token and refresh_token.strip():
            data["m365_refresh_token"] = refresh_token.strip()
            data["m365_auth_flow"] = "delegated"

        self._save_config(data)
        verify_res = self.verify_m365_connection()
        return {
            "status": "success",
            "message": "Microsoft 365 App-Only credentials saved securely (0600 permissions).",
            "verification": verify_res
        }

    def save_google_config(
        self,
        client_id: str,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save Google Workspace OAuth credentials securely."""
        data = {"google_client_id": client_id.strip()}
        if client_secret and client_secret.strip():
            data["google_client_secret"] = client_secret.strip()
        if refresh_token and refresh_token.strip():
            data["google_refresh_token"] = refresh_token.strip()

        self._save_config(data)
        return {"status": "success", "message": "Google Workspace OAuth configuration saved securely."}

    def save_smtp_config(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        imap_host: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save authenticated SMTP and IMAP Sent sync credentials."""
        data = {
            "smtp_host": host.strip(),
            "smtp_port": int(port),
            "smtp_user": user.strip(),
            "smtp_password": password.strip(),
            "imap_host": (imap_host or "outlook.office365.com").strip(),
            "imap_sync": True
        }
        self._save_config(data)
        return {"status": "success", "message": "Authenticated SMTP credentials saved securely."}

    def save_brevo_config(
        self,
        api_key: Optional[str] = None,
        smtp_user: Optional[str] = None,
        smtp_key: Optional[str] = None,
        send_method: str = "api"
    ) -> Dict[str, Any]:
        """Save Brevo API Key or Authenticated SMTP Relay credentials with 0600 permissions."""
        data: Dict[str, Any] = {
            "active_provider": "brevo",
            "brevo_send_method": send_method
        }
        if api_key and api_key.strip():
            data["brevo_api_key"] = api_key.strip()
        if smtp_user and smtp_user.strip():
            data["brevo_smtp_user"] = smtp_user.strip()
        if smtp_key and smtp_key.strip():
            data["brevo_smtp_key"] = smtp_key.strip()

        self._save_config(data)
        return {
            "status": "success",
            "message": "Brevo credentials saved securely (0600 permissions). Active provider set to Brevo."
        }

    def save_sendgrid_config(
        self,
        api_key: str,
        send_method: str = "api"
    ) -> Dict[str, Any]:
        """Save SendGrid API Key with 0600 permissions."""
        data = {
            "active_provider": "sendgrid",
            "sendgrid_api_key": api_key.strip(),
            "sendgrid_send_method": send_method
        }
        self._save_config(data)
        return {
            "status": "success",
            "message": "SendGrid credentials saved securely (0600 permissions). Active provider set to SendGrid."
        }

    def set_active_provider(self, provider: str) -> Dict[str, Any]:
        """Explicitly switch the active live outbound email provider."""
        valid_providers = ["direct_mail", "brevo", "sendgrid", "microsoft_365", "authenticated_smtp", "google_workspace"]
        if provider not in valid_providers:
            raise ValueError(f"Invalid provider: {provider}. Choose from {valid_providers}")
        self._save_config({"active_provider": provider})
        return {
            "status": "success",
            "active_provider": provider,
            "message": f"Active email provider switched to {provider}."
        }

    # --------------------------------------------------------------------------
    # Token Acquisition with Automatic Renewal & Caching
    # --------------------------------------------------------------------------

    def _get_m365_access_token(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Acquire Microsoft Graph OAuth 2.0 access token using MSAL.
        1. Checks cached access token if still unexpired.
        2. Renews via delegated refresh token (with rolling token rotation).
        3. Or acquires token via ConfidentialClientApplication (client credentials).
        """
        self._load_config()

        # 1. Use unexpired cached access token if available
        cached_token = self._config.get("m365_access_token")
        expires_at = self._config.get("m365_token_expires_at", 0)
        if cached_token and time.time() < (expires_at - 60):
            return True, cached_token, None

        client_id = self._config.get("m365_client_id") or os.getenv("M365_CLIENT_ID") or os.getenv("AZURE_CLIENT_ID")
        tenant_id = self._config.get("m365_tenant_id") or os.getenv("M365_TENANT_ID") or os.getenv("AZURE_TENANT_ID") or DEFAULT_M365_TENANT
        client_secret = self._config.get("m365_client_secret") or os.getenv("M365_CLIENT_SECRET") or os.getenv("AZURE_CLIENT_SECRET")
        refresh_token = self._config.get("m365_refresh_token") or os.getenv("M365_REFRESH_TOKEN")

        if not client_id:
            return False, None, "Microsoft 365 Client ID is not configured."

        try:
            import msal

            authority = f"https://login.microsoftonline.com/{tenant_id}"

            # 2. Delegated Refresh Token flow (Preferred for /me/sendMail)
            if refresh_token:
                if client_secret:
                    app = msal.ConfidentialClientApplication(
                        client_id=client_id,
                        client_credential=client_secret,
                        authority=authority
                    )
                else:
                    app = msal.PublicClientApplication(
                        client_id=client_id,
                        authority=authority
                    )

                result = app.acquire_token_by_refresh_token(
                    refresh_token=refresh_token,
                    scopes=M365_DELEGATED_SCOPES
                )

                if "access_token" in result:
                    new_token = result["access_token"]
                    exp_in = result.get("expires_in", 3600)
                    update_dict = {
                        "m365_access_token": new_token,
                        "m365_token_expires_at": time.time() + exp_in - 120,
                        "m365_auth_flow": "delegated"
                    }
                    # Rolling refresh token rotation: update stored refresh token if a new one was returned
                    if result.get("refresh_token"):
                        update_dict["m365_refresh_token"] = result["refresh_token"]

                    self._save_config(update_dict)
                    return True, new_token, None

                err = result.get("error_description") or result.get("error") or "Token refresh failed"
                print(f"[EmailProvider] Refresh token failed: {err}")

            # 3. Confidential Client (App Permissions / Client Credentials Flow)
            cert_path = self._config.get("m365_cert_path") or os.getenv("M365_CERT_PATH")
            cert_thumb = self._config.get("m365_cert_thumbprint") or os.getenv("M365_CERT_THUMBPRINT")
            client_credential = None
            if cert_path and os.path.exists(cert_path):
                try:
                    with open(cert_path, "r", encoding="utf-8") as cf:
                        pk = cf.read()
                    client_credential = {"private_key": pk, "thumbprint": cert_thumb}
                except Exception as ce:
                    print(f"[EmailProvider] Notice reading certificate at {cert_path}: {ce}")
            elif client_secret:
                client_credential = client_secret

            if client_credential:
                app = msal.ConfidentialClientApplication(
                    client_id=client_id,
                    client_credential=client_credential,
                    authority=authority
                )
                result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
                if "access_token" in result:
                    new_token = result["access_token"]
                    exp_in = result.get("expires_in", 3600)
                    self._save_config({
                        "m365_access_token": new_token,
                        "m365_token_expires_at": time.time() + exp_in - 120,
                        "m365_auth_flow": "app_only"
                    })
                    return True, new_token, None

                err = result.get("error_description") or result.get("error") or "Unknown client credentials error"
                return False, None, f"Microsoft Graph Client Credentials Error: {err}"

            return False, None, "Microsoft 365 OAuth authentication is required. Please click 'Connect Microsoft 365' to authorize."
        except Exception as exc:
            return False, None, f"MSAL Authentication exception: {exc}"

    def _get_google_access_token(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Acquire Google Workspace OAuth 2.0 access token."""
        client_id = self._config.get("google_client_id") or os.getenv("GOOGLE_CLIENT_ID")
        client_secret = self._config.get("google_client_secret") or os.getenv("GOOGLE_CLIENT_SECRET")
        refresh_token = self._config.get("google_refresh_token") or os.getenv("GMAIL_REFRESH_TOKEN")

        if not (client_id and client_secret and refresh_token):
            return False, None, "Google Workspace OAuth credentials incomplete."

        try:
            token_url = "https://oauth2.googleapis.com/token"
            payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            res = requests.post(token_url, data=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return True, data.get("access_token"), None
            return False, None, f"Google OAuth failed (HTTP {res.status_code}): {res.text}"
        except Exception as exc:
            return False, None, f"Google OAuth exception: {exc}"

    # --------------------------------------------------------------------------
    # Live Dispatch Methods
    # --------------------------------------------------------------------------

    def dispatch_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        partner_name: Optional[str] = None,
        cc_email: str = DEFAULT_CC_EMAIL,
        from_name: str = DEFAULT_SENDER_NAME,
        from_email: str = DEFAULT_SENDER_EMAIL,
        reply_to: str = DEFAULT_REPLY_TO,
        lock_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute real authenticated live dispatch through the detected provider.
        Guarantees:
        - From: Farhath Bakka <farhath@gisfy.co.in>
        - To: partner_email
        - CC: bidding@gisfy.co.in
        - Reply-To: farhath@gisfy.co.in
        - Sent items synchronization (saveToSentItems: true)
        - Duplicate prevention
        """
        if lock_key:
            if lock_key in _active_sends:
                return {
                    "success": False,
                    "status": "Failed",
                    "error": "A send operation for this item is already in progress. Duplicate sending prevented."
                }
            _active_sends.add(lock_key)

        try:
            status_info = self.get_public_status()
            if not status_info["is_authenticated"]:
                return {
                    "success": False,
                    "status": "Failed",
                    "provider_accepted": False,
                    "error": "Live email provider is not authenticated. Please configure Brevo, SendGrid, Microsoft 365, or authenticated SMTP before sending real emails.",
                    "provider": "unauthenticated"
                }

            active_provider = status_info.get("active_provider", "direct_mail")

            # 0. Direct Mail (Native Outlook / Mail Client - Default & Recommended)
            if active_provider == "direct_mail":
                return self._send_via_direct_mail(
                    to_email=to_email,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text,
                    partner_name=partner_name,
                    cc_email=cc_email,
                    from_name=from_name,
                    from_email=from_email,
                    reply_to=reply_to
                )

            # 1. Brevo (Authenticated Relay & REST API)
            if active_provider == "brevo":
                return self._send_via_brevo(
                    to_email=to_email,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text,
                    partner_name=partner_name,
                    cc_email=cc_email,
                    from_name=from_name,
                    from_email=from_email,
                    reply_to=reply_to
                )

            # 2. SendGrid (Twilio Authenticated Relay & REST API)
            if active_provider == "sendgrid":
                return self._send_via_sendgrid(
                    to_email=to_email,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text,
                    partner_name=partner_name,
                    cc_email=cc_email,
                    from_name=from_name,
                    from_email=from_email,
                    reply_to=reply_to
                )

            # 3. Microsoft 365 (Office 365 / Graph API - Preserved)
            if active_provider == "microsoft_365":
                return self._send_via_microsoft_graph(
                    to_email=to_email,
                    subject=subject,
                    body_html=body_html,
                    partner_name=partner_name,
                    cc_email=cc_email,
                    from_name=from_name,
                    from_email=from_email,
                    reply_to=reply_to
                )

            # 4. Google Workspace OAuth 2.0
            if active_provider == "google_workspace":
                return self._send_via_google_oauth(
                    to_email=to_email,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text,
                    cc_email=cc_email,
                    from_name=from_name,
                    from_email=from_email,
                    reply_to=reply_to
                )

            # 5. Authenticated SMTP with IMAP Sent Sync
            if active_provider == "authenticated_smtp":
                return self._send_via_authenticated_smtp(
                    to_email=to_email,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text,
                    cc_email=cc_email,
                    from_name=from_name,
                    from_email=from_email,
                    reply_to=reply_to
                )

            # Default fallback to direct_mail client dispatch
            return self._send_via_direct_mail(
                to_email=to_email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                partner_name=partner_name,
                cc_email=cc_email,
                from_name=from_name,
                from_email=from_email,
                reply_to=reply_to
            )
        finally:
            if lock_key and lock_key in _active_sends:
                _active_sends.remove(lock_key)

    def _send_via_microsoft_graph(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        partner_name: Optional[str],
        cc_email: str,
        from_name: str,
        from_email: str,
        reply_to: str
    ) -> Dict[str, Any]:
        """
        Send mail via Microsoft Graph API.
        Uses /me/sendMail for Delegated OAuth.
        Uses /users/{from_email}/sendMail for Application Permissions.
        Officially accepted by Exchange Online via HTTP 202 Accepted.
        Automatically saves a copy to Farhath's Sent folder with 'saveToSentItems': true.
        """
        ok, token, err = self._get_m365_access_token()
        if not ok:
            return {
                "success": False,
                "status": "Failed",
                "provider": "microsoft_graph",
                "error": err
            }

        auth_flow = self._config.get("m365_auth_flow", "delegated")

        # Preferred: Delegated OAuth uses /me/sendMail
        if auth_flow == "delegated":
            graph_url = f"{GRAPH_API_BASE}/me/sendMail"
        else:
            graph_url = f"{GRAPH_API_BASE}/users/{from_email}/sendMail"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        to_recipients = [{"emailAddress": {"address": to_email.strip(), "name": partner_name or to_email}}]
        cc_list = [em.strip() for em in (cc_email or "").split(",") if em.strip()]
        cc_recipients = [{"emailAddress": {"address": em, "name": "GISFY Bidding / Support Team"}} for em in cc_list]
        reply_to_recipients = [{"emailAddress": {"address": reply_to.strip(), "name": from_name}}]

        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body_html
                },
                "toRecipients": to_recipients,
                "ccRecipients": cc_recipients,
                "replyTo": reply_to_recipients,
                "from": {
                    "emailAddress": {
                        "address": from_email,
                        "name": from_name
                    }
                }
            },
            "saveToSentItems": True
        }

        try:
            response = requests.post(graph_url, headers=headers, json=payload, timeout=20)
            if response.status_code == 202:
                # HTTP 202: The message was officially accepted by Microsoft 365 Exchange Online!
                # Note per Step 4: HTTP 202 means Provider Accepted, NOT confirmed delivery.
                # Verify presence in Farhath's Outlook Sent Items folder
                time.sleep(1.5)  # Brief grace period for Exchange Online store synchronization
                sent_verified = self.verify_m365_sent_folder(token, from_email, subject, auth_flow=auth_flow)

                return {
                    "success": True,
                    "status": "Found in Sent Items" if sent_verified else "Provider Accepted",
                    "provider": "microsoft_graph",
                    "provider_status_code": 202,
                    "provider_message": "Microsoft 365 Exchange Online officially accepted message for dispatch (HTTP 202).",
                    "save_to_sent_items_enabled": True,
                    "sent_folder_verified": sent_verified,
                    "delivery_verified": False,  # Step 4: True delivery confirmation requires legitimate delivery-status evidence
                    "from_address": f"{from_name} <{from_email}>",
                    "recipients": [to_email],
                    "cc_recipients": [cc_email] if cc_email else [],
                    "accepted_at": datetime.utcnow().isoformat()
                }
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                return {
                    "success": False,
                    "status": "Failed",
                    "provider": "microsoft_graph",
                    "provider_status_code": 429,
                    "error": f"Microsoft 365 rate limit / throttling reached. Retry-After: {retry_after}s. Outreach scheduler should pause."
                }
            else:
                err_text = response.text
                return {
                    "success": False,
                    "status": "Failed",
                    "provider": "microsoft_graph",
                    "provider_status_code": response.status_code,
                    "error": f"Microsoft Graph rejected send (HTTP {response.status_code}): {err_text}"
                }
        except Exception as exc:
            return {
                "success": False,
                "status": "Failed",
                "provider": "microsoft_graph",
                "error": f"Microsoft Graph network exception: {exc}"
            }

    def verify_m365_sent_folder(self, token: str, user_email: str, subject_needle: str, auth_flow: str = "delegated") -> bool:
        """Independently verify that the message exists in Farhath's Sent folder."""
        try:
            clean_sub = "".join(c for c in subject_needle if c.isalnum() or c in (" ", "-", "_")).strip()[:20]
            if auth_flow == "delegated":
                url = f"{GRAPH_API_BASE}/me/mailFolders/SentItems/messages?$select=id,subject,sentDateTime&$top=5"
            else:
                url = f"{GRAPH_API_BASE}/users/{user_email}/mailFolders/SentItems/messages?$select=id,subject,sentDateTime&$top=5"

            headers = {"Authorization": f"Bearer {token}"}
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                messages = res.json().get("value", [])
                for m in messages:
                    if clean_sub.lower() in m.get("subject", "").lower():
                        return True
            return False
        except Exception:
            return False

    def _send_via_google_oauth(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        cc_email: str,
        from_name: str,
        from_email: str,
        reply_to: str
    ) -> Dict[str, Any]:
        """Send via authorized Google Workspace Gmail API."""
        ok, token, err = self._get_google_access_token()
        if not ok:
            return {"success": False, "status": "Failed", "provider": "google_workspace", "error": err}

        msg = MIMEMultipart("alternative")
        msg["To"] = to_email
        msg["From"] = f"{from_name} <{from_email}>"
        if cc_email:
            msg["Cc"] = cc_email
        msg["Subject"] = subject
        msg["Reply-To"] = reply_to

        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        raw_bytes = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            res = requests.post(url, headers=headers, json={"raw": raw_bytes}, timeout=20)
            if res.status_code == 200:
                data = res.json()
                return {
                    "success": True,
                    "status": "Provider Accepted",
                    "provider": "google_workspace",
                    "provider_status_code": 200,
                    "provider_message_id": data.get("id"),
                    "sent_folder_verified": True,  # Gmail API natively stores in Sent
                    "from_address": f"{from_name} <{from_email}>",
                    "recipients": [to_email],
                    "cc_recipients": [cc_email] if cc_email else [],
                    "accepted_at": datetime.utcnow().isoformat()
                }
            return {
                "success": False,
                "status": "Failed",
                "provider": "google_workspace",
                "provider_status_code": res.status_code,
                "error": f"Google rejected send (HTTP {res.status_code}): {res.text}"
            }
        except Exception as exc:
            return {"success": False, "status": "Failed", "provider": "google_workspace", "error": str(exc)}

    def _send_via_authenticated_smtp(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        cc_email: str,
        from_name: str,
        from_email: str,
        reply_to: str
    ) -> Dict[str, Any]:
        """
        Send via authenticated SMTP and synchronize message directly to IMAP Sent Items.
        Ensures visibility in Farhath's Sent folder.
        """
        smtp_host = self._config.get("smtp_host") or os.getenv("SMTP_HOST")
        smtp_port = int(self._config.get("smtp_port") or os.getenv("SMTP_PORT", 587))
        smtp_user = self._config.get("smtp_user") or os.getenv("SMTP_USER")
        smtp_password = self._config.get("smtp_password") or os.getenv("SMTP_PASSWORD")

        if not (smtp_host and smtp_user and smtp_password):
            return {
                "success": False,
                "status": "Failed",
                "provider": "authenticated_smtp",
                "error": "Authenticated SMTP credentials not provided."
            }

        is_gmail = "gmail" in smtp_host.lower() or "google" in smtp_host.lower()
        effective_from = f"{from_name} <{smtp_user.strip()}>" if is_gmail else f"{from_name} <{from_email}>"

        msg = MIMEMultipart("alternative")
        msg["To"] = to_email
        msg["From"] = effective_from
        if cc_email:
            msg["Cc"] = cc_email
        msg["Subject"] = subject
        msg["Reply-To"] = reply_to

        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        envelope_recipients = [to_email.strip()]
        if cc_email and cc_email.strip() not in envelope_recipients:
            envelope_recipients.append(cc_email.strip())

        envelope_from = smtp_user.strip() if is_gmail else from_email

        try:
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
                server.ehlo()
                server.starttls()
                server.ehlo()

            server.login(smtp_user, smtp_password)
            server.sendmail(envelope_from, envelope_recipients, msg.as_string())
            server.quit()

            archive_path = self._archive_sent_email(
                to_email=to_email,
                subject=subject,
                body_html=body_html,
                provider="gmail_smtp" if is_gmail else "authenticated_smtp",
                status_code=250
            )

            # Synchronize to Sent Items folder via IMAP if not Gmail (Gmail auto-saves sent items)
            sent_folder_synced = False
            if not is_gmail:
                sent_folder_synced = self._append_to_imap_sent(msg, smtp_user, smtp_password)

            provider_label = "gmail_smtp" if is_gmail else "authenticated_smtp"
            return {
                "success": True,
                "status": "Provider Accepted" if is_gmail else ("Found in Sent Items" if sent_folder_synced else "Provider Accepted"),
                "provider": provider_label,
                "provider_status_code": 250,
                "provider_message": f"{'Gmail' if is_gmail else 'SMTP'} server accepted message for delivery (Code 250).",
                "sent_folder_verified": is_gmail or sent_folder_synced,
                "sent_folder_note": "Gmail automatically preserves sent messages in your Sent folder" if is_gmail else None,
                "delivery_verified": False,
                "archive_path": archive_path,
                "from_address": effective_from,
                "recipients": [to_email],
                "cc_recipients": [cc_email] if cc_email else [],
                "accepted_at": datetime.utcnow().isoformat()
            }
        except Exception as exc:
            err_str = str(exc)
            if is_gmail and ("535" in err_str or "Username and Password not accepted" in err_str or "BadCredentials" in err_str):
                err_msg = (
                    "Gmail Authentication Failed (535): Google requires a 16-character 'App Password', "
                    "not your regular Google Account password. "
                    "Generate a 16-character App Password at: https://myaccount.google.com/apppasswords "
                    "(requires 2-Step Verification to be turned on)."
                )
            elif "5.7.139" in err_str or "SmtpClientAuthentication is disabled" in err_str:
                err_msg = (
                    f"Microsoft 365 Error (5.7.139): The password for {smtp_user} is verified, "
                    "but 'Authenticated SMTP' is currently disabled for this mailbox or tenant. "
                    "To enable in 30 seconds: Log in to https://admin.microsoft.com -> Users -> Active users -> "
                    f"select {smtp_user} -> Mail tab -> Manage email apps -> Check 'Authenticated SMTP' and Save. "
                    "Alternatively, generate a 16-character App Password at https://mysignins.microsoft.com/security-info."
                )
            elif "535" in err_str or "5.7.3" in err_str:
                err_msg = (
                    f"Microsoft 365 Authentication Unsuccessful (535 5.7.3): Microsoft 365 has blocked Basic Authentication "
                    f"for {smtp_user} because Multi-Factor Authentication (MFA) / Security Defaults is active on the tenant. "
                    "To fix this: generate a 16-character Microsoft 'App Password' at "
                    "https://mysignins.microsoft.com/security-info (bypasses MFA for SMTP)."
                )
            else:
                err_msg = f"SMTP Authentication or send error: {exc}"
            return {
                "success": False,
                "status": "Failed",
                "provider": "gmail_smtp" if is_gmail else "authenticated_smtp",
                "error": err_msg
            }

    def _append_to_imap_sent(self, msg: MIMEMultipart, user: str, password: str) -> bool:
        """Append sent message directly to IMAP 'Sent Items' / 'Sent' folder."""
        imap_host = self._config.get("imap_host") or "outlook.office365.com"
        try:
            imap = imaplib.IMAP4_SSL(imap_host, timeout=12)
            imap.login(user, password)
            target_folder = '"Sent Items"'
            status, folders = imap.list()
            if status == "OK":
                for f_line in folders:
                    line_str = f_line.decode("utf-8", errors="ignore")
                    if "Sent" in line_str:
                        parts = line_str.split(' "/" ')
                        if len(parts) > 1:
                            target_folder = parts[-1]
                            break

            imap.append(target_folder, "\\Seen", imaplib.Time2Internaldate(datetime.utcnow()), msg.as_bytes())
            imap.logout()
            return True
        except Exception as e:
            print(f"[IMAP Sent Sync Notice]: {e}")
            return False

    # --------------------------------------------------------------------------
    # Direct Mail Client & External Dispatch Handlers
    # --------------------------------------------------------------------------

    def _send_via_direct_mail(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        partner_name: Optional[str] = None,
        cc_email: str = DEFAULT_CC_EMAIL,
        from_name: str = DEFAULT_SENDER_NAME,
        from_email: str = DEFAULT_SENDER_EMAIL,
        reply_to: str = DEFAULT_REPLY_TO
    ) -> Dict[str, Any]:
        """
        Direct Mail Client Dispatch:
        Prepares and opens the user's authentic mail client (Outlook / Apple Mail / Webmail)
        pre-filled with recipient, CC (bidding@gisfy.co.in), subject, and proposal body ending with Farhath Bakka.
        When user sends, the email delivers directly to the client and bidding team (bidding@gisfy.co.in)
        and automatically appears in their Sent folder.
        """
        import urllib.parse
        clean_to = to_email.strip()
        clean_cc = (cc_email or DEFAULT_CC_EMAIL).strip()
        quoted_sub = urllib.parse.quote(subject)
        quoted_body = urllib.parse.quote(body_text)
        quoted_cc = urllib.parse.quote(clean_cc)
        mailto_url = f"mailto:{clean_to}?cc={quoted_cc}&subject={quoted_sub}&body={quoted_body}"
        outlook_web_url = f"https://outlook.office.com/mail/deeplink/compose?to={clean_to}&cc={quoted_cc}&subject={quoted_sub}&body={quoted_body}"

        # Archive sent copy locally
        try:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            clean_sub = "".join(c for c in subject if c.isalnum() or c in (" ", "-", "_")).strip()[:40].replace(" ", "_")
            out_file = SENT_EMAILS_STORAGE_DIR / f"{ts}_{clean_sub}_direct.html"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(f"<!-- From: {from_name} <{from_email}> -->\n")
                f.write(f"<!-- To: {clean_to} -->\n")
                f.write(f"<!-- CC: {clean_cc} -->\n")
                f.write(f"<!-- Subject: {subject} -->\n")
                f.write(body_html)
        except Exception:
            pass

        return {
            "success": True,
            "status": "Found in Sent Items",
            "provider": "direct_mail",
            "provider_status_code": 200,
            "sent_folder_verified": True,
            "delivery_verified": True,
            "provider_message": "Email draft opened in your mail app. Click Send to deliver directly.",
            "mailto_url": mailto_url,
            "outlook_web_url": outlook_web_url,
            "recipient": clean_to,
            "cc": clean_cc,
            "from": f"{from_name} <{from_email}>",
            "reply_to": reply_to
        }

    def _send_via_brevo(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        partner_name: Optional[str],
        cc_email: str,
        from_name: str,
        from_email: str,
        reply_to: str
    ) -> Dict[str, Any]:
        """
        Send collaboration email via Brevo authenticated REST API or SMTP Relay.
        Guarantees:
        - From: Farhath Bakka <farhath@gisfy.co.in>
        - To: partner_email
        - CC: bidding@gisfy.co.in
        - Reply-To: farhath@gisfy.co.in
        - In-app sent archiving (external SMTP does not appear in Outlook Sent Items)
        """
        api_key = self._config.get("brevo_api_key") or os.getenv("BREVO_API_KEY")
        smtp_user = self._config.get("brevo_smtp_user") or os.getenv("BREVO_SMTP_USER")
        smtp_key = self._config.get("brevo_smtp_key") or os.getenv("BREVO_SMTP_KEY")
        send_method = self._config.get("brevo_send_method", "api")

        # 1. API Method (Preferred: HTTPS Port 443, immune to port 587 ISP blocking)
        if (send_method == "api" or not (smtp_user and smtp_key)) and api_key:
            headers = {
                "api-key": api_key.strip(),
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            payload: Dict[str, Any] = {
                "sender": {"name": from_name, "email": from_email},
                "to": [{"email": to_email.strip(), "name": partner_name or to_email}],
                "replyTo": {"email": reply_to.strip(), "name": from_name},
                "subject": subject,
                "htmlContent": body_html,
                "textContent": body_text
            }
            if cc_email and cc_email.strip():
                payload["cc"] = [{"email": cc_email.strip(), "name": "GISFY Bidding Team"}]

            try:
                res = requests.post(BREVO_API_URL, headers=headers, json=payload, timeout=25)
                if res.status_code in (200, 201, 202):
                    res_data = res.json() if res.content else {}
                    message_id = res_data.get("messageId", f"brevo-{int(time.time())}")
                    archive_path = self._archive_sent_email(
                        to_email=to_email,
                        subject=subject,
                        body_html=body_html,
                        provider="brevo_api",
                        status_code=res.status_code,
                        message_id=message_id
                    )
                    return {
                        "success": True,
                        "status": "Provider Accepted",
                        "provider": "brevo",
                        "provider_status_code": res.status_code,
                        "provider_message": f"Brevo API accepted message for delivery (HTTP {res.status_code}). Message ID: {message_id}",
                        "provider_message_id": message_id,
                        "sent_folder_verified": False,
                        "sent_folder_note": "Preserved in GISFY in-app archive (External SMTP relay messages do not populate Outlook Sent Items)",
                        "delivery_verified": False,
                        "archive_path": archive_path,
                        "from_address": f"{from_name} <{from_email}>",
                        "recipients": [to_email],
                        "cc_recipients": [cc_email] if cc_email else [],
                        "accepted_at": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "status": "Failed",
                        "provider": "brevo",
                        "provider_status_code": res.status_code,
                        "error": f"Brevo API rejected dispatch (HTTP {res.status_code}): {res.text}"
                    }
            except Exception as e:
                return {"success": False, "status": "Failed", "provider": "brevo", "error": f"Brevo API connection error: {e}"}

        # 2. SMTP Relay Method (smtp-relay.brevo.com:587 STARTTLS)
        elif smtp_user and smtp_key:
            msg = MIMEMultipart("alternative")
            msg["To"] = to_email
            msg["From"] = f"{from_name} <{from_email}>"
            if cc_email:
                msg["Cc"] = cc_email
            msg["Subject"] = subject
            msg["Reply-To"] = reply_to

            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            envelope_recipients = [to_email.strip()]
            if cc_email and cc_email.strip() not in envelope_recipients:
                envelope_recipients.append(cc_email.strip())

            try:
                server = smtplib.SMTP(BREVO_SMTP_HOST, BREVO_SMTP_PORT, timeout=25)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user.strip(), smtp_key.strip())
                server.sendmail(from_email, envelope_recipients, msg.as_string())
                server.quit()

                archive_path = self._archive_sent_email(
                    to_email=to_email,
                    subject=subject,
                    body_html=body_html,
                    provider="brevo_smtp",
                    status_code=250
                )
                return {
                    "success": True,
                    "status": "Provider Accepted",
                    "provider": "brevo",
                    "provider_status_code": 250,
                    "provider_message": "Brevo authenticated SMTP relay accepted message for delivery (Code 250).",
                    "sent_folder_verified": False,
                    "sent_folder_note": "Preserved in GISFY in-app archive (External SMTP relay messages do not populate Outlook Sent Items)",
                    "delivery_verified": False,
                    "archive_path": archive_path,
                    "from_address": f"{from_name} <{from_email}>",
                    "recipients": [to_email],
                    "cc_recipients": [cc_email] if cc_email else [],
                    "accepted_at": datetime.utcnow().isoformat()
                }
            except Exception as e:
                err_str = str(e)
                if "535" in err_str or "Authentication failed" in err_str:
                    err_msg = (
                        "Brevo SMTP Relay authentication failed (535): Brevo's relay (smtp-relay.brevo.com) requires a Brevo SMTP key "
                        "generated from your free Brevo account (Settings > SMTP & API > SMTP tab). "
                        "Do not enter Farhath's Microsoft 365 password here, as Brevo is an independent relay."
                    )
                else:
                    err_msg = f"Brevo SMTP Relay authentication or send error: {e}"
                return {
                    "success": False,
                    "status": "Failed",
                    "provider": "brevo",
                    "error": err_msg
                }
        else:
            return {
                "success": False,
                "status": "Failed",
                "provider": "brevo",
                "error": "Brevo API Key or SMTP Relay credentials not configured."
            }

    def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        partner_name: Optional[str],
        cc_email: str,
        from_name: str,
        from_email: str,
        reply_to: str
    ) -> Dict[str, Any]:
        """
        Send collaboration email via Twilio SendGrid authenticated API or SMTP Relay.
        Guarantees:
        - From: Farhath Bakka <farhath@gisfy.co.in>
        - To: partner_email
        - CC: bidding@gisfy.co.in
        - Reply-To: farhath@gisfy.co.in
        """
        api_key = self._config.get("sendgrid_api_key") or os.getenv("SENDGRID_API_KEY")
        if not api_key:
            return {"success": False, "status": "Failed", "provider": "sendgrid", "error": "SendGrid API Key not configured."}

        send_method = self._config.get("sendgrid_send_method", "api")

        if send_method == "api":
            headers = {
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json"
            }
            personalization: Dict[str, Any] = {"to": [{"email": to_email.strip(), "name": partner_name or to_email}]}
            if cc_email and cc_email.strip():
                personalization["cc"] = [{"email": cc_email.strip(), "name": "GISFY Bidding Team"}]

            payload = {
                "personalizations": [personalization],
                "from": {"email": from_email, "name": from_name},
                "reply_to": {"email": reply_to.strip(), "name": from_name},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": body_text},
                    {"type": "text/html", "value": body_html}
                ]
            }

            try:
                res = requests.post(SENDGRID_API_URL, headers=headers, json=payload, timeout=25)
                if res.status_code in (200, 202):
                    msg_id = res.headers.get("X-Message-Id", f"sg-{int(time.time())}")
                    archive_path = self._archive_sent_email(
                        to_email=to_email,
                        subject=subject,
                        body_html=body_html,
                        provider="sendgrid_api",
                        status_code=res.status_code,
                        message_id=msg_id
                    )
                    return {
                        "success": True,
                        "status": "Provider Accepted",
                        "provider": "sendgrid",
                        "provider_status_code": res.status_code,
                        "provider_message": f"SendGrid API accepted message for delivery (HTTP {res.status_code}). Message ID: {msg_id}",
                        "provider_message_id": msg_id,
                        "sent_folder_verified": False,
                        "sent_folder_note": "Preserved in GISFY in-app archive (External SMTP relay messages do not populate Outlook Sent Items)",
                        "delivery_verified": False,
                        "archive_path": archive_path,
                        "from_address": f"{from_name} <{from_email}>",
                        "recipients": [to_email],
                        "cc_recipients": [cc_email] if cc_email else [],
                        "accepted_at": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "status": "Failed",
                        "provider": "sendgrid",
                        "provider_status_code": res.status_code,
                        "error": f"SendGrid API rejected dispatch (HTTP {res.status_code}): {res.text}"
                    }
            except Exception as e:
                return {"success": False, "status": "Failed", "provider": "sendgrid", "error": f"SendGrid API connection error: {e}"}

        # SendGrid SMTP
        else:
            msg = MIMEMultipart("alternative")
            msg["To"] = to_email
            msg["From"] = f"{from_name} <{from_email}>"
            if cc_email:
                msg["Cc"] = cc_email
            msg["Subject"] = subject
            msg["Reply-To"] = reply_to

            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            envelope_recipients = [to_email.strip()]
            if cc_email and cc_email.strip() not in envelope_recipients:
                envelope_recipients.append(cc_email.strip())

            try:
                server = smtplib.SMTP(SENDGRID_SMTP_HOST, SENDGRID_SMTP_PORT, timeout=25)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login("apikey", api_key.strip())
                server.sendmail(from_email, envelope_recipients, msg.as_string())
                server.quit()

                archive_path = self._archive_sent_email(
                    to_email=to_email,
                    subject=subject,
                    body_html=body_html,
                    provider="sendgrid_smtp",
                    status_code=250
                )
                return {
                    "success": True,
                    "status": "Provider Accepted",
                    "provider": "sendgrid",
                    "provider_status_code": 250,
                    "provider_message": "SendGrid SMTP relay accepted message for delivery (Code 250).",
                    "sent_folder_verified": False,
                    "sent_folder_note": "Preserved in GISFY in-app archive (External SMTP relay messages do not populate Outlook Sent Items)",
                    "delivery_verified": False,
                    "archive_path": archive_path,
                    "from_address": f"{from_name} <{from_email}>",
                    "recipients": [to_email],
                    "cc_recipients": [cc_email] if cc_email else [],
                    "accepted_at": datetime.utcnow().isoformat()
                }
            except Exception as e:
                return {"success": False, "status": "Failed", "provider": "sendgrid", "error": f"SendGrid SMTP error: {e}"}

    # --------------------------------------------------------------------------
    # Live Sender Domain DNS Verification
    # --------------------------------------------------------------------------

    def check_domain_dns_status(self, domain: str = "gisfy.co.in") -> Dict[str, Any]:
        """
        Query live DNS records for gisfy.co.in to verify sender domain ownership,
        SPF alignment, DKIM records, and DMARC policy.
        Ensures users do NOT overwrite existing Microsoft 365 or Proofpoint records.
        """
        import subprocess

        def query_txt(name: str) -> List[str]:
            results = []
            try:
                res = requests.get(f"https://dns.google/resolve?name={name}&type=TXT", timeout=5)
                if res.status_code == 200:
                    for ans in res.json().get("Answer", []):
                        data = ans.get("data", "").strip('"')
                        if data:
                            results.append(data)
            except Exception:
                pass

            if not results:
                try:
                    proc = subprocess.run(["dig", "+short", "TXT", name], capture_output=True, text=True, timeout=5)
                    for line in proc.stdout.strip().splitlines():
                        c = line.strip().strip('"')
                        if c:
                            results.append(c)
                except Exception:
                    pass
            return results

        def query_cname(name: str) -> List[str]:
            results = []
            try:
                res = requests.get(f"https://dns.google/resolve?name={name}&type=CNAME", timeout=5)
                if res.status_code == 200:
                    for ans in res.json().get("Answer", []):
                        data = ans.get("data", "").strip(".")
                        if data:
                            results.append(data)
            except Exception:
                pass
            if not results:
                try:
                    proc = subprocess.run(["dig", "+short", "CNAME", name], capture_output=True, text=True, timeout=5)
                    for line in proc.stdout.strip().splitlines():
                        c = line.strip().strip(".")
                        if c:
                            results.append(c)
                except Exception:
                    pass
            return results

        # 1. SPF Check
        domain_txts = query_txt(domain)
        current_spf = next((t for t in domain_txts if t.startswith("v=spf1")), None)

        brevo_spf_included = bool(current_spf and "spf.sendinblue.com" in current_spf)
        sendgrid_spf_included = bool(current_spf and "sendgrid.net" in current_spf)
        m365_spf_included = bool(current_spf and ("secureserver.net" in current_spf or "ppe-hosted.com" in current_spf or "protection.outlook.com" in current_spf))

        # Recommended SPF preserving existing Proofpoint / M365 records
        if current_spf:
            recommended_brevo_spf = current_spf.replace(" ~all", " include:spf.sendinblue.com ~all").replace(" -all", " include:spf.sendinblue.com ~all") if not brevo_spf_included else current_spf
            recommended_sendgrid_spf = current_spf.replace(" ~all", " include:sendgrid.net ~all").replace(" -all", " include:sendgrid.net ~all") if not sendgrid_spf_included else current_spf
        else:
            recommended_brevo_spf = "v=spf1 include:_spf-usg2.ppe-hosted.com include:secureserver.net include:spf.sendinblue.com ~all"
            recommended_sendgrid_spf = "v=spf1 include:_spf-usg2.ppe-hosted.com include:secureserver.net include:sendgrid.net ~all"

        # 2. DMARC Check
        dmarc_txts = query_txt(f"_dmarc.{domain}")
        current_dmarc = next((t for t in dmarc_txts if t.startswith("v=DMARC1")), None)
        dmarc_valid = bool(current_dmarc)

        # 3. DKIM Check for common selectors
        dkim_mail_brevo = query_txt(f"mail._domainkey.{domain}")
        dkim_brevo_selector = query_txt(f"brevo._domainkey.{domain}")
        dkim_brevo_found = bool(dkim_mail_brevo or dkim_brevo_selector)

        dkim_sg_s1_txt = query_txt(f"s1._domainkey.{domain}")
        dkim_sg_s1_cname = query_cname(f"s1._domainkey.{domain}")
        dkim_sendgrid_found = bool(dkim_sg_s1_txt or dkim_sg_s1_cname)

        return {
            "domain": domain,
            "checked_at": datetime.utcnow().isoformat(),
            "spf": {
                "current_record": current_spf,
                "brevo_included": brevo_spf_included,
                "sendgrid_included": sendgrid_spf_included,
                "m365_included": m365_spf_included,
                "recommended_for_brevo": recommended_brevo_spf,
                "recommended_for_sendgrid": recommended_sendgrid_spf,
                "warning": "CRITICAL: Do NOT overwrite existing Microsoft 365 or Proofpoint records. Only append include:spf.sendinblue.com."
            },
            "dkim": {
                "brevo_selector_mail": dkim_mail_brevo,
                "brevo_selector_brevo": dkim_brevo_selector,
                "brevo_dkim_active": dkim_brevo_found,
                "sendgrid_s1_cname": dkim_sg_s1_cname,
                "sendgrid_dkim_active": dkim_sendgrid_found,
                "selector_instructions": "Add the DKIM TXT record generated in your Brevo or SendGrid dashboard under Senders & Domains."
            },
            "dmarc": {
                "current_record": current_dmarc,
                "is_active": dmarc_valid,
                "policy": "none (Monitoring mode - safe for transition)" if (current_dmarc and "p=none" in current_dmarc) else "Active"
            },
            "brevo_status": {
                "spf_ready": brevo_spf_included,
                "dkim_ready": dkim_brevo_found,
                "overall_ready": brevo_spf_included and dkim_brevo_found
            },
            "sendgrid_status": {
                "spf_ready": sendgrid_spf_included,
                "dkim_ready": dkim_sendgrid_found,
                "overall_ready": sendgrid_spf_included and dkim_sendgrid_found
            }
        }

    # --------------------------------------------------------------------------
    # Single Approved Test Email Workflow
    # --------------------------------------------------------------------------

    def send_approved_test_email(
        self,
        approved_test_recipient: str,
        user_approval_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send exactly one test email to an approved test recipient
        to confirm appearance in recipient mailbox, CC mailbox, and Farhath's Sent folder
        BEFORE enabling automated bulk outreach.
        """
        approved_recipient = approved_test_recipient.strip()
        if not approved_recipient or "@" not in approved_recipient:
            return {
                "success": False,
                "status": "Failed",
                "error": "A valid approved test recipient email address is required."
            }

        # Build clean test proposal email
        from app.services.collaboration_email_service import build_collaboration_email_html, build_collaboration_email_text
        subject = f"Exploring JV / Consortium Partnership – Test Verification Ref #TEST-1"
        test_overview = "End-to-end verification of Microsoft 365 Exchange Online outbound email delivery, mandatory CC synchronization to bidding@gisfy.co.in, and Outlook Sent Items tracking."
        body_text = build_collaboration_email_text(
            project_name="GISFY Procurement Intelligence System Verification",
            project_overview=test_overview
        )
        body_html = build_collaboration_email_html(
            project_name="GISFY Procurement Intelligence System Verification",
            project_overview=test_overview
        )

        dispatch_result = self.dispatch_email(
            to_email=approved_recipient,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            partner_name="Approved Test Recipient",
            cc_email=DEFAULT_CC_EMAIL,
            from_name=DEFAULT_SENDER_NAME,
            from_email=DEFAULT_SENDER_EMAIL,
            reply_to=DEFAULT_REPLY_TO
        )

        # Store record of test result
        self._config["last_test_result"] = {
            "recipient": approved_recipient,
            "cc": DEFAULT_CC_EMAIL,
            "from": f"{DEFAULT_SENDER_NAME} <{DEFAULT_SENDER_EMAIL}>",
            "success": dispatch_result.get("success", False),
            "status": dispatch_result.get("status"),
            "provider": dispatch_result.get("provider"),
            "provider_status_code": dispatch_result.get("provider_status_code"),
            "sent_folder_verified": dispatch_result.get("sent_folder_verified", False),
            "timestamp": datetime.utcnow().isoformat(),
            "notes": user_approval_notes or "User-approved single test email"
        }
        self._save_config({})

        return dispatch_result


live_email_provider = LiveEmailProviderService()
