# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude Desktop Cowork scheduled task that generates a daily WSJ-style morning briefing. Output is an Obsidian vault note (or local `output/` folder). One prompt file, three Python helper scripts, one state folder. No framework, no server, no CI/CD.

## Architecture

```
scheduled-prompt.md       -- The entire system: modular prompt for Claude Desktop scheduled task
briefing-data/
  config.yaml             -- User config: Gmail accounts, output path, priority senders (gitignored)
  config.example.yaml     -- Template for config.yaml (committed)
  .env                    -- API keys and email address (gitignored)
  .env.example            -- Template for .env (committed)
  fetch_macro.py          -- FRED API + Twelve Data (or yfinance fallback) -> macro_latest.json
  fetch_emails.py         -- Gmail API -> <label>_emails.json for any Gmail account
  fetch_pubmed.py         -- NCBI E-utilities -> pubmed_latest.json (publication volume trends)
  macro_latest.json       -- Overwritten each run by fetch_macro.py
  pubmed_latest.json      -- Overwritten each run by fetch_pubmed.py (gitignored)
  *_emails.json           -- Overwritten each run by fetch_emails.py (e.g. work_emails.json, personal_emails.json)
  credentials.json        -- Google OAuth credentials (gitignored)
  token_*.json            -- Per-account OAuth tokens (gitignored, auto-refresh)
  curriculum_state.json           -- Education progress tracker, updated each run (gitignored)
  curriculum_state.example.json   -- Template for curriculum_state.json (committed)
  deals_log.csv                   -- Append-only deal database, grows daily (gitignored)
  deals_log.example.csv           -- Template for deals_log.csv (committed)
  briefing_log.txt                -- Rolling 7-day FIFO log (gitignored)

Output: {obsidian_vault_path}/Morning News Briefings/YYYY-MM-DD Morning Briefing.md
        (or output/YYYY-MM-DD Morning Briefing.md if no vault configured)
```

The scheduled prompt is built as independent module blocks (`== MODULE: Name ==`). Each module has its own MCP data source, processing logic, and output format. The `== SYNTHESIZE ==` block combines all outputs into the final briefing.

## Key Commands

```bash
# Test the macro data fetcher (FRED + Twelve Data / yfinance)
cd briefing-data && python fetch_macro.py

# Test the PubMed publication volume fetcher (NCBI E-utilities)
cd briefing-data && python fetch_pubmed.py

# Fetch emails for a specific account (requires credentials.json + OAuth token)
cd briefing-data && python fetch_emails.py work your_work@gmail.com
cd briefing-data && python fetch_emails.py personal your_personal@gmail.com

# Personal email via gws CLI (optional -- requires gws CLI installed and authenticated)
gws gmail +triage                    # list unread inbox (sender, subject, date, id)
gws gmail users messages get --params '{"userId":"me","id":"<id>","format":"full"}' --format json  # read body

# API keys are read from briefing-data/.env
# FRED_API_KEY (required), TWELVE_DATA_API_KEY (optional), NCBI_API_KEY (optional)
```

## Gmail Fallback Chain

Per-account, configurable via `<label>_gmail_method` in config.yaml:
- `"auto"` (default): try MCP `gmail_search_messages` -> `python fetch_emails.py` -> `gws gmail +triage`, stop at first success
- `"mcp"` / `"fetch"` / `"gws"`: use only that method

The Python script (`fetch_emails.py`) has a 10-second timeout on token refresh and a 15-second timeout on OAuth. If `credentials.json` is from a Cloud project the account can't access, the script exits gracefully with empty JSON instead of hanging. Per-account tokens stored as `token_<label>.json`.

Setup requirements per method:
- **MCP**: Gmail MCP configured in Claude Desktop
- **fetch**: `credentials.json` in `briefing-data/` from a Google Cloud project where the account is authorized. First run opens browser for OAuth consent (saves `token_<label>.json`).
- **gws**: `gws` CLI installed and authenticated (`gws auth`; verify with `gws gmail +triage`)

