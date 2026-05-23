import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_client():
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None, "ANTHROPIC_API_KEY not found in .env file."
    try:
        import anthropic
        return anthropic.Anthropic(api_key=key), None
    except ImportError:
        return None, "anthropic package not installed."
    except Exception as e:
        return None, str(e)


def _call_claude(prompt: str, system: str = "", max_tokens: int = 1500) -> str:
    client, err = get_client()
    if client is None:
        return f"AI analysis unavailable: {err}"
    try:
        import anthropic
        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": "claude-opus-4-7",
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        resp = client.messages.create(**kwargs)
        return resp.content[0].text
    except Exception as e:
        return f"Error calling Claude API: {e}"


SYSTEM_DISCLAIMER = (
    "You are a financial research assistant providing educational analysis only. "
    "Do NOT give buy, sell, or hold recommendations. Do NOT say 'you should' or 'I recommend'. "
    "Use neutral, factual language. Frame everything as educational context. "
    "End every response with: '— For educational purposes only. Not financial advice.'"
)


def bull_bear_case(ticker: str, info: dict, tech_score: float, fund_score: float) -> str:
    name = info.get("shortName") or ticker
    sector = info.get("sector", "N/A")
    pe = info.get("trailingPE")
    market_cap = info.get("marketCap")
    rev_growth = info.get("revenueGrowth")
    net_margin = info.get("profitMargins")
    roe = info.get("returnOnEquity")
    de = info.get("debtToEquity")
    beta = info.get("beta")
    price = info.get("currentPrice") or info.get("regularMarketPrice")

    prompt = f"""
Provide an educational bull and bear case analysis for {name} ({ticker}), a {sector} company.

Key metrics:
- Price: ${price}
- Market Cap: ${market_cap:,} if {market_cap} else N/A
- P/E: {pe}
- Revenue Growth (YoY): {rev_growth}
- Net Margin: {net_margin}
- ROE: {roe}
- D/E: {de}
- Beta: {beta}
- Technical score: {tech_score:.0f}/100
- Fundamental score: {fund_score:.0f}/100

Structure your response as:
## Bull Case
- 3-4 factual positive factors with context

## Bear Case
- 3-4 factual risk factors with context

Keep it objective, educational, and concise. No investment recommendations.
"""
    return _call_claude(prompt, SYSTEM_DISCLAIMER, max_tokens=800)


def deep_analysis(ticker: str, info: dict, fundamentals: dict) -> str:
    name = info.get("shortName") or ticker
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    description = info.get("longBusinessSummary", "")[:500]

    prompt = f"""
Provide an in-depth educational analysis of {name} ({ticker}).

Company: {description}
Sector: {sector} | Industry: {industry}

Financial profile:
- Revenue: ${fundamentals.get('revenue')}
- Revenue Growth: {fundamentals.get('revenue_growth')}
- Gross Margin: {fundamentals.get('gross_margin')}
- Operating Margin: {fundamentals.get('op_margin')}
- Net Margin: {fundamentals.get('net_margin')}
- ROE: {fundamentals.get('roe')}
- ROA: {fundamentals.get('roa')}
- Debt/Equity: {fundamentals.get('debt_equity')}
- P/E: {fundamentals.get('pe')} | Forward P/E: {fundamentals.get('forward_pe')}
- P/B: {fundamentals.get('pb')} | P/S: {fundamentals.get('ps')}
- EV/EBITDA: {fundamentals.get('ev_ebitda')}

Cover:
1. Business model and competitive positioning
2. Financial health and trends
3. Key risks and opportunities
4. Industry context

Educational purposes only. No investment recommendations.
"""
    return _call_claude(prompt, SYSTEM_DISCLAIMER, max_tokens=1200)


def etf_analysis(ticker: str, etf_data: dict, risk_score: float, risk_label: str) -> str:
    name = etf_data.get("name", ticker)
    expense = etf_data.get("expense_ratio")
    aum = etf_data.get("aum")
    ytd = etf_data.get("ytd_return")
    three_yr = etf_data.get("three_year_return")
    five_yr = etf_data.get("five_year_return")
    category = etf_data.get("category", "N/A")
    top_holdings = etf_data.get("holdings", [])[:5]
    holdings_str = ", ".join([f"{h['symbol']} ({h['weight']:.1f}%)" for h in top_holdings if h.get('symbol')])

    prompt = f"""
Provide an educational overview of the ETF {name} ({ticker}).

Key facts:
- Category: {category}
- Expense Ratio: {expense}
- AUM: ${aum}
- YTD Return: {ytd}
- 3Y Avg Return: {three_yr}
- 5Y Avg Return: {five_yr}
- Risk Score: {risk_score:.0f}/100 ({risk_label})
- Top Holdings: {holdings_str}

Cover:
1. What this ETF tracks and its strategy
2. Cost structure and how it compares to peers
3. Risk profile and suitable use cases
4. Key considerations for research

Educational purposes only. No investment recommendations.
"""
    return _call_claude(prompt, SYSTEM_DISCLAIMER, max_tokens=900)


def macro_pulse(indicators: dict) -> str:
    prompt = f"""
Provide an educational macro-economic pulse-check based on current US indicators:

{indicators}

Cover:
1. Current economic cycle positioning
2. Inflation and monetary policy context
3. Labor market conditions
4. Key risks and tailwinds for markets
5. Historical context (what similar periods looked like)

Keep it factual and educational. Cite specific numbers. No investment recommendations.
"""
    return _call_claude(prompt, SYSTEM_DISCLAIMER, max_tokens=1000)


def portfolio_analysis(holdings_summary: str, total_value: float, total_return: float) -> str:
    prompt = f"""
Provide an educational analysis of this investment portfolio:

Total Value: ${total_value:,.2f}
Total Return: {total_return:.2f}%

Holdings:
{holdings_summary}

Cover:
1. Diversification assessment (sector, geography, asset class)
2. Concentration risks
3. Risk profile observations
4. What factors could impact this portfolio

Educational purposes only. No investment recommendations.
"""
    return _call_claude(prompt, SYSTEM_DISCLAIMER, max_tokens=900)
