import pandas as pd
import numpy as np


def _safe(val, default=0.0):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    return float(val)


def compute_technical_score(df: pd.DataFrame, info: dict) -> tuple[float, list[str]]:
    """Return (score 0-100, list of factual observation strings)."""
    if df is None or df.empty or len(df) < 5:
        return 50.0, ["Insufficient price history"]

    close = df["Close"].dropna()
    if len(close) < 5:
        return 50.0, ["Insufficient price history"]

    score = 50.0
    drivers = []

    price = float(close.iloc[-1])

    # 200 DMA
    dma200 = _safe(info.get("twoHundredDayAverage")) or (float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None)
    if dma200:
        if price > dma200:
            score += 12
            drivers.append(f"Price ({price:.2f}) above 200DMA ({dma200:.2f})")
        else:
            score -= 12
            drivers.append(f"Price ({price:.2f}) below 200DMA ({dma200:.2f})")

    # 50 DMA
    dma50 = _safe(info.get("fiftyDayAverage")) or (float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None)
    if dma50:
        if price > dma50:
            score += 8
            drivers.append(f"Price above 50DMA ({dma50:.2f})")
        else:
            score -= 8
            drivers.append(f"Price below 50DMA ({dma50:.2f})")

    # RSI (14)
    if len(close) >= 15:
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = float(100 - 100 / (1 + rs.iloc[-1]))
        if rsi > 70:
            score -= 5
            drivers.append(f"RSI {rsi:.0f} — overbought territory")
        elif rsi > 55:
            score += 8
            drivers.append(f"RSI {rsi:.0f} — firm momentum")
        elif rsi >= 45:
            score += 2
            drivers.append(f"RSI {rsi:.0f} — neutral momentum")
        elif rsi >= 30:
            score -= 5
            drivers.append(f"RSI {rsi:.0f} — weak momentum")
        else:
            score -= 10
            drivers.append(f"RSI {rsi:.0f} — oversold territory")

    # 52-week range position
    high52 = _safe(info.get("fiftyTwoWeekHigh"))
    low52 = _safe(info.get("fiftyTwoWeekLow"))
    if high52 and low52 and high52 > low52:
        pos = (price - low52) / (high52 - low52) * 100
        if pos >= 80:
            score += 10
            drivers.append(f"Near 52-week high — top {100-pos:.0f}% of range")
        elif pos >= 50:
            score += 4
            drivers.append(f"Upper half of 52-week range ({pos:.0f}%)")
        elif pos >= 25:
            score -= 4
            drivers.append(f"Lower half of 52-week range ({pos:.0f}%)")
        else:
            score -= 10
            drivers.append(f"Near 52-week low — bottom {pos:.0f}% of range")

    # Volume trend (recent vs average)
    avg_vol = _safe(info.get("averageVolume"))
    recent_vol = _safe(info.get("volume") or info.get("regularMarketVolume"))
    if avg_vol and recent_vol:
        ratio = recent_vol / avg_vol
        if ratio > 1.5:
            score += 5
            drivers.append(f"Volume {ratio:.1f}x above average — elevated activity")
        elif ratio < 0.5:
            score -= 3
            drivers.append(f"Volume {ratio:.1f}x below average — low activity")

    return max(0.0, min(100.0, score)), drivers


def compute_fundamental_score(info: dict) -> tuple[float, list[str]]:
    """Return (score 0-100, list of factual observation strings)."""
    score = 50.0
    drivers = []

    # Profitability: net margin
    net_margin = _safe(info.get("profitMargins"))
    if net_margin:
        if net_margin > 0.25:
            score += 12
            drivers.append(f"Net margin {net_margin*100:.1f}% — high profitability")
        elif net_margin > 0.10:
            score += 7
            drivers.append(f"Net margin {net_margin*100:.1f}% — solid profitability")
        elif net_margin > 0:
            score += 2
            drivers.append(f"Net margin {net_margin*100:.1f}% — thin but positive")
        else:
            score -= 10
            drivers.append(f"Net margin {net_margin*100:.1f}% — unprofitable")

    # ROE
    roe = _safe(info.get("returnOnEquity"))
    if roe:
        if roe > 0.25:
            score += 10
            drivers.append(f"ROE {roe*100:.1f}% — high returns on equity")
        elif roe > 0.10:
            score += 5
            drivers.append(f"ROE {roe*100:.1f}% — moderate returns")
        elif roe > 0:
            score += 1
            drivers.append(f"ROE {roe*100:.1f}% — low returns")
        else:
            score -= 8
            drivers.append(f"ROE {roe*100:.1f}% — negative returns on equity")

    # Leverage: D/E
    de = _safe(info.get("debtToEquity"))
    if de:
        de_ratio = de / 100 if de > 10 else de
        if de_ratio < 0.3:
            score += 8
            drivers.append(f"D/E {de:.0f} — low leverage")
        elif de_ratio < 1.0:
            score += 3
            drivers.append(f"D/E {de:.0f} — moderate leverage")
        elif de_ratio < 2.0:
            score -= 5
            drivers.append(f"D/E {de:.0f} — elevated leverage")
        else:
            score -= 10
            drivers.append(f"D/E {de:.0f} — high leverage")

    # Valuation: P/E
    pe = _safe(info.get("trailingPE"))
    if pe and pe > 0:
        if pe < 12:
            score += 8
            drivers.append(f"P/E {pe:.1f} — low multiple")
        elif pe < 20:
            score += 4
            drivers.append(f"P/E {pe:.1f} — moderate multiple")
        elif pe < 35:
            score -= 3
            drivers.append(f"P/E {pe:.1f} — elevated multiple")
        else:
            score -= 8
            drivers.append(f"P/E {pe:.1f} — high multiple")

    # Revenue growth
    rev_growth = _safe(info.get("revenueGrowth"))
    if rev_growth:
        if rev_growth > 0.20:
            score += 8
            drivers.append(f"Revenue growth {rev_growth*100:.1f}% YoY — strong expansion")
        elif rev_growth > 0.05:
            score += 4
            drivers.append(f"Revenue growth {rev_growth*100:.1f}% YoY — steady growth")
        elif rev_growth > 0:
            score += 1
            drivers.append(f"Revenue growth {rev_growth*100:.1f}% YoY — slow growth")
        else:
            score -= 6
            drivers.append(f"Revenue {rev_growth*100:.1f}% YoY — declining revenue")

    return max(0.0, min(100.0, score)), drivers


