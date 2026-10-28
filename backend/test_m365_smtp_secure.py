#!/usr/bin/env python3
"""
GISFY Microsoft 365 SMTP Secure Diagnostic & Verification Tool
==============================================================
Securely tests whether password-based authenticated SMTP is permitted
by Microsoft 365 tenant and mailbox policies for support@gisfy.co.in.

Security Guarantees:
- Passwords entered via prompt are hidden (no echo).
- Passwords are never logged, printed, or sent to the frontend.
- Files written are restricted to 0600 permissions.
"""

import sys
import os
import smtplib
import ssl
import getpass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import dotenv_values

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

ENV_FILE = os.path.join(BASE_DIR, ".env")

def load_env_password():
    if os.path.exists(ENV_FILE):
        vals = dotenv_values(ENV_FILE)
        p = vals.get("SMTP_PASSWORD") or os.getenv("SMTP_PASSWORD")
        if p and p.strip():
            return p.strip()
    config_file = os.path.join(BASE_DIR, ".email_credentials", "provider_config.json")
    if os.path.exists(config_file):
        try:
            import json
            with open(config_file, "r", encoding="utf-8") as f:
                c = json.load(f)
                p = c.get("smtp_password")
                if p and p.strip():
                    return p.strip()
        except Exception:
            pass
    return None

def save_env_password(password: str):
    if not os.path.exists(ENV_FILE):
        return
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    found = False
    for line in lines:
        if line.strip().startswith("SMTP_PASSWORD="):
            new_lines.append(f"SMTP_PASSWORD={password}\n")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"\nSMTP_PASSWORD={password}\n")
    
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    try:
        os.chmod(ENV_FILE, 0o600)
    except Exception:
        pass
    print("🔒 Password saved securely to backend/.env with restricted 0600 permissions.")

