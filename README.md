# Morning Briefing System

Claude Desktop Cowork scheduled task that delivers a daily WSJ-style briefing at 6:00 AM ET.

## Architecture

```
scheduled-prompt.md          -- Claude Desktop scheduled prompt (the entire system)
briefing-data/
  fetch_macro.py             -- FRED + yfinance helper (run by Cowork each morning)
  macro_latest.json          -- written by fetch_macro.py each run
  curriculum_state.json      -- education progress tracker
  deals_log.csv              -- persistent deal database (append-only)
  briefing_log.txt           -- rolling 7-day log
  archive/
    deals_openclaw.csv       -- historical deals from old system
```

## Setup

### 1. Claude Desktop MCP connections

Connect in Claude Desktop settings:
- Gmail: kimber01@gmail.com (personal)
- Gmail: sakclawbot@gmail.com (work)
- Google Calendar

### 2. Claude Desktop scheduled task

1. Open Claude Desktop -> Cowork (or Code)
2. Connect the `Morning Briefing System` folder for file access
3. Click Scheduled in sidebar -> + New task
4. Paste the content of `scheduled-prompt.md` as task instructions
5. Set cadence: Weekdays, 6:00 AM

Note: Computer must be awake and Claude Desktop open at run time. If asleep, it runs when you wake up.

## Data sources

| Source | Tool | Data |
|--------|------|------|
| FRED API | fetch_macro.py (run by Cowork) | Fed Funds, 10Y, unemployment, CPI, oil |
| yfinance | fetch_macro.py (run by Cowork) | S&P 500, XBI, Russell 2000 |
| Gmail MCP | scheduled prompt | emails from 2 accounts |
| Google Calendar MCP | scheduled prompt | events next 48h |
| Tavily MCP | scheduled prompt | deals, VC, AI news, jobs, PDUFA |
| PubMed MCP | scheduled prompt | publication volume trends |
| ChEMBL MCP | scheduled prompt | drug mechanism enrichment |
| Clinical Trials MCP | scheduled prompt | trial status for catalysts |