def get_at_a_glance(info: dict, df: pd.DataFrame) -> list[dict]:
    """Return list of {label, value, color} chips for the At a Glance panel."""
    chips = []
    price = None
    if df is not None and not df.empty:
        price = float(df["Close"].dropna().iloc[-1])

    # Trend: above/below 200DMA
    dma200 = _safe(info.get("twoHundredDayAverage"))
    if price and dma200:
        above = price > dma200
        chips.append({
            "label": "Trend",
            "value": "Above 200DMA" if above else "Below 200DMA",
            "color": "#26a69a" if above else "#ef5350",
        })

    # Momentum: RSI bucket
    if df is not None and not df.empty and len(df) >= 15:
        close = df["Close"].dropna()
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi_val = float(100 - 100 / (1 + rs.iloc[-1]))
        if rsi_val > 70:
            rsi_label, rsi_color = "Overbought (RSI>70)", "#ffa726"
        elif rsi_val > 55:
            rsi_label, rsi_color = "Firm momentum", "#26a69a"
        elif rsi_val >= 45:
            rsi_label, rsi_color = "Neutral momentum", "#aaa"
        elif rsi_val >= 30:
            rsi_label, rsi_color = "Weak momentum", "#ffa726"
        else:
            rsi_label, rsi_color = "Oversold (RSI<30)", "#ef5350"
        chips.append({"label": "Momentum", "value": f"{rsi_label} ({rsi_val:.0f})", "color": rsi_color})

    # 52W range
    high52 = _safe(info.get("fiftyTwoWeekHigh"))
    low52 = _safe(info.get("fiftyTwoWeekLow"))
    if price and high52 and low52 and high52 > low52:
        pos = (price - low52) / (high52 - low52) * 100
        chips.append({
            "label": "52W Range",
            "value": f"{pos:.0f}% of range",
            "color": "#26a69a" if pos >= 50 else "#ef5350",
        })

    # Profitability: ROE tier
    roe = _safe(info.get("returnOnEquity"))
    if roe:
        if roe > 0.25:
            roe_label, roe_color = "High ROE", "#26a69a"
        elif roe > 0.10:
            roe_label, roe_color = "Moderate ROE", "#ffa726"
        elif roe > 0:
            roe_label, roe_color = "Low ROE", "#aaa"
        else:
            roe_label, roe_color = "Negative ROE", "#ef5350"
        chips.append({"label": "Profitability", "value": f"{roe_label} ({roe*100:.1f}%)", "color": roe_color})

    # Leverage: D/E tier
    de = _safe(info.get("debtToEquity"))
    if de:
        de_r = de / 100 if de > 10 else de
        if de_r < 0.3:
            de_label, de_color = "Low leverage", "#26a69a"
        elif de_r < 1.0:
            de_label, de_color = "Moderate leverage", "#ffa726"
        else:
            de_label, de_color = "High leverage", "#ef5350"
        chips.append({"label": "Leverage", "value": f"{de_label} (D/E {de:.0f})", "color": de_color})

    # Volatility: beta
    beta = _safe(info.get("beta"))
    if beta:
        if beta < 0.8:
            b_label, b_color = "Low volatility", "#26a69a"
        elif beta <= 1.2:
            b_label, b_color = "Market-like volatility", "#aaa"
        elif beta <= 1.8:
            b_label, b_color = "Higher than market", "#ffa726"
        else:
            b_label, b_color = "High volatility", "#ef5350"
        chips.append({"label": "Volatility", "value": f"{b_label} (β={beta:.2f})", "color": b_color})

    # Valuation: P/E tier
    pe = _safe(info.get("trailingPE"))
    if pe and pe > 0:
        if pe < 12:
            pe_label, pe_color = "Low multiple", "#26a69a"
        elif pe < 20:
            pe_label, pe_color = "Fair multiple", "#aaa"
        elif pe < 35:
            pe_label, pe_color = "Elevated multiple", "#ffa726"
        else:
            pe_label, pe_color = "High multiple", "#ef5350"
        chips.append({"label": "Valuation", "value": f"{pe_label} (P/E {pe:.1f}x)", "color": pe_color})

    return chips
