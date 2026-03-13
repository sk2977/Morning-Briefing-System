# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude Desktop Cowork scheduled task that generates a daily WSJ-style morning briefing. Output is an Obsidian vault note (or local `output/` folder). One prompt file, two Python helper scripts, one state folder. No framework, no server, no CI/CD.

## Architecture

```
scheduled-prompt.md       -- The entire system: modular prompt for Claude Desktop scheduled task
briefing-data/
  config.yaml             -- User config: Gmail accounts, output path, priority senders (gitignored)
  config.example.yaml     -- Template for config.yaml (committed)
  .env                    -- API keys and email address (gitignored)
  .env.example            -- Template for .env (committed)
  fetch_macro.py          -- FRED API + yfinance -> macro_latest.json (run by Cowork each morning)
  fetch_emails.py         -- Gmail API -> <label>_emails.json for any Gmail account
  macro_latest.json       -- Overwritten each run by fetch_macro.py
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
# Test the macro data fetcher (FRED + yfinance)
cd briefing-data && python fetch_macro.py

# Fetch emails for a specific account (requires credentials.json + OAuth token)
cd briefing-data && python fetch_emails.py work your_work@gmail.com
cd briefing-data && python fetch_emails.py personal your_personal@gmail.com

# Personal email via gws CLI (optional -- requires gws CLI installed and authenticated)
gws gmail +triage                    # list unread inbox (sender, subject, date, id)
gws gmail users messages get --params '{"userId":"me","id":"<id>","format":"full"}' --format json  # read body

# FRED API key is read from briefing-data/.env
# Set via: FRED_API_KEY=your_key in .env
```

## Gmail Fallback Chain

Per-account, try in order: MCP `gmail_search_messages` (Claude Desktop) -> `python fetch_emails.py <label> <email>` (needs `credentials.json`) -> `gws gmail +triage` (needs gws auth). The Python script shares one `credentials.json` across accounts via per-account tokens (`token_<label>.json`).

## State Files

- `curriculum_state.json`: Tracks education module progress (current week/topic, lessons completed). Updated by the scheduled prompt after each lesson. Day rotation: Mon=MECHANISM, Tue=CLINICAL_DATA, Wed=COMPETITIVE, Thu=DEAL_ANGLE, Fri=SYNTHESIS.
- `deals_log.csv`: Append-only. New deals added each morning by the Deals module. Schema: date, deal_type, buyer/acquirer, target/seller, drug_name, modality, therapeutic_area, disease, stage, upfront_m, milestone_m, total_m, region, strategic_rationale, source_url. Deduplicate by date + acquirer + target.
- `briefing_log.txt`: Max 7 entries, oldest removed first.
- `macro_latest.json`: Overwritten completely each run. If values are null, FRED or yfinance API failed.

## MCP Dependencies (Claude Desktop)

The scheduled prompt relies on these MCP connections:
- Gmail (fallback chain per account): MCP gmail_search_messages -> python fetch_emails.py -> gws gmail CLI
- WebSearch (built-in, free) -- PDUFA, top news, AI updates, macro fallback
- Tavily -- domain-filtered deal searches (3 queries, search_depth: advanced, include_raw_content: true) + VC research (1 tavily_research query)
- PubMed -- publication volume trends
- ChEMBL -- drug mechanism enrichment for education module
- Clinical Trials -- trial status for catalysts

## Conventions

- No emojis or Unicode symbols in any output (Windows cp1252 terminal compatibility)
- All file I/O uses `encoding='utf-8'`
- Context blocks required for every deal/trial/update in the briefing output
- Only include data from past 48 hours; never backfill with training data
- Tavily: 3 deal searches (topic: "news", search_depth: "advanced", include_raw_content: true, start_date 7 days back) + 1 tavily_research (model: "mini") for VC. No separate tavily_extract needed -- raw_content in search results replaces it (~4 calls/run, 7 credits). Note: MCP tool schema shows topic as enum ["general"] only, but "news" works and is correct for deal searches.
- Tavily param pitfalls: `days` is NOT a valid parameter (use `start_date` or `time_range`). Domain filter should exclude reuters.com (too much non-biopharma noise)
- WebSearch (free) handles PDUFA, clinical readouts, top news, AI updates, macro events, and macro fallback queries (~15-17 calls/run)
- Briefing output is written as an Obsidian markdown note (or to output/ folder if no vault configured)

## Known Limitations

- **yfinance rate limiting**: Market data (S&P 500, XBI, Russell 2000) frequently returns null. Use WebSearch as fallback for current market levels.
- **PubMed MCP sessions**: Can terminate mid-run ("MCP session has been terminated"). If some queries fail, use prior run's data or skip.
- **Tavily VC research**: `tavily_research` with `model: "auto"` over-verifies dates and often returns empty for current-week rounds. Use `model: "mini"` for actionable results.
