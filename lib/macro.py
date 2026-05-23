import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

FRED_SERIES = {
    "GDP": {"id": "GDP", "name": "Real GDP (Bil. $)", "freq": "Quarterly"},
    "UNRATE": {"id": "UNRATE", "name": "Unemployment Rate (%)", "freq": "Monthly"},
    "CPIAUCSL": {"id": "CPIAUCSL", "name": "CPI YoY (%)", "freq": "Monthly", "pct_change": True},
    "CPILFESL": {"id": "CPILFESL", "name": "Core CPI YoY (%)", "freq": "Monthly", "pct_change": True},
    "FEDFUNDS": {"id": "FEDFUNDS", "name": "Fed Funds Rate (%)", "freq": "Monthly"},
    "T10Y2Y": {"id": "T10Y2Y", "name": "10Y-2Y Spread (bps)", "freq": "Daily"},
    "RSAFS": {"id": "RSAFS", "name": "Retail Sales (Bil. $)", "freq": "Monthly"},
    "INDPRO": {"id": "INDPRO", "name": "Industrial Production Index", "freq": "Monthly"},
    "DGS10": {"id": "DGS10", "name": "10Y Treasury Yield (%)", "freq": "Daily"},
    "DGS2": {"id": "DGS2", "name": "2Y Treasury Yield (%)", "freq": "Daily"},
    "DGS30": {"id": "DGS30", "name": "30Y Treasury Yield (%)", "freq": "Daily"},
    "DGS5": {"id": "DGS5", "name": "5Y Treasury Yield (%)", "freq": "Daily"},
    "DGS1": {"id": "DGS1", "name": "1Y Treasury Yield (%)", "freq": "Daily"},
    "DGS3MO": {"id": "DGS3MO", "name": "3M Treasury Yield (%)", "freq": "Daily"},
}


def get_fred_api():
    key = os.getenv("FRED_API_KEY")
    if not key:
        return None, "FRED_API_KEY not found in .env file."
    try:
        from fredapi import Fred
        return Fred(api_key=key), None
    except ImportError:
        return None, "fredapi package not installed. Run: pip install fredapi"
    except Exception as e:
        return None, str(e)


@st.cache_data(ttl=3600)
def get_fred_series(series_id: str, limit: int = 120) -> pd.Series | None:
    fred, err = get_fred_api()
    if fred is None:
        return None
    try:
        s = fred.get_series(series_id)
        s = s.dropna()
        if limit:
            s = s.iloc[-limit:]
        return s
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_yield_curve() -> pd.DataFrame | None:
    maturities = {
        "3M": "DGS3MO",
        "1Y": "DGS1",
        "2Y": "DGS2",
        "5Y": "DGS5",
        "10Y": "DGS10",
        "30Y": "DGS30",
    }
    fred, err = get_fred_api()
    if fred is None:
        return None
    try:
        rows = {}
        for label, sid in maturities.items():
            s = fred.get_series(sid)
            s = s.dropna()
            rows[label] = s.iloc[-1] if len(s) > 0 else None
        return pd.DataFrame([rows])
    except Exception:
        return None


def get_cpi_yoy(limit: int = 60) -> pd.Series | None:
    s = get_fred_series("CPIAUCSL", limit=limit + 12)
    if s is None or len(s) < 13:
        return None
    yoy = s.pct_change(12) * 100
    return yoy.dropna().iloc[-limit:]


def get_core_cpi_yoy(limit: int = 60) -> pd.Series | None:
    s = get_fred_series("CPILFESL", limit=limit + 12)
    if s is None or len(s) < 13:
        return None
    yoy = s.pct_change(12) * 100
    return yoy.dropna().iloc[-limit:]
