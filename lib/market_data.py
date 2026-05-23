import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

INDEX_TICKERS = {
    "^GSPC": "S&P 500",
    "^NDX": "Nasdaq 100",
    "^DJI": "Dow Jones",
    "^RUT": "Russell 2000",
    "^VIX": "VIX",
    "^TNX": "10Y Yield",
    "GC=F": "Gold",
    "CL=F": "WTI Crude",
    "BTC-USD": "Bitcoin",
    "DX-Y.NYB": "DXY",
}

SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Health Care",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLY": "Cons. Discretionary",
    "XLP": "Cons. Staples",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLB": "Materials",
    "XLC": "Comm. Services",
}

PERIOD_MAP = {
    "1D": ("1d", "5m"),
    "5D": ("5d", "15m"),
    "1M": ("1mo", "1d"),
    "3M": ("3mo", "1d"),
    "6M": ("6mo", "1d"),
    "YTD": ("ytd", "1d"),
    "1Y": ("1y", "1d"),
    "3Y": ("3y", "1wk"),
    "5Y": ("5y", "1wk"),
    "10Y": ("10y", "1mo"),
    "20Y": ("20y", "1mo"),
    "30Y": ("30y", "1mo"),
    "Max": ("max", "1mo"),
}


@st.cache_data(ttl=60)
def get_quote(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="2d", interval="1d")
        prev_close = None
        if len(hist) >= 2:
            prev_close = float(hist["Close"].iloc[-2])
        elif len(hist) == 1:
            prev_close = float(hist["Close"].iloc[0])

        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        if price is None and len(hist) > 0:
            price = float(hist["Close"].iloc[-1])

        change = info.get("regularMarketChange", 0)
        change_pct = info.get("regularMarketChangePercent", 0)
        if change_pct and abs(change_pct) > 1:
            change_pct = change_pct / 100 if abs(change_pct) > 10 else change_pct

        return {
            "ticker": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "prev_close": prev_close or info.get("previousClose"),
            "market_cap": info.get("marketCap"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "avg_volume": info.get("averageVolume"),
            "pe": info.get("trailingPE"),
            "beta": info.get("beta"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency", "USD"),
            "info": info,
        }
    except Exception:
        return {"ticker": ticker, "name": ticker, "price": None, "change": 0, "change_pct": 0}


@st.cache_data(ttl=300)
def get_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval)
        df.index = pd.to_datetime(df.index)
        if df.index.tzinfo is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def get_prev_close(ticker: str) -> float | None:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d", interval="1d")
        if len(hist) >= 2:
            return float(hist["Close"].iloc[-2])
        return None
    except Exception:
        return None


@st.cache_data(ttl=60)
def get_quotes_bulk(tickers: list) -> dict:
    results = {}
    for ticker in tickers:
        results[ticker] = get_quote(ticker)
    return results


@st.cache_data(ttl=300)
def get_history_bulk(tickers: list, period: str = "1y", interval: str = "1d") -> dict:
    results = {}
    for ticker in tickers:
        results[ticker] = get_history(ticker, period, interval)
    return results


@st.cache_data(ttl=300)
def get_etf_details(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        holdings = []
        try:
            fund_holdings = t.funds_data
            if fund_holdings is not None and hasattr(fund_holdings, "top_holdings"):
                holdings_df = fund_holdings.top_holdings
                if holdings_df is not None and not holdings_df.empty:
                    for sym, row in holdings_df.iterrows():
                        holdings.append({
                            "symbol": sym,
                            "name": row.get("Holding Name", sym),
                            "weight": float(row.get("% Assets", 0)),
                        })
        except Exception:
            pass

        sector_weights = {}
        try:
            fund_holdings = t.funds_data
            if fund_holdings is not None and hasattr(fund_holdings, "sector_weightings"):
                sw = fund_holdings.sector_weightings
                if sw is not None:
                    for sector, weight in sw.items():
                        sector_weights[sector] = float(weight) * 100
        except Exception:
            pass

        return {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName") or ticker,
            "expense_ratio": info.get("annualReportExpenseRatio") or info.get("totalExpenseRatio"),
            "aum": info.get("totalAssets"),
            "nav": info.get("navPrice"),
            "ytd_return": info.get("ytdReturn"),
            "three_year_return": info.get("threeYearAverageReturn"),
            "five_year_return": info.get("fiveYearAverageReturn"),
            "beta": info.get("beta3Year"),
            "holdings": holdings[:20],
            "sector_weights": sector_weights,
            "category": info.get("category"),
            "fund_family": info.get("fundFamily"),
            "info": info,
        }
    except Exception:
        return {"ticker": ticker, "name": ticker, "holdings": [], "sector_weights": {}}


@st.cache_data(ttl=300)
def get_stock_fundamentals(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb": info.get("priceToBook"),
            "ps": info.get("priceToSalesTrailing12Months"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "revenue": info.get("totalRevenue"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "gross_margin": info.get("grossMargins"),
            "op_margin": info.get("operatingMargins"),
            "net_margin": info.get("profitMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "debt_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "beta": info.get("beta"),
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
            "eps": info.get("trailingEps"),
            "forward_eps": info.get("forwardEps"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "float_shares": info.get("floatShares"),
            "short_ratio": info.get("shortRatio"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "50dma": info.get("fiftyDayAverage"),
            "200dma": info.get("twoHundredDayAverage"),
            "analyst_count": info.get("numberOfAnalystOpinions"),
            "target_mean": info.get("targetMeanPrice"),
            "target_high": info.get("targetHighPrice"),
            "target_low": info.get("targetLowPrice"),
            "recommendation": info.get("recommendationKey"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "employees": info.get("fullTimeEmployees"),
            "description": info.get("longBusinessSummary"),
        }
    except Exception:
        return {}


@st.cache_data(ttl=60)
def is_etf(ticker: str) -> bool:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        qt = info.get("quoteType", "").upper()
        return qt in ("ETF", "MUTUALFUND")
    except Exception:
        return False


@st.cache_data(ttl=300)
def get_top_movers() -> dict:
    gainers_tickers = ["NVDA", "META", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "AVGO", "AMD", "NFLX",
                       "CRM", "ORCL", "ADBE", "INTC", "QCOM", "TXN", "MU", "PANW", "SNOW", "PLTR"]
    quotes = get_quotes_bulk(gainers_tickers)
    valid = [q for q in quotes.values() if q.get("price") and q.get("change_pct") is not None]
    sorted_by_change = sorted(valid, key=lambda x: x.get("change_pct", 0) or 0, reverse=True)
    sorted_by_volume = sorted(valid, key=lambda x: x.get("volume", 0) or 0, reverse=True)
    return {
        "gainers": sorted_by_change[:5],
        "losers": sorted_by_change[-5:][::-1],
        "active": sorted_by_volume[:5],
    }
