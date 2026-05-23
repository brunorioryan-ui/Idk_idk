import numpy as np
import pandas as pd


def compute_etf_risk_score(df: pd.DataFrame, holdings: list, beta: float | None = None) -> tuple[float, str]:
    """
    Compute ETF risk score 0-100 based on:
    - Volatility (annualized std dev)
    - Max drawdown
    - Concentration (top 10 holdings weight)
    Returns (score, label).
    """
    score = 0.0

    if df is not None and not df.empty and len(df) >= 20:
        close = df["Close"].dropna()
        returns = close.pct_change().dropna()

        # Annualized volatility
        ann_vol = float(returns.std() * np.sqrt(252)) * 100
        if ann_vol < 8:
            score += 10
        elif ann_vol < 12:
            score += 20
        elif ann_vol < 18:
            score += 35
        elif ann_vol < 25:
            score += 50
        elif ann_vol < 35:
            score += 65
        else:
            score += 80

        # Max drawdown
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.cummax()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_dd = float(drawdown.min()) * 100
        if max_dd > -5:
            score += 5
        elif max_dd > -10:
            score += 10
        elif max_dd > -20:
            score += 18
        elif max_dd > -35:
            score += 25
        else:
            score += 35
    else:
        score += 30

    # Concentration
    if holdings:
        top10_weight = sum(h.get("weight", 0) for h in holdings[:10])
        if top10_weight < 20:
            score += 5
        elif top10_weight < 40:
            score += 10
        elif top10_weight < 60:
            score += 15
        else:
            score += 20
    else:
        score += 10

    # Beta adjustment
    if beta and beta > 0:
        score = score * (0.7 + beta * 0.3)

    score = max(0.0, min(100.0, score))

    if score < 20:
        label = "Conservative"
    elif score < 40:
        label = "Moderate-Conservative"
    elif score < 60:
        label = "Moderate"
    elif score < 80:
        label = "Aggressive"
    else:
        label = "Very Aggressive"

    return score, label


def compute_portfolio_risk(holdings_df: pd.DataFrame, histories: dict) -> float:
    """Compute portfolio-level risk score as weighted average of individual ETF-like risk scores."""
    if holdings_df is None or holdings_df.empty:
        return 50.0
    scores = []
    weights = []
    total_val = holdings_df["current_value"].sum() if "current_value" in holdings_df.columns else 1
    for _, row in holdings_df.iterrows():
        ticker = row["ticker"]
        df = histories.get(ticker)
        weight = row.get("current_value", 1) / total_val if total_val else 1
        risk_score, _ = compute_etf_risk_score(df, [], None)
        scores.append(risk_score)
        weights.append(weight)
    if not scores:
        return 50.0
    return float(np.average(scores, weights=weights))
