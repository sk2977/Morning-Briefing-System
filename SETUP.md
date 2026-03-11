# Setup Guide

This file is a reference for Claude to walk you through setup. Open this repo in Claude Code or Claude Desktop and say **"help me set up"**.

---

## What Claude will do

Claude will read this file and guide you through each step interactively, asking for your inputs as needed.

## Prerequisites

- [Claude Desktop](https://claude.ai/download) with a Pro or Max plan (for Scheduled Tasks / Cowork)
- Python 3.10+ installed
- A Gmail account (personal). Work Gmail is optional.
- (Optional) An [Obsidian](https://obsidian.md/) vault for output

## Setup Steps

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Create config.yaml

Copy `briefing-data/config.example.yaml` to `briefing-data/config.yaml` and fill in:

- **personal_gmail**: Your personal Gmail address (must be connected as a Gmail MCP server in Claude Desktop)
- **work_gmail**: Your work Gmail address (optional -- leave blank to skip work email module)
- **obsidian_vault_path**: Full path to your Obsidian vault (optional -- leave blank to output to `output/` folder)
- **priority_senders**: Comma-separated names or domains to flag as HIGH priority in email triage
- **extra_skip_senders**: Additional senders to always skip (the prompt already skips common automated senders)
- **tavily_available**: Set to `false` if you don't have a Tavily MCP server configured

### 3. Create .env

Copy `briefing-data/.env.example` to `briefing-data/.env` and fill in:

- **FRED_API_KEY**: Free API key from https://fred.stlouisfed.org/docs/api/api_key.html (takes 30 seconds to register)
- **WORK_GMAIL_ADDRESS**: Same as work_gmail in config.yaml (used by the Python script)

### 4. Gmail MCP server (personal)

Connect your personal Gmail as an MCP server in Claude Desktop:
1. Open Claude Desktop Settings > MCP Servers
2. Add the Gmail MCP server and authenticate with your personal Gmail account
3. The briefing uses read-only access -- it never sends emails or creates drafts

### 5. Work Gmail API setup (optional)

If you have a work Gmail account:
1. Create a Google Cloud project at https://console.cloud.google.com/
2. Enable the Gmail API
3. Create OAuth 2.0 credentials (Desktop app type)
4. Download the credentials JSON file and save it as `briefing-data/credentials.json`
5. Run `cd briefing-data && python fetch_work_email.py` -- this will open a browser for OAuth consent on first run
6. After authenticating, `token.json` is saved and auto-refreshes on future runs

If you don't have a work Gmail account, skip this step. The briefing will work without it.

### 6. Optional MCP servers

These MCP servers enhance the briefing but are not required:
- **Tavily** -- Improves deal search quality. Without it, set `tavily_available: false` in config.yaml and WebSearch (free, built-in) handles everything.
- **PubMed** -- Publication volume trends in the education module
- **ChEMBL** -- Drug mechanism enrichment in the education module
- **Clinical Trials** -- Trial status lookups for catalyst tracking

### 7. Test the setup

```bash
cd briefing-data && python fetch_macro.py
```

If you see `[OK] Wrote macro_latest.json` with market data, your FRED key and Python environment are working.

### 8. Create the Scheduled Task

1. Open Claude Desktop
2. Go to Cowork > Scheduled Tasks
3. Create a new task and paste the contents of `scheduled-prompt.md` as the prompt
4. Set the schedule (e.g., daily at 6:30 AM on weekdays)
5. On the first run, Claude will ask for permissions to use MCP tools -- click "Always allow" for each

### 9. Customize

The briefing is modular. Each section (`== MODULE: Name ==` in `scheduled-prompt.md`) is independent. To add, remove, or modify sections, just tell Claude what you want in a conversation and it will update the code.
