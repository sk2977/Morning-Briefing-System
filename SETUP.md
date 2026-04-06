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

## What you get at each level

**Free tier (just Claude Desktop + FRED API key):**
- Market data (S&P 500, XBI, Russell 2000, rates, oil)
- Top news headlines, PDUFA dates, clinical readouts, AI updates (all via WebSearch)
- Biopharma deal flow and VC rounds (via WebSearch -- less precise than Tavily)
- Daily education curriculum (400-600 word lessons, 3-month rotation)
- Macro environment with key dates (FOMC, CPI, NFP)

**+ Gmail MCP server (free, recommended):**
- Email triage with priority flagging and action detection
- Newsletter intelligence (FierceBiotech, STAT, Endpoints) feeds into deal/news sections

**+ Tavily MCP server (paid, ~7 credits/run):**
- Higher-quality deal searches with domain filtering and full article content
- VC funding round research with structured output

**+ ChEMBL, Clinical Trials MCP servers (free):**
- Drug mechanism enrichment in education lessons (ChEMBL)
- Trial detail lookups for regulatory catalysts (Clinical Trials)

Note: PubMed publication trends are included in the free tier via `fetch_pubmed.py` (no MCP needed).

**+ Work Gmail via Google Cloud OAuth (free, more setup):**
- Second email account triage (e.g., work inbox alongside personal)

**+ Obsidian vault (free):**
- Briefing saved as a daily note with wikilinks that build a knowledge graph over time
- Without Obsidian, briefing prints in Cowork chat and saves to `output/` folder

## Setup Steps

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Create config and state files

```bash
cp briefing-data/config.example.yaml briefing-data/config.yaml
cp briefing-data/.env.example briefing-data/.env
cp briefing-data/curriculum_state.example.json briefing-data/curriculum_state.json
cp briefing-data/deals_log.example.csv briefing-data/deals_log.csv
```

Edit `config.yaml` and fill in:

- **personal_email**: Your personal email address (Gmail or Microsoft 365 -- leave blank to skip)
- **work_email**: Your work email address (Gmail or Microsoft 365 -- leave blank to skip)
- **personal_email_method** / **work_email_method**: How to fetch email for each account (optional, default: `"auto"`):
  - `"auto"` -- try MCP -> fetch_emails.py -> gws CLI, stop at first success (Gmail only)
  - `"m365"` -- Microsoft 365 Graph API via m365 CLI
  - `"mcp"` -- Gmail MCP server only (Claude Desktop)
  - `"fetch"` -- `fetch_emails.py` only (requires `credentials.json` from Google Cloud Console, Gmail only)
  - `"gws"` -- `gws` CLI only (requires `gws auth` setup, Gmail only)
- **obsidian_vault_path**: Full path to your Obsidian vault (optional -- leave blank to output to `output/` folder)
- **priority_senders**: Comma-separated names or domains to flag as HIGH priority in email triage
- **extra_skip_senders**: Additional senders to always skip (the prompt already skips common automated senders)
- **tavily_available**: Set to `false` if you don't have a Tavily MCP server configured

### 3. Configure .env

Edit `briefing-data/.env` and fill in:

- **FRED_API_KEY**: Free API key from https://fred.stlouisfed.org/docs/api/api_key.html (takes 30 seconds to register)
- **TWELVE_DATA_API_KEY** (optional): Free API key from https://twelvedata.com/pricing (800 calls/day). Provides reliable market data for S&P 500, XBI, Russell 2000. Without it, falls back to yfinance (often rate-limited).
- **NCBI_API_KEY** (optional): Free from https://www.ncbi.nlm.nih.gov/account/. Increases PubMed rate limit from 3/sec to 10/sec. Works without it.
- **M365_CLI_PATH** (optional): Path to your m365 CLI directory (default: `~/GitHub/m365-cli/`). Only needed if using `"m365"` email method.

### 4. Email setup (choose one method per account)

Both accounts support Gmail and Microsoft 365. Pick one method per account and set `<label>_email_method` in `config.yaml`:

**Option A: Microsoft 365 (method: "m365") -- for Outlook/Office 365 accounts**
1. Install and set up an m365 CLI that exposes `mail list` and `mail read` commands via subprocess
2. Authenticate using the CLI's device code or browser flow
3. Test: `cd briefing-data && python fetch_m365_emails.py work your_work@domain.com`
4. Set `work_email_method: "m365"` in config.yaml

**Option B: Gmail MCP server (method: "mcp") -- recommended for Claude Desktop + Gmail**
1. Open Claude Desktop Settings > MCP Servers
2. Add the Gmail MCP server and authenticate with your Gmail account
3. The briefing uses read-only access -- it never sends emails or creates drafts
4. Set `personal_email_method: "mcp"` in config.yaml

**Option C: gws CLI (method: "gws") -- recommended for Claude Code + Gmail**
1. Install `gws` CLI: see https://github.com/googleworkspace/cli
2. Run `gws auth` to authenticate
3. Verify with `gws gmail +triage` -- should show your unread inbox
4. Set `personal_email_method: "gws"` in config.yaml

**Option D: Google Cloud OAuth (method: "fetch") -- for advanced Gmail users**
1. Create a Google Cloud project at https://console.cloud.google.com/
2. Enable the Gmail API
3. Create OAuth 2.0 credentials (Desktop app type)
4. Download the credentials JSON file and save it as `briefing-data/credentials.json`
5. Run `cd briefing-data && python fetch_emails.py work your_work@gmail.com` -- opens browser for OAuth consent on first run
6. After authenticating, `token_work.json` is saved and auto-refreshes on future runs
7. Set `work_email_method: "fetch"` in config.yaml

**Note:** For Gmail methods, `credentials.json` is tied to a specific Google Cloud project. Only accounts added as test users in that project can authenticate. If OAuth hangs or fails, use "gws" method for that account instead. The script has a 10-second timeout on token refresh and a 15-second timeout on OAuth, and will exit gracefully if authentication cannot complete.

### 6. Optional MCP servers

These MCP servers enhance the briefing but are not required:
- **Tavily** -- Improves deal search quality. Without it, set `tavily_available: false` in config.yaml and WebSearch (free, built-in) handles everything.
- **ChEMBL** -- Drug mechanism enrichment in the education module
- **Clinical Trials** -- Trial status lookups for catalyst tracking

Note: PubMed is no longer an MCP dependency. Publication volume data is fetched directly via `fetch_pubmed.py` (NCBI E-utilities API).

### 7. Test the setup

```bash
cd briefing-data && python fetch_macro.py
cd briefing-data && python fetch_pubmed.py
```

If you see `[OK] Wrote macro_latest.json` and `[OK] Wrote pubmed_latest.json`, your API keys and Python environment are working.

### 8. Create the Scheduled Task

1. Open Claude Desktop
2. Go to Cowork > Scheduled Tasks
3. Create a new task and paste the contents of `scheduled-prompt.md` as the prompt
4. Set the schedule (e.g., daily at 6:30 AM on weekdays)
5. On the first run, Claude will ask for permissions to use MCP tools -- click "Always allow" for each

### 9. Customize

The briefing is modular. Each section (`== MODULE: Name ==` in `scheduled-prompt.md`) is independent. To add, remove, or modify sections, just tell Claude what you want in a conversation and it will update the code.