def run_smtp_diagnostic(password: str = None, test_recipient: str = None):
    host = "smtp.office365.com"
    port = 587
    user = "support@gisfy.co.in"
    from_addr = "GISFY Support Team <support@gisfy.co.in>"
    cc_addr = "bidding@gisfy.co.in"

    print("\n" + "=" * 70)
    print("   GISFY MICROSOFT 365 LIVE SMTP AUTHENTICATION DIAGNOSTIC")
    print("=" * 70)
    print(f"• Host:       {host}:{port}")
    print(f"• Encryption: STARTTLS")
    print(f"• Sender:     {from_addr}")
    print(f"• User:       {user}")
    print(f"• CC:         {cc_addr}")
    print("=" * 70)

    # 1. TCP Connection
    print("\n[1/4] Establishing TCP Connection to smtp.office365.com:587...")
    try:
        server = smtplib.SMTP(host, port, timeout=15)
        server.ehlo()
        print("  ✓ TCP Connection established successfully.")
    except Exception as e:
        print(f"  ❌ TCP Connection Failed: {e}")
        return False, f"TCP Connection error: {e}"

    # 2. STARTTLS Negotiation
    print("\n[2/4] Negotiating STARTTLS TLS 1.2/1.3 Encryption...")
    try:
        context = ssl.create_default_context()
        tls_code, tls_msg = server.starttls(context=context)
        server.ehlo()
        print(f"  ✓ TLS Encryption Negotiated successfully (Code {tls_code}: {tls_msg.decode('utf-8', errors='ignore')}).")
    except Exception as e:
        print(f"  ❌ TLS Negotiation Failed: {e}")
        server.quit()
        return False, f"TLS negotiation error: {e}"

    # 3. SMTP Authentication
    print(f"\n[3/4] Authenticating with Microsoft 365 for {user}...")
    auth_success = False
    auth_error_code = None
    auth_error_message = None

    try:
        auth_code, auth_msg = server.login(user, password)
        auth_success = True
        print(f"  🎉 AUTHENTICATION SUCCESSFUL! (Code {auth_code}: {auth_msg.decode('utf-8', errors='ignore')})")
        print("  ✓ Microsoft 365 Exchange Online has permitted authenticated SMTP for support@gisfy.co.in!")
    except smtplib.SMTPAuthenticationError as e:
        auth_error_code = e.smtp_code
        auth_error_message = e.smtp_error.decode("utf-8", errors="ignore") if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
        print(f"\n  ❌ AUTHENTICATION REJECTED BY MICROSOFT 365:")
        print(f"  • SMTP Status Code: {auth_error_code}")
        print(f"  • Response Details: {auth_error_message}")
    except Exception as e:
        print(f"  ❌ Authentication Exception: {type(e).__name__}: {e}")
        server.quit()
        return False, str(e)

    if not auth_success:
        server.quit()
        print("\n" + "-" * 70)
        print("📋 TECHNICAL ROOT CAUSE ANALYSIS:")
        print("-" * 70)
        if auth_error_code == 535:
            if "SmtpClientAuthentication is disabled" in auth_error_message:
                print("• Exact Cause: Authenticated SMTP is DISABLED on the mailbox.")
                print("• Solution: In Microsoft 365 Admin Center (admin.microsoft.com):")
                print("  Users > Active users > GISFY Support > Mail tab > Manage email apps >")
                print("  Check 'Authenticated SMTP' > Save changes.")
            elif "5.7.3" in auth_error_message:
                print("• Exact Cause: 5.7.3 Authentication unsuccessful.")
                print("  This error occurs under either of these conditions in Microsoft 365:")
                print("  1. The password entered does not match the active mailbox password.")
                print("  2. Multi-Factor Authentication (MFA) or Security Defaults are enforced on support@gisfy.co.in.")
                print("     When MFA/Security Defaults are active, Exchange Online automatically blocks legacy Basic Auth SMTP.")
                print("  3. Authenticated SMTP is turned off for this specific mailbox in Exchange Online.")
        print("-" * 70)
        return False, f"SMTP {auth_error_code}: {auth_error_message}"

    # 4. If Authentication Succeeded, offer Single Test Email
    print("\n[4/4] Authenticated SMTP is ACTIVE and Operational!")
    if test_recipient:
        print(f"\nDispatching single test email to approved recipient: {test_recipient}")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Exploring JV / Consortium Partnership – Test Verification Ref #TEST-1"
        msg["From"] = from_addr
        msg["To"] = test_recipient
        msg["Cc"] = cc_addr
        msg["Date"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

        from app.services.collaboration_email_service import build_collaboration_email_html, build_collaboration_email_text
        overview = "End-to-end verification of Microsoft 365 Authenticated SMTP outbound email delivery, mandatory CC to bidding@gisfy.co.in, and Sent folder synchronization."
        body_text = build_collaboration_email_text(project_name="GISFY SMTP Live Delivery Verification", project_overview=overview)
        body_html = build_collaboration_email_html(project_name="GISFY SMTP Live Delivery Verification", project_overview=overview)

        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        envelope = [test_recipient.strip(), cc_addr.strip()]
        try:
            server.sendmail(user, envelope, msg.as_string())
            print(f"  ✓ Provider Accepted message (SMTP Code 250 OK)!")
            print(f"  ✓ Dispatched to {test_recipient} (Mandatory CC: {cc_addr}).")
            
            # Sync to IMAP Sent Items
            from app.services.live_email_provider import live_email_provider
            synced = live_email_provider._append_to_imap_sent(msg, user, password)
            print(f"  ✓ Sent folder synchronization: {'Verified in Outlook Sent Items ✅' if synced else 'IMAP sync skipped'}")
        except Exception as se:
            print(f"  ❌ Send failed: {se}")
    else:
        print("No test recipient provided. Connection test complete.")

    server.quit()
    return True, "Authenticated SMTP Succeeded (Code 235)"

if __name__ == "__main__":
    env_pass = load_env_password()
    password = env_pass
    
    if not password:
        print("No password found in backend/.env.")
        if sys.stdin.isatty():
            try:
                password = getpass.getpass("Enter GISFY Support's Microsoft 365 Password (input hidden): ")
                if password:
                    save_choice = input("Save this password securely to backend/.env (0600 permissions)? [Y/n]: ").strip().lower()
                    if save_choice != 'n':
                        save_env_password(password)
            except Exception as e:
                print(f"Prompt error: {e}")
                sys.exit(1)
        else:
            print("To run non-interactively, add SMTP_PASSWORD=<your_password> to backend/.env and re-run.")
            sys.exit(1)
    else:
        print("Found securely stored SMTP_PASSWORD in backend/.env.")

    test_recip = None
    if len(sys.argv) > 1:
        test_recip = sys.argv[1].strip()

    run_smtp_diagnostic(password=password, test_recipient=test_recip)
