# Morning Briefing System

Claude Desktop Cowork scheduled task that delivers a daily WSJ-style briefing at 6:00 AM ET. One prompt file, four Python helper scripts, one state folder. No framework, no server, no CI/CD.

## What It Produces

A ~10 minute read covering:
- Actionable emails from one or two accounts (Gmail or Microsoft 365, personal and/or work)
- 9-point summary (market sentiment, top deal, VC pulse, regulatory catalysts, AI news)
- Biopharma deep dive: M&A/deal flow with context blocks, clinical trials, therapeutic area signals, VC rounds
- Macro environment: FRED rates, market indices, key dates (FOMC, PDUFA)
- AI technology updates (Claude, OpenAI, Gemini)
- Compounding education: 400-600 word daily lesson on a rotating curriculum
- What to Watch: 7 specific catalysts with dates

Output is written as an Obsidian vault note (or saved locally to `output/` if no vault is configured).

## Architecture

```
scheduled-prompt.md              -- Claude Desktop scheduled prompt (the entire system)
briefing-data/
  config.yaml                    -- Your personal config (gitignored)
  config.example.yaml            -- Template with placeholders
  .env                           -- API keys (gitignored)
  .env.example                   -- Template for .env
  fetch_macro.py                 -- FRED + Twelve Data / yfinance helper (run by Cowork each morning)
  fetch_emails.py                -- Gmail API helper (usage: python fetch_emails.py <label> <email>)
  fetch_m365_emails.py           -- Microsoft 365 helper (usage: python fetch_m365_emails.py <label> <email>)
  fetch_pubmed.py                -- NCBI E-utilities helper (publication volume trends)
  macro_latest.json              -- Written by fetch_macro.py each run (gitignored)
  pubmed_latest.json             -- Written by fetch_pubmed.py each run (gitignored)
  *_emails.json                  -- Written by fetch_emails.py or fetch_m365_emails.py each run (gitignored)
  credentials.json               -- Google OAuth credentials (gitignored)
  token_*.json                   -- Per-account OAuth tokens (gitignored)
  curriculum_state.json          -- Education progress tracker (gitignored)
  curriculum_state.example.json  -- Template for curriculum_state.json (committed)
  deals_log.csv                  -- Persistent deal database, append-only (gitignored)
  deals_log.example.csv          -- Template for deals_log.csv (committed)
  briefing_log.txt               -- Rolling 7-day log (gitignored)
output/                          -- Fallback output directory (gitignored)
```

## Quick Start

### 1. Clone and install dependencies

```bash
git clone https://github.com/sk2977/Morning-Briefing-System.git
cd Morning-Briefing-System
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp briefing-data/.env.example briefing-data/.env
# Edit .env: add your FRED API key (and optionally Twelve Data, NCBI keys)

cp briefing-data/config.example.yaml briefing-data/config.yaml
# Edit config.yaml: add your email addresses, methods, Obsidian vault path, priority senders

cp briefing-data/curriculum_state.example.json briefing-data/curriculum_state.json
cp briefing-data/deals_log.example.csv briefing-data/deals_log.csv
```

### 3. Set up email access (choose per account)

**For Microsoft 365 / Outlook accounts** (method: `"m365"`):
1. Set up an m365 CLI that exposes `mail list` and `mail read` commands
2. Authenticate and test: `python briefing-data/fetch_m365_emails.py work your_work@domain.com`
3. Set `work_email_method: "m365"` in config.yaml

**For Gmail accounts** (method: `"fetch"`, `"gws"`, `"mcp"`, or `"auto"`):
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the Gmail API
3. Create OAuth 2.0 credentials (Desktop app type)
4. Download `credentials.json` to `briefing-data/`
5. Run `python briefing-data/fetch_emails.py personal your_personal@gmail.com` once to complete OAuth flow in browser
6. Or use `gws` CLI (`gws auth`) or Gmail MCP in Claude Desktop -- see SETUP.md for details

### 4. Create Claude Desktop scheduled task

1. Open Claude Desktop -> Cowork
2. Connect the `Morning Briefing System` folder for file access
3. Click Scheduled in sidebar -> + New task
4. Paste the content of `scheduled-prompt.md` as task instructions
5. Set cadence: Weekdays, 6:00 AM

### 5. Connect MCP servers in Claude Desktop (optional)

Connect your Gmail as an MCP server in Claude Desktop (recommended for Gmail email integration). The following MCP servers are optional enhancements -- the briefing works without them:
- **Tavily** -- Better deal search quality. Without it, set `tavily_available: false` in config.yaml.
- **PubMed** -- Publication volume trends in education module
- **ChEMBL** -- Drug mechanism enrichment in education module
- **Clinical Trials** -- Trial status lookups for catalyst tracking

### 6. Approve permissions

On the first run, click "Run now" and select "Always allow" for every permission prompt (WebSearch, Gmail, Tavily, Bash, file read/write). Future runs auto-approve.

Note: Computer must be awake and Claude Desktop open at run time. If asleep, it runs when you wake up.

## Data Sources

| Source | Tool | Data | Cost |
|--------|------|------|------|
| FRED API | fetch_macro.py | Fed Funds, 10Y, unemployment, CPI, oil | Free |
| Twelve Data | fetch_macro.py | S&P 500, XBI, Russell 2000 (yfinance fallback) | Free (800 calls/day) |
| NCBI E-utilities | fetch_pubmed.py | Publication volume trends (5 therapeutic areas) | Free |
| Gmail | MCP -> fetch_emails.py -> gws CLI (fallback chain) | Email triage (Gmail) | Free |
| Microsoft 365 | fetch_m365_emails.py (m365 CLI) | Email triage (Outlook) | Free |
| WebSearch | scheduled prompt | PDUFA, AI news, macro fallback | Free |
| Tavily MCP | scheduled prompt | Deal searches (3, advanced), VC research (1) | ~4 calls/run, 7 credits |
| ChEMBL MCP | scheduled prompt | Drug mechanism enrichment (optional) | Free |
| Clinical Trials MCP | scheduled prompt | Trial status for catalysts (optional) | Free |

## Execution Order

The prompt uses a 3-phase dependency graph for parallel execution:

- **Phase 1**: All independent data fetches in parallel (~18 tool calls)
- **Phase 2**: Dependent follow-ups (read emails, extract articles, enrich with ChEMBL)
- **Phase 3**: Synthesize briefing, write state files, output to vault or file

## Education Curriculum

Rotating daily lessons on a 3-month curriculum:
- Day type derived from day-of-week: Mon=MECHANISM, Tue=CLINICAL_DATA, Wed=COMPETITIVE, Thu=DEAL_ANGLE, Fri=SYNTHESIS
- Month 1: Drug Modalities (ADCs, Gene/Cell Therapy, RNA, Bispecifics)
- Month 2: Deal Structuring & Valuation
- Month 3: Regulatory Science & Market Access

Progress tracked in `curriculum_state.json`.
