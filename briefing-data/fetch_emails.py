#!/usr/bin/env python3
"""
Fetch unread emails from a Gmail account via Gmail API.
Writes <label>_emails.json to the same directory.

Usage:
    python fetch_emails.py <label> <email_address>
    python fetch_emails.py work your_work@gmail.com
    python fetch_emails.py personal your_personal@gmail.com

Each account gets its own token file (token_<label>.json) and output file
(<label>_emails.json). All accounts share the same credentials.json OAuth client.

First run per account: opens browser for OAuth consent.
"""

import base64
import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SCRIPT_DIR = Path(__file__).parent
DEFAULT_MAX_RESULTS = 20
FULL_BODY_COUNT = 5
MAX_BODY_LENGTH = 2000
OAUTH_TIMEOUT_SECONDS = 15

load_dotenv(SCRIPT_DIR / ".env")
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"


def _parse_args():
    """Parse CLI args or fall back to env var for backward compatibility."""
    if len(sys.argv) >= 3:
        return sys.argv[1], sys.argv[2]
    if len(sys.argv) == 2:
        print("[ERROR] Usage: python fetch_emails.py <label> <email_address>")
        sys.exit(1)
    # Backward compat: no args = work account from .env
    label = "work"
    email = os.environ.get("WORK_GMAIL_ADDRESS")
    if not email:
        print("[ERROR] No args and WORK_GMAIL_ADDRESS not set in .env")
        sys.exit(1)
    return label, email


def _token_path(label):
    return SCRIPT_DIR / f"token_{label}.json"


def _output_path(label):
    return SCRIPT_DIR / f"{label}_emails.json"


def _migrate_legacy_token(label):
    """If label=work and token.json exists but token_work.json doesn't, rename it."""
    if label != "work":
        return
    legacy = SCRIPT_DIR / "token.json"
    new = _token_path(label)
    if legacy.exists() and not new.exists():
        legacy.rename(new)
        print(f"[INFO] Migrated token.json -> {new.name}")


def get_gmail_service(label):
    """Authenticate and return Gmail API service."""
    _migrate_legacy_token(label)
    token_file = _token_path(label)

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

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
            # Timeout wrapper: prevents indefinite hang when credentials.json
            # is from a project the account can't access.
            oauth_result = [None]
            oauth_error = [None]

            def _run_oauth():
                try:
                    oauth_result[0] = flow.run_local_server(port=0)
                except Exception as e:
                    oauth_error[0] = e

            t = threading.Thread(target=_run_oauth, daemon=True)
            t.start()
            t.join(timeout=OAUTH_TIMEOUT_SECONDS)
            if t.is_alive():
                raise TimeoutError(
                    f"OAuth flow timed out after {OAUTH_TIMEOUT_SECONDS}s -- "
                    "credentials.json may be from a project this account "
                    "cannot access. Use gws method instead."
                )
            if oauth_error[0]:
                raise oauth_error[0]
            creds = oauth_result[0]

        with open(token_file, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print(f"[OK] Token saved to {token_file.name}.")

    return build("gmail", "v1", credentials=creds)


def _extract_headers(msg):
    """Extract From/Subject/Date headers from a message payload."""
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    return {
        "from": headers.get("From", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", ""),
    }


def _extract_plain_text(payload):
    """Recursively walk MIME parts to find text/plain body."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        text = _extract_plain_text(part)
        if text:
            return text
    return ""


def _extract_body(msg):
    """Extract and truncate plain text body from a full message."""
    body = _extract_plain_text(msg.get("payload", {}))
    if len(body) > MAX_BODY_LENGTH:
        body = body[:MAX_BODY_LENGTH] + "\n[...truncated]"
    return body


def fetch_emails(service, max_results=DEFAULT_MAX_RESULTS):
    """Fetch unread emails from the past day.

    Top FULL_BODY_COUNT emails are fetched with full body in a single API call
    (avoiding a redundant metadata-then-full double-fetch). Remaining emails
    are fetched as metadata only.
    """
    results = service.users().messages().list(
        userId="me",
        q="is:unread newer_than:1d",
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        print("[INFO] No unread emails in the past 24 hours.")
        return []

    print(f"[INFO] Found {len(messages)} unread emails. Fetching details...")
    emails = []

    for i, msg_info in enumerate(messages):
        # Fetch top N as full (headers + body in one call), rest as metadata only
        if i < FULL_BODY_COUNT:
            msg = service.users().messages().get(
                userId="me",
                id=msg_info["id"],
                format="full",
            ).execute()
            entry = {"id": msg_info["id"], "snippet": msg.get("snippet", "")}
            entry.update(_extract_headers(msg))
            entry["body"] = _extract_body(msg)
        else:
            msg = service.users().messages().get(
                userId="me",
                id=msg_info["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()
            entry = {"id": msg_info["id"], "snippet": msg.get("snippet", "")}
            entry.update(_extract_headers(msg))

        emails.append(entry)

    return emails


def _write_output(label, email, emails, note=None):
    """Write email results to JSON file."""
    output_file = _output_path(label)
    output = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "account": email,
        "count": len(emails),
        "emails": emails,
    }
    if note:
        output["note"] = note
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    return output_file


def main():
    label, email = _parse_args()

    print(f"[INFO] Fetching {label} emails ({email})...")

    if not CREDENTIALS_FILE.exists():
        out = _write_output(label, email, [], note="credentials.json not found -- skipping email fetch")
        print(f"[WARNING] credentials.json not found -- wrote empty {out.name}")
        return

    try:
        service = get_gmail_service(label)
    except Exception as e:
        out = _write_output(label, email, [], note=f"Gmail auth failed ({e}) -- skipping email fetch")
        print(f"[WARNING] Gmail auth failed -- wrote empty {out.name}")
        return

    emails = fetch_emails(service)

    out = _write_output(label, email, emails)
    print(f"[OK] Wrote {len(emails)} emails to {out.name}")


if __name__ == "__main__":
    main()
