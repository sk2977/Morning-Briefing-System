# Production Readiness Review

**Date:** 2026-03-16
**Reviewer:** Claude Code (automated review)

## Summary

| Area | Verdict |
|------|---------|
| **Safe for public sharing?** | Yes - no secrets, PII, or credentials in committed files |
| **Production ready?** | No - suitable for personal/small-team use; needs hardening for mission-critical operation |

---

## Public Sharing Assessment: PASS

- No hardcoded secrets, API keys, or tokens in any committed file
- `.gitignore` properly excludes: `.env`, `credentials.json`, `token_*.json`, `config.yaml`, `*_emails.json`, state files
- All example files contain only placeholders (e.g., `your_work_email@gmail.com`)
- Git history is clean -- sensitive state files removed in "Prepare repo for public release" commit
- No PII in code or documentation

---

## Production Readiness Issues

### Critical

1. **Path traversal vulnerability** (`fetch_emails.py`)
   - `label` CLI argument used unsanitized in file paths: `f"token_{label}.json"`, `f"{label}_emails.json"`
   - A malicious label like `../../etc/passwd` could read/write outside the intended directory
   - **Fix:** Validate label with regex `^[a-z0-9_-]+$`

2. **No tests** (entire project)
   - Zero unit, integration, or end-to-end tests
   - No test fixtures or mocked API responses
   - Breaking changes in yfinance/Google API only discovered at runtime
   - **Fix:** Add `pytest` with mocked API responses for both scripts

3. **Division-by-zero bug** (`fetch_macro.py`, lines 115-116)
   - `daily_change = ((latest_close - prior_close) / prior_close) * 100`
   - If `prior_close` or `jan1_close` is 0 (possible on yfinance data errors), script crashes
   - **Fix:** Guard with `if prior_close and prior_close != 0:`

### High

4. **No retry logic for API calls** (`fetch_macro.py`)
   - FRED and yfinance calls have no retries or exponential backoff
   - yfinance rate-limiting is a known issue (documented in CLAUDE.md)
   - A single transient failure produces null data for the entire briefing
   - **Fix:** Add retry with backoff (e.g., `tenacity` library or manual loop)

5. **No persistent logging** (both scripts)
   - Only stdout/stderr output -- lost after scheduled task completes
   - No audit trail for debugging 6:00 AM failures
   - **Fix:** Add `logging` module with file handler

6. **No config validation** (`config.yaml`)
   - Malformed YAML or missing required keys crash with unhelpful errors
   - No schema validation for field types or required fields
   - **Fix:** Validate schema on load with clear error messages

7. **No error isolation between email accounts** (`fetch_emails.py`)
   - One account's OAuth failure blocks processing of all accounts
   - CLAUDE.md describes a per-account fallback chain, but the script doesn't implement per-account error recovery
   - **Fix:** Wrap per-account processing in try-except, continue on failure

### Medium

8. **Dependencies not pinned** (`requirements.txt`)
   - Uses `>=` minimum versions instead of exact `==` pins
   - A yfinance or google-api-python-client major version bump could break the script
   - **Fix:** Pin to exact versions: `yfinance==0.2.57`, etc.

9. **No atomic file writes** (`fetch_macro.py`, `fetch_emails.py`)
   - A crash during JSON write produces a corrupt/truncated file
   - **Fix:** Write to temp file, then `os.rename()` atomically

10. **Google token file permissions** (`fetch_emails.py`)
    - OAuth token files created with default umask (potentially world-readable)
    - Contains access tokens that grant Gmail read access
    - **Fix:** Set `chmod 0o600` after writing token files

---

## What's Already Good

- **Architecture:** Clean separation of concerns -- prompt, data fetching, config, state
- **Documentation:** Excellent CLAUDE.md, README.md, and SETUP.md
- **Secrets management:** Proper use of `.env`, `.gitignore`, and example templates
- **File encoding:** UTF-8 explicitly specified in all file I/O
- **Code structure:** Functions have docstrings, clear naming, reasonable modularity
- **Graceful degradation:** Missing FRED key logs a warning and continues

---

## Recommended Fix Priority

### Before Production Use
- [ ] Fix path traversal: validate `label` parameter in `fetch_emails.py`
- [ ] Fix division-by-zero: guard calculations in `fetch_macro.py`
- [ ] Add file-based logging to both scripts
- [ ] Validate config.yaml schema on load

### Short-Term (1-2 weeks)
- [ ] Add retry logic with exponential backoff for API calls
- [ ] Pin dependency versions
- [ ] Add per-account error isolation in `fetch_emails.py`
- [ ] Create unit tests with mocked API responses

### Medium-Term
- [ ] Implement atomic file writes for state/data files
- [ ] Restrict token file permissions
- [ ] Add CI pipeline for automated testing
- [ ] Create troubleshooting guide for known failure modes
