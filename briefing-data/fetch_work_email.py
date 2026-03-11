#!/usr/bin/env python3
"""
Fetch unread emails from work Gmail account via Gmail API.
Writes work_emails.json to the same directory.
Called by Claude Desktop Cowork scheduled task before building the briefing.

First run: opens browser for OAuth consent. Saves token.json for future runs.
"""

import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SCRIPT_DIR = Path(__file__).parent

load_dotenv(SCRIPT_DIR / ".env")
WORK_EMAIL = os.environ.get("WORK_GMAIL_ADDRESS", "your_work_email")
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"
OUTPUT_FILE = SCRIPT_DIR / "work_emails.json"


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[INFO] Refreshing expired token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[WARNING] Token refresh failed ({e}), re-authenticating...")
                creds = None
        if not creds or not creds.valid:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(f"{CREDENTIALS_FILE} not found")
            print("[INFO] Opening browser for OAuth consent...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print("[OK] Token saved.")

    return build("gmail", "v1", credentials=creds)


def fetch_emails(service, max_results=20):
    """Fetch unread emails from the past day."""
    results = service.users().messages().list(
        userId="me",
        q="is:unread newer_than:1d",
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        print("[INFO] No unread emails in the past 24 hours.")
        return []

    print(f"[INFO] Found {len(messages)} unread emails. Fetching metadata...")
    emails = []

    for msg_info in messages:
        msg = service.users().messages().get(
            userId="me",
            id=msg_info["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        emails.append({
            "id": msg_info["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        })

    return emails


def _extract_plain_text(payload):
    """Recursively walk MIME parts to find text/plain body."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        text = _extract_plain_text(part)
        if text:
            return text
    return ""


def fetch_full_message(service, msg_id):
    """Fetch full message body for a specific email."""
    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full",
    ).execute()

    body = _extract_plain_text(msg.get("payload", {}))

    # Truncate long bodies
    if len(body) > 2000:
        body = body[:2000] + "\n[...truncated]"

    return body


def _write_empty_output(reason):
    """Write an empty work_emails.json so downstream consumers don't break."""
    output = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "account": WORK_EMAIL,
        "count": 0,
        "emails": [],
        "note": reason,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"[WARNING] {reason} -- wrote empty {OUTPUT_FILE}")


def main():
    print(f"[INFO] Fetching work emails ({WORK_EMAIL})...")

    if not CREDENTIALS_FILE.exists():
        _write_empty_output("credentials.json not found -- skipping work email fetch")
        return

    try:
        service = get_gmail_service()
    except Exception as e:
        _write_empty_output(f"Gmail auth failed ({e}) -- skipping work email fetch")
        return

    emails = fetch_emails(service)

    # Fetch full body for top 5 emails (by recency)
    for email in emails[:5]:
        email["body"] = fetch_full_message(service, email["id"])

    output = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "account": WORK_EMAIL,
        "count": len(emails),
        "emails": emails,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[OK] Wrote {len(emails)} emails to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
