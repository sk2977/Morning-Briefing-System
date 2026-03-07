# Morning Briefing System: Migration to Claude Desktop

## Context

The Morning Briefing System runs on OpenClaw (Linux, 4 cron jobs, Telegram delivery) with known issues: v6 timeout, serial API bottlenecks, Gmail auth degradation. Migrating to Claude Desktop's schedule feature eliminates infrastructure burden, adds new MCP capabilities (Calendar, ChEMBL, Clinical Trials), and consolidates into a single scheduled prompt. Focus is on high-value output, not over-engineering.

## Decisions

- **Platform**: Claude Desktop schedule feature (MCP tools pre-wired, zero code, interactive follow-up)
- **Gmail**: Two accounts -- kimber01@gmail.com (personal) + sakclawbot@gmail.com (work)
- **Outlook**: Forward relevant emails to one of the Gmail accounts via Outlook rule
- **Macro data**: Python helper scripts for FRED API + yfinance (precise, cost-effective); Tavily for ad-hoc lookups
- **Job search**: Tavily-based replacement (5-10 targeted queries)
- **Delivery**: Claude Desktop (primary) + `gmail_create_draft` backup
- **Memory**: Local folder with bounded state files (no unbounded growth)
- **Skills**: Consider Claude Desktop skills for reusable workflows
- **Extensibility**: Modular prompt architecture -- each module is a self-contained block that can be added, modified, or removed independently
- **Cleanup**: Delete all old OpenClaw reference files after migration

## Architecture

### Extensible Modular Design

The scheduled prompt is built as **independent module blocks**. Each block is self-contained with:
- Its own data source (which MCP tool to call)
- Its own processing logic (what to extract, how to score/filter)
- Its own output format (how it appears in the briefing)

To **add a module**: insert a new `== MODULE: [Name] ==` block in the prompt with data source + output format.
To **modify a module**: edit just that block. Other modules are unaffected.
To **remove a module**: delete or comment out that block. The synthesis step skips missing modules.

