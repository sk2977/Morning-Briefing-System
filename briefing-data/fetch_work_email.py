#!/usr/bin/env python3
"""
Fetch unread emails from sakclawbot@gmail.com via Gmail API.
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

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SCRIPT_DIR = Path(__file__).parent
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
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"[ERROR] {CREDENTIALS_FILE} not found.", file=sys.stderr)
                sys.exit(1)
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


def fetch_full_message(service, msg_id):
    """Fetch full message body for a specific email."""
    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full",
    ).execute()

    body = ""
    payload = msg.get("payload", {})

    # Try plain text first
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    elif payload.get("parts"):
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                break

    # Truncate long bodies
    if len(body) > 2000:
        body = body[:2000] + "\n[...truncated]"

    return body


def main():
    print("[INFO] Fetching work emails (sakclawbot@gmail.com)...")

    service = get_gmail_service()
    emails = fetch_emails(service)

    # Fetch full body for top 5 emails (by recency)
    for email in emails[:5]:
        email["body"] = fetch_full_message(service, email["id"])

    output = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "account": "sakclawbot@gmail.com",
        "count": len(emails),
        "emails": emails,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[OK] Wrote {len(emails)} emails to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
