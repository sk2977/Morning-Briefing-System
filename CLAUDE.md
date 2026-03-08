# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude Desktop Cowork scheduled task that generates a daily WSJ-style morning briefing at 6:00 AM ET. One prompt file, one Python helper script, one state folder. No framework, no server, no CI/CD.

## Architecture

```
scheduled-prompt.md       -- The entire system: modular prompt for Claude Desktop scheduled task
briefing-data/
  fetch_macro.py          -- FRED API + yfinance -> macro_latest.json (run by Cowork each morning)
  fetch_work_email.py     -- Gmail API -> work_emails.json for sakclawbot@gmail.com
  macro_latest.json       -- Overwritten each run by fetch_macro.py
  work_emails.json        -- Overwritten each run by fetch_work_email.py
  credentials.json        -- Google OAuth credentials (gitignored)
  token.json              -- Google OAuth token (gitignored, auto-refreshes)
  curriculum_state.json   -- Education progress tracker (updated by scheduled prompt each run)
  deals_log.csv           -- Append-only deal database (29 seeded deals, grows daily)
  briefing_log.txt        -- Rolling 7-day FIFO log
docs/migration-plan.md    -- Full migration plan from OpenClaw (reference for debugging)
```

The scheduled prompt is built as independent module blocks (`== MODULE: Name ==`). Each module has its own MCP data source, processing logic, and output format. The `== SYNTHESIZE ==` block combines all outputs into the final briefing.

## Key Commands

```bash
# Test the macro data fetcher (FRED + yfinance)
cd briefing-data && python fetch_macro.py

# FRED API key is hardcoded in fetch_macro.py (free tier)
# Can also be set via: export FRED_API_KEY=your_key
```

## State Files

- `curriculum_state.json`: Tracks education module progress (current week/topic, lessons completed). Updated by the scheduled prompt after each lesson. Day rotation: Mon=MECHANISM, Tue=CLINICAL_DATA, Wed=COMPETITIVE, Thu=DEAL_ANGLE, Fri=SYNTHESIS.
- `deals_log.csv`: Append-only. New deals added each morning by the Deals module. Schema: date, deal_type, buyer/acquirer, target/seller, drug_name, modality, therapeutic_area, disease, stage, upfront_m, milestone_m, total_m, region, strategic_rationale, source_url. Deduplicate by date + acquirer + target.
- `briefing_log.txt`: Max 7 entries, oldest removed first.
- `macro_latest.json`: Overwritten completely each run. If values are null, FRED or yfinance API failed.

## MCP Dependencies (Claude Desktop)

The scheduled prompt relies on these MCP connections:
- Gmail MCP (kimber01@gmail.com) -- email triage and newsletter scanning
- Gmail API via fetch_work_email.py (sakclawbot@gmail.com) -- work emails fetched by Python script, written to work_emails.json
- Google Calendar -- 48h event window
- WebSearch (built-in, free) -- PDUFA, AI news, jobs, macro fallback
- Tavily -- domain-filtered deal searches (3 queries) + VC research (1 query) only
- PubMed -- publication volume trends
- ChEMBL -- drug mechanism enrichment for education module
- Clinical Trials -- trial status for catalysts

## Conventions

- No emojis or Unicode symbols in any output (Windows cp1252 terminal compatibility)
- All file I/O uses `encoding='utf-8'`
- Context blocks required for every deal/trial/update in the briefing output
- Only include data from past 48 hours; never backfill with training data
- Tavily is used only for domain-filtered deal searches (days: 3) + VC research (time_range: week) (~4-5 calls/run)
- WebSearch (free) handles PDUFA, clinical readouts, AI news, jobs, macro events, and macro fallback queries (~16-19 calls/run)