The state folder (`C:\Users\skimb\GitHub\Morning Briefing System\briefing-data\`) follows the same pattern -- each module can optionally have a state file, but none are required. New modules default to stateless (live data only).

```
Prompt Structure:
  == CONFIG ==              (global rules, accounts, format rules)
  == MODULE: Calendar ==    (gcal_list_events)
  == MODULE: Email ==       (gmail_search_messages x2)
  == MODULE: Deals ==       (tavily_search + tavily_extract)
  == MODULE: Macro ==       (run fetch_macro.py + read macro_latest.json)
  == MODULE: VC ==          (tavily_research)
  == MODULE: PDUFA ==       (tavily_search + search_trials)
  == MODULE: AI Tech ==     (tavily_search)
  == MODULE: Science ==     (search_articles)
  == MODULE: Education ==   (in-prompt + ChEMBL)
  == MODULE: Jobs ==        (tavily_search)
  == SYNTHESIZE ==          (combine all module outputs into final format)
```

### Data Flow

```
[6:00 AM scheduled prompt]
    |
    +--> Python helper (FRED + yfinance) --> writes to local state folder
    |      Fed Funds, 10Y yield, unemployment, CPI, oil
    |      S&P 500, XBI, Russell 2000 (YTD + daily)
    |
    +--> Gmail MCP (2 accounts)
    |      kimber01@gmail.com: personal emails, newsletters
    |      sakclawbot@gmail.com: work emails, action items
    |
    +--> Google Calendar MCP --> meetings/deadlines next 48h
    |
    +--> Tavily MCP --> deals, VC rounds, AI news, PDUFA, jobs
    |
    +--> PubMed MCP --> science trend volumes
    |
    +--> ChEMBL MCP --> drug mechanism enrichment for deals
    |
    +--> Clinical Trials MCP --> trial status for catalysts
    |
    +--> Local state folder --> curriculum progress, macro numbers
    |
    v
[WSJ 10-Point Briefing + Gmail Draft]
```

### Local State Folder: `C:\Users\skimb\GitHub\Morning Briefing System\briefing-data\`

Bounded state files -- no unbounded growth:

| File | Purpose | Size Cap |
|------|---------|----------|
| `curriculum_state.json` | Education progress (week, topic, lessons completed) | ~5KB, fixed structure |
| `macro_latest.json` | FRED + yfinance numbers from helper script | ~1KB, overwritten daily |
| `briefing_log.txt` | Rolling 7-day log of briefing dates + topics covered | Max 7 entries, FIFO |

| `deals_log.csv` | Persistent deal database (M&A, licensing, VC, partnerships) | Append-only, grows over time (this is the one unbounded file -- valuable as a research database) |

**`deals_log.csv` schema** (expanded from current deals.csv):

```
date,deal_type,buyer/acquirer,target/seller,drug_name,modality,therapeutic_area,disease,stage,upfront_m,milestone_m,total_m,region,strategic_rationale,source_url
```

Fields:
- `date`: announcement date (YYYY-MM-DD)
- `deal_type`: acquisition | licensing | partnership | vc_series_a | vc_series_b | vc_series_c | vc_other
- `buyer/acquirer`: acquiring company or lead investor
- `target/seller`: target company or fund recipient
- `drug_name`: lead asset name if applicable
- `modality`: ADC, bispecific, CAR-T, gene therapy, RNA, small molecule, antibody, cell therapy, microbiome, etc.
- `therapeutic_area`: Oncology, Immunology, Cardiovascular, CNS, Metabolic, Rare Disease, Infectious Disease, etc.
- `disease`: specific indication (e.g., "NSCLC", "Crohn's disease", "heart failure")
- `stage`: Preclinical, Phase 1, Phase 2, Phase 3, Approved, Platform
- `upfront_m`: upfront payment in millions USD
- `milestone_m`: milestone payments in millions USD
- `total_m`: total deal value in millions USD
- `region`: US, EU, China, Global, etc.
- `strategic_rationale`: 1-2 sentence explanation of why this deal matters
- `source_url`: article URL for reference

The scheduled prompt appends new deals each morning. Seeded with existing 30+ deals from the OpenClaw deals.csv.
This CSV is the one intentionally unbounded file -- it's a research asset that grows more valuable over time.

### Python Helper Script: `C:\Users\skimb\GitHub\Morning Briefing System\briefing-data\fetch_macro.py`

Run by Cowork as the first step of the Macro module. Lightweight:
- FRED API: Fed Funds, 10Y yield, unemployment, CPI, oil (5 calls, free tier)
- yfinance: S&P 500, XBI, Russell 2000 YTD + daily change
- Writes `macro_latest.json` to the state folder
- ~50 lines of Python, runs in <10 seconds

### Module Mapping

| Module | MCP Tool(s) | Notes |
|--------|------------|-------|
| Email follow-up | `gmail_search_messages` x2 accounts + `gmail_read_message` | Score by sender priority + action keywords |
| Newsletter intel | `gmail_search_messages` (pharma/biotech keywords) | Both accounts |
| Calendar | `gcal_list_events` | NEW -- real meeting/deadline data |
| Deal intelligence | `tavily_search` (5 queries) + `tavily_extract` | Domain-filtered: fiercebiotech, endpts, statnews |
| Macro snapshot | Run `fetch_macro.py` + read `macro_latest.json` | Python helper provides precise numbers |
| AI tech updates | `tavily_search` (3 queries, 24h freshness) | Claude/OpenAI/Gemini releases |
| VC rounds | `tavily_research` | Multi-source synthesis |
| PDUFA/earnings | `tavily_search` + `search_trials` | Clinical Trials MCP is NEW capability |
| Science trends | `search_articles` (5 therapeutic areas) | Compare volumes for trend signals |
| Education | In-prompt logic + `drug_search`/`get_mechanism` | ChEMBL enrichment is NEW |
| Job search | `tavily_search` (5-10 queries) | Pharma/biotech director+ roles |

## Implementation Plan

### Phase 1: Foundation (Days 1-3)

1. **Create state folder** `C:\Users\skimb\GitHub\Morning Briefing System\briefing-data\`
2. **Write `fetch_macro.py`** -- FRED + yfinance helper script
3. **Seed `curriculum_state.json`** -- copy current state (Week 4, 19 lessons, Bispecific Antibodies)
4. **Write the scheduled prompt** -- full orchestration prompt for Claude Desktop
   - Port email scoring from `email_followup.py` lines 21-58 (SKIP_SENDERS, PRIORITY_SENDERS, ACTION_KEYWORDS)
   - Port deal queries from `scraper_v2.py` line 40 (6 Tavily query templates + domain filters)
   - Port synthesis format from `02_Cron_Prompts_Full.md` (WSJ 10-Point structure, context blocks)
   - Port education rotation from `education/generate_lesson.py` (Mon=mechanism, Tue=clinical, etc.)

### Phase 2: Gmail + Calendar Setup (Days 3-5)

1. **Connect both Gmail accounts** to Claude Desktop's Gmail MCP
2. **Connect Google Calendar** to Claude Desktop
3. **Set up Outlook forwarding rule** to one of the Gmail accounts
4. **Test email search** -- verify `gmail_search_messages` returns sufficient metadata from both accounts
5. **Test calendar** -- verify `gcal_list_events` shows upcoming meetings

### Phase 3: Test & Iterate (Days 5-7)

1. **Run the scheduled prompt manually** -- compare output against OpenClaw briefing
2. **Validate each module**: deals found? macro numbers correct? education lesson appropriate?
3. **Tune the prompt** based on output quality
4. **Enable the Claude Desktop schedule** at 6:00 AM weekdays

### Phase 4: Parallel Run & Cutover (Week 2)

1. Run both systems for 5 business days
2. Compare output quality daily
3. Disable OpenClaw crons once satisfied

## Key Files Ported From

| Source File | What Was Ported |
|-------------|-------------|
| `morning-briefing-v2/scripts/invoke_v5_final.py` | Orchestrator logic, module sequencing |
| `morning-briefing-v2/scripts/email_followup.py` | Email scoring rules (lines 21-58) |
| `pharma-intel/scripts/scraper_v2.py` | Deal search queries (line 40), extraction prompt (line 125) |
| `02_Cron_Prompts_Full.md` | v6 synthesis prompt, freshness rules, context block format |
| `education/curriculum_state.json` | Current state seeded into state folder |
| `education/generate_lesson.py` | Lesson rotation logic (day-of-week mapping) |
| `macro-economic-analyzer/scripts/invoke.py` | FRED API call patterns |
| `morning-briefing-v2/scripts/stock_movers.py` | yfinance patterns |

## Claude Desktop Skills (Optional Enhancement)

Consider packaging reusable workflows as Claude Desktop skills:
- **Deal Deep Dive**: given a company/drug name, run ChEMBL + Clinical Trials + Tavily for a full analysis
- **Catalyst Check**: search upcoming PDUFA dates and trial readouts for a specific company
- **Macro Refresh**: re-run the macro snapshot on demand

These are optional -- build the core briefing first, then extract skills from patterns that prove useful.

## Final Briefing Output Format

The scheduled prompt produces this exact structure. ~10 minute read. No emojis. No template filler -- every line must be grounded in fresh data (past 48 hours) or state files.

```
================================================================
MORNING BRIEFING -- [Today's Date]
~10 min read | 6:00 AM ET
================================================================

CRITICAL EVENTS (next 48h)
--------------------------
[From Google Calendar: interviews, deadlines, important meetings]
[If none: omit this section entirely]

EMAIL -- ACTION NEEDED
----------------------
[From Gmail (both accounts): top 5 actionable emails, sorted by urgency]
[Each entry: sender | subject | action needed | urgency (HIGH/MEDIUM/LOW)]
[Skip: noreply, newsletters, marketing, LinkedIn notifications]
[Priority senders flagged: shannon, corey, jenna, simon, philip, ali, herman, peter, yasmin]

TODAY'S 10 POINTS
-----------------
1. [Market/XBI sentiment -- from macro_latest.json]
2. [Top biopharma deal -- from Tavily deal search]
   > Modality: [type, mechanism, advantages/limitations]
   > Disease: [what it is, patient population, burden]
   > Unmet need: [what current treatments miss]
   > Competition: [key players, late-stage threats]
   > Why it matters: [strategic rationale, market signal]
3. [Therapeutic area signal -- pattern from multiple deals/trials]
4. [VC pulse -- notable round >$10M from tavily_research]
5. [Clinical/regulatory catalyst -- from Tavily + Clinical Trials MCP]
6. [AI technology update -- from Tavily AI searches]
7. [Newsletter signal -- from Gmail newsletter scan]
8. [Job market intel -- from Tavily job search]
9. [Macro context -- from macro_latest.json]
10. YOUR MOVE: [Most actionable item today -- specific, concrete next step]

----------------------------------------------------------------
BIOPHARMA
----------------------------------------------------------------

M&A / Deal Flow (past 7 days)
Company News & Strategic Moves (past 48h)
Clinical Trial Results & Regulatory (past 48h)
Therapeutic Area Signals
VC / Private Markets (past 48h)

----------------------------------------------------------------
MACRO ENVIRONMENT
----------------------------------------------------------------

Rates & Fixed Income
Labor & Inflation
Market Context for Biotech
Key Dates

----------------------------------------------------------------
AI TECHNOLOGY
----------------------------------------------------------------

Model Releases & Updates (past 48h)
AI x Biopharma (past 48h)
Strategic Signal

----------------------------------------------------------------
COMPOUNDING EDUCATION
----------------------------------------------------------------

Week [N]: [Topic Name]
[Day type]: [Subtopic]
[400-600 word lesson]
Connections to prior lessons

----------------------------------------------------------------
JOB MARKET
----------------------------------------------------------------

Top Matches (pharma/biotech, Director+ level)

----------------------------------------------------------------
WHAT TO WATCH
----------------------------------------------------------------

[7 specific catalysts with dates]

================================================================
Sources: Gmail, Google Calendar, Tavily, FRED, yfinance, PubMed, ChEMBL, ClinicalTrials.gov
================================================================
```

### Format Rules

1. **Freshness**: Only include news/deals from past 48 hours. If no fresh data for a section, write "No new developments in the past 48 hours" -- never backfill with training data
2. **Context blocks**: Required for EVERY deal, trial result, pipeline update, or strategic move. No exceptions. Full context every time, even for well-known modalities
3. **No emojis**: Use text headers and dashes for formatting. No Unicode symbols.
4. **Specificity**: Cite data dates, source names, exact numbers. No vague claims.
5. **YOUR MOVE (#10)**: Always concrete and actionable -- "Review X", "Follow up on Y", "Watch Z at [level]"
6. **Education**: Use day-of-week rotation (Mon=mechanism, Tue=clinical data, Wed=competitive, Thu=deal/valuation, Fri=weekly synthesis)
7. **Omit empty sections**: If no fresh data, skip the section entirely rather than padding

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Schedule feature timeout | Batch Tavily queries; test with subset first |
| Tavily rate limits (15+ searches) | Use `tavily_research` for multi-source synthesis where possible |
| Curriculum state drift | Bounded JSON in state folder; prompt updates it each run |
| Memory/state bloat | Fixed-size state files + 7-day rolling log; only deals_log.csv grows (intentional research database) |
| Two Gmail accounts auth | Built-in MCP supports one account; forward second account or use custom multi-account MCP |

## Cleanup: Delete Old OpenClaw Files

After migration is validated (Phase 4 complete), delete `_OLD_OpenClaw_DELETE_AFTER_MIGRATION/` folder.

Files preserved before deletion:
- `education/curriculum_state.json` -> seeded into `briefing-data/curriculum_state.json`
- `pharma-intel/deals/deals.csv` -> archived at `briefing-data/archive/deals_openclaw.csv`

## Post-Launch Optimization (2026-03-07)

Changes made after first scheduled run:

1. **Cost reduction**: Tavily calls reduced from ~15-20 to ~4-5 per run. Deals: 5->3 queries (consolidated overlapping terms). PDUFA, AI Tech, Jobs, Macro fallback switched to free WebSearch. Tavily retained only for domain-filtered deal searches (include_domains is critical) and VC research (multi-source synthesis).

2. **Freshness enforcement**: All Tavily calls now use `days: 1` and `topic: "news"`. All WebSearch queries append "past 24 hours" or "today [date]" since WebSearch has no date parameter.

3. **Permissions fix**: Added permissions note to CONFIG section. User must "Always allow" all tools on first manual run to prevent scheduled task stalling.

4. **Parallel execution**: Added EXECUTION ORDER section with 3 phases. Phase 1 batches all independent data-fetch calls. Phase 2 runs dependent follow-ups. Phase 3 synthesizes and writes.

5. **Jobs simplification**: Reduced from 5-10 Tavily queries to 3 WebSearch queries.

6. **Git repo initialized**: `.gitignore` excludes `macro_latest.json` and `_OLD_OpenClaw_DELETE_AFTER_MIGRATION/`. Private GitHub repo for backup.

## Verification

1. Run `fetch_macro.py` manually, confirm `macro_latest.json` has current FRED + yfinance data
2. Run the scheduled prompt manually in Claude Desktop, compare against today's OpenClaw briefing
3. Check Gmail MCP returns emails with sufficient metadata
4. Verify Tavily freshness filters produce same-day deal results
5. Confirm calendar events appear for next-48h window
6. Verify education lesson matches expected day-of-week rotation
7. Run parallel with OpenClaw for 1 week before cutover
