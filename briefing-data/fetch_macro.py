#!/usr/bin/env python3
"""
Fetch macro data from FRED API + yfinance.
Writes macro_latest.json to the same directory.
Called by Claude Desktop Cowork scheduled task before building the briefing.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
import yfinance as yf

OUTPUT_DIR = Path(__file__).parent
OUTPUT_FILE = OUTPUT_DIR / "macro_latest.json"

# FRED API key (free tier: https://fred.stlouisfed.org/docs/api/api_key.html)
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# (series_id, frequency) -- "monthly" series use observation[11] for YoY; "daily" skip YoY
FRED_SERIES = {
    "fed_funds_rate": ("FEDFUNDS", "monthly"),
    "ten_year_yield": ("GS10", "monthly"),
    "unemployment_rate": ("UNRATE", "monthly"),
    "cpi_index": ("CPIAUCSL", "monthly"),
    "oil_wti": ("DCOILWTICO", "daily"),
}

MARKET_TICKERS = {
    "sp500": "^GSPC",
    "xbi": "XBI",
    "russell2000": "^RUT",
}


FRED_NULL_RESULT = {"value": None, "date": None, "yoy_change": None}


def fetch_fred_series(series_id: str, frequency: str = "monthly") -> dict:
    """Fetch latest value from FRED API."""
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 13,
    }
    try:
        resp = requests.get(FRED_BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        observations = resp.json().get("observations", [])
        valid = [o for o in observations if o["value"] != "."]
        if not valid:
            return dict(FRED_NULL_RESULT)

        latest = valid[0]
        value = float(latest["value"])
        date = latest["date"]

        # YoY only meaningful for monthly series (12 observations ~ 1 year)
        yoy_change = None
        if frequency == "monthly" and len(valid) >= 12:
            year_ago = float(valid[11]["value"])
            if year_ago != 0:
                if series_id == "CPIAUCSL":
                    yoy_change = round(((value - year_ago) / year_ago) * 100, 2)
                else:
                    yoy_change = round(value - year_ago, 2)

        return {"value": round(value, 2), "date": date, "yoy_change": yoy_change}
    except Exception as e:
        print(f"[ERROR] FRED {series_id}: {e}", file=sys.stderr)
        return dict(FRED_NULL_RESULT)


MARKET_NULL_RESULT = {"price": None, "daily_change_pct": None, "ytd_change_pct": None}


def fetch_market_data() -> dict:
    """Fetch market index data via yfinance batch download."""
    results = {}
    tickers_list = list(MARKET_TICKERS.values())

    try:
        ytd_data = yf.download(tickers_list, period="ytd", progress=False, group_by="ticker")

        for name, ticker in MARKET_TICKERS.items():
            try:
                if len(MARKET_TICKERS) == 1:
                    hist = ytd_data
                else:
                    hist = ytd_data[ticker] if ticker in ytd_data.columns.get_level_values(0) else None

                if hist is None or hist.empty or len(hist) < 2:
                    results[name] = dict(MARKET_NULL_RESULT)
                    continue

                hist = hist.dropna(subset=["Close"])
                if len(hist) < 2:
                    results[name] = dict(MARKET_NULL_RESULT)
                    continue

                latest_close = float(hist["Close"].iloc[-1])
                prior_close = float(hist["Close"].iloc[-2])
                jan1_close = float(hist["Close"].iloc[0])

                daily_change = round(((latest_close - prior_close) / prior_close) * 100, 2)
                ytd_change = round(((latest_close - jan1_close) / jan1_close) * 100, 2)

                results[name] = {
                    "price": round(latest_close, 2),
                    "daily_change_pct": daily_change,
                    "ytd_change_pct": ytd_change,
                }
            except Exception as e:
                print(f"[ERROR] yfinance {ticker}: {e}", file=sys.stderr)
                results[name] = dict(MARKET_NULL_RESULT)

    except Exception as e:
        print(f"[ERROR] yfinance batch download: {e}", file=sys.stderr)
        for name in MARKET_TICKERS:
            results[name] = dict(MARKET_NULL_RESULT)

    return results


def main():
    print("[INFO] Fetching macro data...")

    fred_results = {}
    if not FRED_API_KEY:
        print("[WARNING] FRED_API_KEY not set. Skipping FRED data.")
        for name in FRED_SERIES:
            fred_results[name] = dict(FRED_NULL_RESULT)
    else:
        for name, (series_id, frequency) in FRED_SERIES.items():
            fred_results[name] = fetch_fred_series(series_id, frequency)
            val = fred_results[name]["value"]
            if val is not None:
                print(f"  [OK] {name}: {val}")
            else:
                print(f"  [WARNING] {name}: no data")

    print("[INFO] Fetching market data...")
    market_results = fetch_market_data()
    for name, data in market_results.items():
        if data["price"] is not None:
            print(f"  [OK] {name}: {data['price']} ({data['daily_change_pct']:+.2f}%)")
        else:
            print(f"  [WARNING] {name}: no data")

    output = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "fred": fred_results,
        "markets": market_results,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[OK] Wrote {OUTPUT_FILE}")
    return output


if __name__ == "__main__":
    main()
