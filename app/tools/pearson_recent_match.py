from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

RECENT_FILE = Path("app/database/coin_gecko_eth_windows_step5_72.json")


def pearson(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("sequences must have the same length")
    n = len(a)
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    numerator = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    denom_a = sum((x - mean_a) ** 2 for x in a)
    denom_b = sum((y - mean_b) ** 2 for y in b)
    denom = math.sqrt(denom_a * denom_b)
    if denom == 0:
        return 0.0
    return numerator / denom


def load_windows() -> list[dict]:
    if not RECENT_FILE.exists():
        raise FileNotFoundError(f"{RECENT_FILE} does not exist")
    return json.loads(RECENT_FILE.read_text(encoding="utf-8"))


def best_match(probe: Sequence[float]) -> Tuple[float, list[float], list[float]]:
    if len(probe) != 5:
        raise ValueError("probe must have 5 elements")
    windows = load_windows()
    best_corr = -2.0
    best_first: list[float] = []
    best_last: list[float] = []
    for window in windows:
        data = window.get("data", [])
        if len(data) < 10:
            continue
        first5 = data[:5]
        corr = pearson(probe, first5)
        if corr > best_corr:
            best_corr = corr
            best_first = first5
            best_last = data[5:10]
    if best_corr == -2.0:
        raise ValueError("no valid windows found")
    return best_corr, best_first, best_last


def get_rag_inform() -> Tuple[float, list[float], list[float]]:
    """Fetch the last five ETH closing prices and run best_match on them."""
    url = (
        "https://api.coingecko.com/api/v3/coins/ethereum/market_chart"
        "?vs_currency=usd&days=5&interval=daily"
    )
    try:
        with urlopen(url, timeout=10) as response:
            payload = json.load(response)
    except (HTTPError, URLError) as exc:
        raise RuntimeError("failed to fetch ETH prices from CoinGecko") from exc

    prices = payload.get("prices")
    if not prices or len(prices) < 5:
        raise ValueError("CoinGecko did not return enough ETH prices")

    recent_closes = [round(float(value), 2) for _, value in prices[-5:]]
    return best_match(recent_closes)
