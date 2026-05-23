import json
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

PORTFOLIO_FILE = Path(__file__).parent.parent / "data" / "portfolio.json"


def load_portfolio() -> list[dict]:
    try:
        PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
        if PORTFOLIO_FILE.exists():
            with open(PORTFOLIO_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_portfolio(holdings: list[dict]) -> None:
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(holdings, f, indent=2)


def add_holding(ticker: str, shares: float, cost_basis: float) -> None:
    holdings = load_portfolio()
    for h in holdings:
        if h["ticker"].upper() == ticker.upper():
            h["shares"] = shares
            h["cost_basis"] = cost_basis
            h["updated"] = datetime.now().isoformat()
            save_portfolio(holdings)
            return
    holdings.append({
        "ticker": ticker.upper(),
        "shares": shares,
        "cost_basis": cost_basis,
        "added": datetime.now().isoformat(),
    })
    save_portfolio(holdings)


def remove_holding(ticker: str) -> None:
    holdings = load_portfolio()
    holdings = [h for h in holdings if h["ticker"].upper() != ticker.upper()]
    save_portfolio(holdings)


def build_portfolio_df(quotes: dict) -> pd.DataFrame:
    holdings = load_portfolio()
    if not holdings:
        return pd.DataFrame()
    rows = []
    for h in holdings:
        ticker = h["ticker"]
        q = quotes.get(ticker, {})
        price = q.get("price") or 0
        shares = h.get("shares", 0)
        cost = h.get("cost_basis", 0)
        current_val = price * shares
        cost_val = cost * shares
        gain = current_val - cost_val
        gain_pct = (gain / cost_val * 100) if cost_val else 0
        rows.append({
            "ticker": ticker,
            "name": q.get("name", ticker),
            "shares": shares,
            "cost_basis": cost,
            "price": price,
            "current_value": current_val,
            "total_cost": cost_val,
            "gain_loss": gain,
            "gain_loss_pct": gain_pct,
            "sector": q.get("sector", "Unknown"),
        })
    return pd.DataFrame(rows)
