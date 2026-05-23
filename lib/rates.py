import pandas as pd
import streamlit as st
from lib.macro import get_fred_series


@st.cache_data(ttl=3600)
def get_yield_curve_snapshot() -> dict:
    maturities = {
        "3M": "DGS3MO",
        "1Y": "DGS1",
        "2Y": "DGS2",
        "5Y": "DGS5",
        "10Y": "DGS10",
        "30Y": "DGS30",
    }
    result = {}
    for label, sid in maturities.items():
        s = get_fred_series(sid, limit=5)
        if s is not None and len(s) > 0:
            result[label] = float(s.iloc[-1])
    return result
