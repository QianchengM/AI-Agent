"""Fetch 365 ETH closes and build 72 windows with a 5-day stride."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import requests

TOTAL_DAYS = 365
CHUNK_SIZE = 10
STEP = 5
WINDOW_COUNT = 72
COINGECKO_ENDPOINT = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart"
OUTPUT_FILE = Path("coin_gecko_eth_windows_step5_72.json")


def fetch_closes(days: int = TOTAL_DAYS) -> list[tuple[str, float]]:
    """Return the latest `days` ETH/USD closing prices from CoinGecko (daily)."""

    params = {"vs_currency": "usd", "days": days, "interval": "daily"}
    response = requests.get(COINGECKO_ENDPOINT, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    prices = payload.get("prices", [])
    closes: list[tuple[str, float]] = []
    for ts_ms, close in prices[:days]:
        date = datetime.datetime.utcfromtimestamp(ts_ms / 1000).date().isoformat()
        closes.append((date, round(float(close), 2)))

    if len(closes) < days:
        raise ValueError(f"expected >= {days} closes, got {len(closes)}")

    return closes


def build_windows(closes: list[tuple[str, float]]) -> list[list[float]]:
    """Build windows that start every STEP days and span CHUNK_SIZE closes."""

    prices = [close for _, close in closes]
    required = (WINDOW_COUNT - 1) * STEP + CHUNK_SIZE
    if len(prices) < required:
        raise ValueError(f"need at least {required} prices, got {len(prices)}")

    windows: list[list[float]] = []
    for idx in range(WINDOW_COUNT):
        start = idx * STEP
        windows.append(prices[start : start + CHUNK_SIZE])

    return windows


def main() -> None:
    closes = fetch_closes()
    print("Date        Close (USD)")
    for date, close in closes:
        print(f"{date}  {close:0.2f}")

    windows = build_windows(closes)
    records = [{"id": idx, "data": window} for idx, window in enumerate(windows)]

    OUTPUT_FILE.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"{len(records)} windows written to {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
