# Morning Briefing System

Claude Desktop Cowork scheduled task that delivers a daily WSJ-style briefing at 6:00 AM ET. One prompt file, one Python helper script, one state folder. No framework, no server, no CI/CD.

## What It Produces

A ~10 minute read covering:
- Calendar events and actionable emails (Gmail x2 accounts)
- 10-point summary (market sentiment, top deal, VC pulse, regulatory catalysts, AI news, jobs)
- Biopharma deep dive: M&A/deal flow with context blocks, clinical trials, therapeutic area signals, VC rounds
- Macro environment: FRED rates, market indices, key dates (FOMC, PDUFA)
- AI technology updates (Claude, OpenAI, Gemini + AI x biopharma)
- Compounding education: 400-600 word daily lesson on a rotating curriculum
- Job market: director+ pharma/biotech roles
- What to Watch: 7 specific catalysts with dates

Output is delivered in Claude Desktop and drafted to Gmail.

## Architecture

```
scheduled-prompt.md          -- Claude Desktop scheduled prompt (the entire system)
briefing-data/
  fetch_macro.py             -- FRED + yfinance helper (run by Cowork each morning)
  macro_latest.json          -- written by fetch_macro.py each run (gitignored)
  curriculum_state.json      -- education progress tracker
  deals_log.csv              -- persistent deal database (append-only)
  briefing_log.txt           -- rolling 7-day log
  archive/
    deals_openclaw.csv       -- historical deals from old system
docs/
  migration-plan.md          -- migration plan from OpenClaw (reference)
```

## Setup

### 1. Claude Desktop MCP connections

Connect in Claude Desktop settings:
- Gmail: kimber01@gmail.com (personal)
- Gmail: sakclawbot@gmail.com (work)
- Google Calendar

### 2. Create scheduled task

1. Open Claude Desktop -> Cowork
2. Connect the `Morning Briefing System` folder for file access
3. Click Scheduled in sidebar -> + New task
4. Paste the content of `scheduled-prompt.md` as task instructions
5. Set cadence: Weekdays, 6:00 AM

### 3. Approve permissions

On the first run, click "Run now" and select "Always allow" for every permission prompt (WebSearch, Gmail, Calendar, Tavily, Bash, file read/write). Future runs auto-approve. Review or revoke from the task's "Always allowed" panel.

Note: Computer must be awake and Claude Desktop open at run time. If asleep, it runs when you wake up.

## Data Sources

| Source | Tool | Data | Cost |
|--------|------|------|------|
| FRED API | fetch_macro.py | Fed Funds, 10Y, unemployment, CPI, oil | Free |
| yfinance | fetch_macro.py | S&P 500, XBI, Russell 2000 | Free |
| Gmail MCP | scheduled prompt | Emails from 2 accounts | Free |
| Google Calendar MCP | scheduled prompt | Events next 48h | Free |
| WebSearch | scheduled prompt | PDUFA, AI news, jobs, macro fallback | Free |
| Tavily MCP | scheduled prompt | Domain-filtered deal searches (3), VC research (1) | ~4-5 calls/run |
| PubMed MCP | scheduled prompt | Publication volume trends | Free |
| ChEMBL MCP | scheduled prompt | Drug mechanism enrichment | Free |
| Clinical Trials MCP | scheduled prompt | Trial status for catalysts | Free |

## Execution Order

The prompt uses a 3-phase dependency graph for parallel execution:

- **Phase 1**: All independent data fetches in parallel (~20 tool calls)
- **Phase 2**: Dependent follow-ups (read emails, extract articles, enrich with ChEMBL)
- **Phase 3**: Synthesize briefing, write state files, draft Gmail

## Education Curriculum

Rotating daily lessons on a 3-month curriculum:
- Mon=MECHANISM, Tue=CLINICAL_DATA, Wed=COMPETITIVE, Thu=DEAL_ANGLE, Fri=SYNTHESIS
- Month 1: Drug Modalities (ADCs, Gene/Cell Therapy, RNA, Bispecifics)
- Month 2: Deal Structuring & Valuation
- Month 3: Regulatory Science & Market Access

Progress tracked in `curriculum_state.json`.
