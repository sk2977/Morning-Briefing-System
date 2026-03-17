#!/usr/bin/env python3
"""
Fetch publication volume data from NCBI E-utilities (PubMed).
Writes pubmed_latest.json to the same directory.
Called by Claude Desktop Cowork scheduled task before building the briefing.

Replaces the fragile PubMed MCP dependency with direct API calls.
No API key required (3 req/sec limit without key, 10 req/sec with key).
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

OUTPUT_DIR = Path(__file__).parent
OUTPUT_FILE = OUTPUT_DIR / "pubmed_latest.json"

load_dotenv(OUTPUT_DIR / ".env")

NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

WINDOW_DAYS = 30
TOP_ARTICLES = 5
REQUEST_TIMEOUT = 15

HIGH_IMPACT_JOURNALS = [
    "Nature",
    "N Engl J Med",
    "The New England journal of medicine",
    "Lancet",
    "The Lancet",
    "Cell",
    "Science",
    "JAMA",
    "BMJ",
    "Nature medicine",
    "Nature biotechnology",
]

PUBMED_QUERIES = {
    "adc": "antibody drug conjugate",
    "glp1_obesity": "GLP-1 obesity",
    "car_t": "CAR-T cell therapy",
    "crispr": "CRISPR gene editing therapeutic",
    "bispecific": "bispecific antibody cancer",
}


def _api_params(**kwargs):
    """Add API key to params if available."""
    if NCBI_API_KEY:
        kwargs["api_key"] = NCBI_API_KEY
    return kwargs


def _is_high_impact(journal_name):
    """Check if journal is in the high-impact list (case-insensitive)."""
    lower = journal_name.lower()
    return any(j.lower() in lower for j in HIGH_IMPACT_JOURNALS)


def fetch_pubmed_count(term):
    """Fetch publication count and top PMIDs for a search term."""
    params = _api_params(
        db="pubmed",
        term=term,
        reldate=WINDOW_DAYS,
        datetype="edat",
        retmode="json",
        retmax=TOP_ARTICLES,
        sort="relevance",
    )
    try:
        resp = requests.get(ESEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json().get("esearchresult", {})
        count = int(data.get("count", 0))
        pmids = data.get("idlist", [])
        return count, pmids
    except Exception as e:
        print(f"[ERROR] PubMed esearch '{term}': {e}", file=sys.stderr)
        return None, []


def fetch_article_summaries(pmids):
    """Fetch article summaries (title, journal, date) for a list of PMIDs."""
    if not pmids:
        return []
    params = _api_params(
        db="pubmed",
        id=",".join(pmids),
        retmode="json",
    )
    try:
        resp = requests.get(ESUMMARY_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        result = resp.json().get("result", {})
        articles = []
        for pmid in pmids:
            info = result.get(pmid, {})
            if not info or "error" in info:
                continue
            journal = info.get("fulljournalname", info.get("source", ""))
            articles.append({
                "pmid": pmid,
                "title": info.get("title", ""),
                "journal": journal,
                "pub_date": info.get("pubdate", ""),
                "high_impact": _is_high_impact(journal),
            })
        return articles
    except Exception as e:
        print(f"[ERROR] PubMed esummary: {e}", file=sys.stderr)
        return []


def main():
    print("[INFO] Fetching PubMed publication volumes...")
    queries_result = {}

    for key, term in PUBMED_QUERIES.items():
        count, pmids = fetch_pubmed_count(term)
        if count is not None:
            articles = fetch_article_summaries(pmids)
            queries_result[key] = {
                "term": term,
                "count": count,
                "top_articles": articles,
            }
            hi_count = sum(1 for a in articles if a.get("high_impact"))
            hi_note = f" ({hi_count} high-impact)" if hi_count else ""
            print(f"  [OK] {key}: {count} articles{hi_note}")
        else:
            queries_result[key] = {
                "term": term,
                "count": None,
                "top_articles": [],
            }
            print(f"  [WARNING] {key}: query failed")

        # Respect rate limit (3/sec without key, 10/sec with key)
        # Each query makes 2 calls (esearch + esummary), so delay between queries
        delay = 0.15 if NCBI_API_KEY else 0.7
        time.sleep(delay)

    output = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "window_days": WINDOW_DAYS,
        "queries": queries_result,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[OK] Wrote {OUTPUT_FILE}")
    return output


if __name__ == "__main__":
    main()
