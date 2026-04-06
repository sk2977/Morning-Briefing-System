#!/usr/bin/env python3
"""
Fetch unread emails from Microsoft 365 via Graph API (m365 CLI).
Writes <label>_emails.json to the same directory.

Usage:
    python fetch_m365_emails.py <label> <email>
    python fetch_m365_emails.py work your_work@domain.com
    python fetch_m365_emails.py personal your_personal@outlook.com

    m365 CLI path defaults to ~/GitHub/m365-cli/ (override with M365_CLI_PATH in .env).

Requires: m365 CLI with authenticated token.
If token is expired, prints device code instructions and exits gracefully.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent

load_dotenv(SCRIPT_DIR / ".env")

M365_CLI = Path(os.environ.get("M365_CLI_PATH", str(Path.home() / "GitHub" / "m365-cli")))
M365_PYTHON = M365_CLI / "venv" / "Scripts" / "python.exe"
M365_SCRIPT = M365_CLI / "m365.py"

MAX_RESULTS = 20
FULL_BODY_COUNT = 5
MAX_BODY_LENGTH = 2000
TIMEOUT_SECONDS = 30


def _run_m365(service, action, params):
    """Run m365 CLI command and return parsed JSON."""
    cmd = [
        str(M365_PYTHON), str(M365_SCRIPT),
        service, action,
        "--params", json.dumps(params),
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
        encoding="utf-8",
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        # Check if device code auth is needed
        if "use a web browser" in stderr.lower() or "user_code" in stderr.lower():
            print(f"[WARNING] m365 token expired. Re-authenticate:\n{stderr}")
            return None
        raise RuntimeError(f"m365 {service} {action} failed: {stderr}")
    return json.loads(result.stdout)


def _strip_html(html_text):
    """Strip HTML tags and decode entities to plain text."""
    text = re.sub(r"<br\s*/?>", "\n", html_text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    # Collapse whitespace but preserve newlines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text


def _truncate(text, max_len=MAX_BODY_LENGTH):
    """Truncate text with marker."""
    if len(text) > max_len:
        return text[:max_len] + "\n[...truncated]"
    return text


def fetch_emails():
    """Fetch unread emails from the past day via m365 CLI."""
    # List unread inbox emails from the past day (matches fetch_emails.py window)
    since = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    listing = _run_m365("mail", "list", {
        "top": MAX_RESULTS,
        "filter": f"isRead eq false and receivedDateTime ge {since}",
    })
    if listing is None:
        return None, "m365 token expired -- re-authenticate with device code flow"

    if not listing:
        print("[INFO] No unread emails.")
        return [], None

    print(f"[INFO] Found {len(listing)} unread emails. Fetching details...")
    emails = []

    for i, msg in enumerate(listing):
        entry = {
            "id": msg["id"],
            "snippet": msg.get("subject", "")[:100],
            "from": msg.get("from", ""),
            "subject": msg.get("subject", ""),
            "date": msg.get("date", ""),
        }

        # Fetch full body for top N emails
        if i < FULL_BODY_COUNT:
            full = _run_m365("mail", "read", {"id": msg["id"]})
            if full:
                body_raw = full.get("body", "")
                body_type = full.get("bodyType", "text")
                if body_type.lower() == "html":
                    body_raw = _strip_html(body_raw)
                entry["body"] = _truncate(body_raw)

        emails.append(entry)

    return emails, None


def _write_output(label, account, emails, note=None):
    """Write email results to JSON file."""
    output_file = SCRIPT_DIR / f"{label}_emails.json"
    output = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "account": account,
        "count": len(emails),
        "emails": emails,
    }
    if note:
        output["note"] = note
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    return output_file


def main():
    if len(sys.argv) < 3:
        print("Usage: python fetch_m365_emails.py <label> <email>")
        print("  e.g. python fetch_m365_emails.py work your_work@domain.com")
        sys.exit(1)

    label = sys.argv[1]
    account = sys.argv[2]

    print(f"[INFO] Fetching {label} emails ({account}) via m365 CLI...")

    if not M365_SCRIPT.exists():
        out = _write_output(label, account, [], note="m365 CLI not found -- skipping email fetch")
        print(f"[WARNING] m365 CLI not found at {M365_CLI} -- wrote empty {out.name}")
        return

    try:
        emails, note = fetch_emails()
    except subprocess.TimeoutExpired:
        out = _write_output(label, account, [], note=f"m365 CLI timed out after {TIMEOUT_SECONDS}s")
        print(f"[WARNING] Timeout -- wrote empty {out.name}")
        return
    except Exception as e:
        out = _write_output(label, account, [], note=f"m365 fetch failed ({e})")
        print(f"[WARNING] {e} -- wrote empty {out.name}")
        return

    if emails is None:
        out = _write_output(label, account, [], note=note)
        print(f"[WARNING] {note} -- wrote empty {out.name}")
        return

    out = _write_output(label, account, emails, note)
    print(f"[OK] Wrote {len(emails)} emails to {out.name}")


if __name__ == "__main__":
    main()