## State Files

- `curriculum_state.json`: Tracks education module progress (current week/topic, subtopics covered this week, lessons completed). Updated by the scheduled prompt after each lesson. Day type derived from day-of-week: Mon=MECHANISM, Tue=CLINICAL_DATA, Wed=COMPETITIVE, Thu=DEAL_ANGLE, Fri=SYNTHESIS. Week advances on Monday boundary detection.
- `deals_log.csv`: Append-only. New deals added each morning by the Deals module. Schema: date, deal_type, buyer/acquirer, target/seller, drug_name, modality, therapeutic_area, disease, stage, upfront_m, milestone_m, total_m, region, strategic_rationale, source_url. Deduplicate by date + acquirer + target.
- `briefing_log.txt`: Max 7 entries, oldest removed first.
- `macro_latest.json`: Overwritten completely each run. If values are null, FRED or Twelve Data/yfinance API failed.
- `pubmed_latest.json`: Overwritten each run by `fetch_pubmed.py`. Contains publication counts and top articles for 5 therapeutic areas (30-day window).

## MCP Dependencies (Claude Desktop)

The scheduled prompt relies on these MCP connections:
- Gmail (fallback chain per account): MCP gmail_search_messages -> python fetch_emails.py -> gws gmail CLI
- WebSearch (built-in, free) -- PDUFA, top news, AI updates, macro fallback
- Tavily -- domain-filtered deal searches (3 queries, search_depth: advanced, time_range: week) + VC research (1 tavily_research query)
- ChEMBL -- drug mechanism enrichment for education module (optional)
- Clinical Trials -- trial status for catalysts (optional)

**No longer MCP-dependent:**
- PubMed -- replaced by `fetch_pubmed.py` (direct NCBI E-utilities API)
- Market data -- `fetch_macro.py` uses Twelve Data API (yfinance fallback)

## Conventions

- No emojis or Unicode symbols in any output (Windows cp1252 terminal compatibility)
- All file I/O uses `encoding='utf-8'`
- Context blocks required for every deal/trial/update in the briefing output
- Only include data from past 48 hours; never backfill with training data
- Tavily: 3 deal searches (search_depth: "advanced", time_range: "week", include_raw_content: false, max_results: 5) + 1 tavily_research (model: "mini") for VC (~4 calls/run, 7 credits). Discard any results with article dates older than 10 days (Tavily date filtering can leak old results).
- Tavily param pitfalls: `days` and `topic: "news"` are NOT available in the cloud MCP schema (enum is ["general"] only). `start_date`/`end_date` (YYYY-MM-DD) exist but are soft filters -- `time_range` is more reliable for date filtering. `search_depth` supports `"basic"`, `"advanced"`, `"fast"`, `"ultra-fast"`. `tavily_extract` supports a `query` param for relevance reranking. Domain filter should exclude reuters.com (too much non-biopharma noise).
- WebSearch (free) handles PDUFA, clinical readouts, top news, AI updates, macro events, and macro fallback queries (~15-17 calls/run)
- Briefing output is written as an Obsidian markdown note (or to output/ folder if no vault configured)

## Known Limitations

- **yfinance rate limiting**: Market data (S&P 500, XBI, Russell 2000) frequently returns null via yfinance. Twelve Data API is the preferred source (set `TWELVE_DATA_API_KEY` in .env). yfinance is the fallback. If both fail, use WebSearch for current market levels.
- **Tavily VC research**: `tavily_research` with `model: "auto"` over-verifies dates and often returns empty for current-week rounds. Use `model: "mini"` for actionable results.
- **credentials.json is project-scoped**: The OAuth client in `credentials.json` is tied to a specific Google Cloud project. Accounts not added as test users in that project will fail at the OAuth screen. Set the account's method to `"gws"` in config.yaml, or add the account to the Cloud project's test users.

## PUBLIC REPO
This is a public repo. Please ensure that no secret or confidential information is uploaded to github. Use gitignore, a .env file, or other necessary structures