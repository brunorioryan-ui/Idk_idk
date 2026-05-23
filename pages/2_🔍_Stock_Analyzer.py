import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Stock Analyzer", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .main .block-container { font-size: 17px; }
    .stat-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; }
    .stat-cell { background: rgba(255,255,255,0.04); border-radius: 8px; padding: 10px 14px; }
    .stat-label { color: #aaa; font-size: 12px; }
    .stat-value { font-size: 16px; font-weight: 600; margin-top: 2px; }
    .chip { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 13px; margin: 3px; }
    .driver-item { padding: 4px 0; font-size: 14px; color: #ddd; }
    .disclosure { color: #888; font-size: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; margin-top: 20px; }
    .ai-output { background: rgba(255,255,255,0.03); border-left: 3px solid #5c9bd6; border-radius: 4px; padding: 16px; font-size: 15px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📈 Market Analyst")
    st.caption("Educational & research use only")
    st.divider()

from lib.market_data import get_quote, get_history, get_stock_fundamentals, PERIOD_MAP, is_etf
from lib.charts import render_price_chart, render_gauge
from lib.logos import logo_img_tag
from lib.signals import compute_technical_score, compute_fundamental_score, get_at_a_glance
from lib.news import ticker_news
from lib.claude_analyst import bull_bear_case, deep_analysis
from lib.config import DISCLOSURE

st.title("🔍 Stock Analyzer")

col_input, col_period = st.columns([2, 3])
with col_input:
    ticker = st.text_input("Ticker symbol", value="AAPL", placeholder="e.g. AAPL, MSFT, TSLA").upper().strip()
with col_period:
    period = st.segmented_control("Period", list(PERIOD_MAP.keys()), default="1Y", key="stock_period")

if not period:
    period = "1Y"
yf_period, yf_interval = PERIOD_MAP[period]

if not ticker:
    st.info("Enter a ticker symbol to get started.")
    st.stop()

if is_etf(ticker):
    st.info(f"**{ticker}** appears to be an ETF. For ETF analysis, use the **ETF Analyzer** page.")

with st.spinner(f"Loading {ticker}..."):
    quote = get_quote(ticker)
    df = get_history(ticker, period=yf_period, interval=yf_interval)
    fundamentals = get_stock_fundamentals(ticker)
    info = quote.get("info", {})

price = quote.get("price")
if price is None:
    st.error(f"Could not load data for **{ticker}**. Please check the ticker symbol.")
    st.stop()

chg = quote.get("change", 0) or 0
chg_pct = quote.get("change_pct", 0) or 0
name = quote.get("name", ticker)
sector = quote.get("sector") or "N/A"
industry = quote.get("industry") or "N/A"
market_cap = quote.get("market_cap")
pe = quote.get("pe")
beta = quote.get("beta")

# Header
logo = logo_img_tag(ticker, size=64)
chg_color = "#26a69a" if chg_pct >= 0 else "#ef5350"
sign = "+" if chg_pct >= 0 else ""

def _fmt_cap(val):
    if not val:
        return "—"
    if val >= 1e12:
        return f"${val/1e12:.2f}T"
    if val >= 1e9:
        return f"${val/1e9:.2f}B"
    return f"${val/1e6:.1f}M"

header_col, metrics_col = st.columns([1, 2])
with header_col:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:8px;">
        {logo}
        <div>
            <div style="font-size:22px;font-weight:700;">{name}</div>
            <div style="color:#aaa;font-size:14px;">{ticker} · {sector} · {industry}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with metrics_col:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Price", f"${price:,.2f}", f"{sign}{chg:.2f} ({sign}{chg_pct:.2f}%)", delta_color="normal")
    m2.metric("Market Cap", _fmt_cap(market_cap))
    m3.metric("P/E (TTM)", f"{pe:.1f}" if pe else "—")
    m4.metric("Beta", f"{beta:.2f}" if beta else "—")

st.divider()

# Chart
view = st.segmented_control("Chart view", ["Performance", "Price", "Candlestick", "Area"], default="Performance", key="stock_chart_view")
show_vol = st.checkbox("Volume overlay", value=True, key="stock_vol")

from lib.market_data import get_prev_close
baseline_price = None
if period == "1D":
    baseline_price = get_prev_close(ticker)

if not df.empty:
    fig = render_price_chart(df, ticker, view=view or "Performance",
                             show_volume=show_vol, baseline_price=baseline_price, height=460)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No price history available for the selected period.")

st.divider()

# Snapshot section
st.subheader("Snapshot")
st.caption("Factual metrics — no buy/sell signals. Scores reflect technical and fundamental strength relative to historical ranges.")

tech_score, tech_drivers = compute_technical_score(df, info)
fund_score, fund_drivers = compute_fundamental_score(info)
chips = get_at_a_glance(info, df)

snap_left, snap_mid, snap_right = st.columns([1.2, 1, 1])

with snap_left:
    st.markdown("**At a Glance**")
    chip_html = ""
    for chip in chips:
        chip_html += f'<div class="chip" style="background:rgba(255,255,255,0.06);border:1px solid {chip["color"]}40;color:{chip["color"]};margin-bottom:5px;"><span style="color:#aaa;font-size:11px;">{chip["label"]}: </span>{chip["value"]}</div><br>'
    st.markdown(chip_html, unsafe_allow_html=True)

with snap_mid:
    fig_tech = render_gauge(tech_score, "Technical strength",
                            "Trend, momentum, position vs averages", height=230)
    st.plotly_chart(fig_tech, use_container_width=True, config={"displayModeBar": False})
    st.markdown("**Observations**")
    for d in tech_drivers[:5]:
        st.markdown(f'<div class="driver-item">• {d}</div>', unsafe_allow_html=True)

with snap_right:
    fig_fund = render_gauge(fund_score, "Fundamental quality",
                            "Margins, returns, leverage, growth", height=230)
    st.plotly_chart(fig_fund, use_container_width=True, config={"displayModeBar": False})
    st.markdown("**Observations**")
    for d in fund_drivers[:5]:
        st.markdown(f'<div class="driver-item">• {d}</div>', unsafe_allow_html=True)

st.divider()

# Key statistics
st.subheader("Key Statistics")

def _pct(v):
    return f"{v*100:.2f}%" if v is not None else "—"

def _val(v, fmt=".2f"):
    return f"{v:{fmt}}" if v is not None else "—"

def _big(v):
    if v is None:
        return "—"
    if v >= 1e12:
        return f"${v/1e12:.2f}T"
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.1f}M"
    return f"${v:,.0f}"

stats_groups = {
    "Valuation": [
        ("Trailing P/E", _val(fundamentals.get("pe"), ".1f")),
        ("Forward P/E", _val(fundamentals.get("forward_pe"), ".1f")),
        ("P/Book", _val(fundamentals.get("pb"), ".2f")),
        ("P/Sales", _val(fundamentals.get("ps"), ".2f")),
        ("EV/EBITDA", _val(fundamentals.get("ev_ebitda"), ".1f")),
        ("Market Cap", _big(fundamentals.get("market_cap"))),
    ],
    "Profitability": [
        ("Gross Margin", _pct(fundamentals.get("gross_margin"))),
        ("Op. Margin", _pct(fundamentals.get("op_margin"))),
        ("Net Margin", _pct(fundamentals.get("net_margin"))),
        ("ROE", _pct(fundamentals.get("roe"))),
        ("ROA", _pct(fundamentals.get("roa"))),
        ("Rev Growth (YoY)", _pct(fundamentals.get("revenue_growth"))),
    ],
    "Balance Sheet": [
        ("Total Revenue", _big(fundamentals.get("revenue"))),
        ("Debt/Equity", _val(fundamentals.get("debt_equity"), ".1f")),
        ("Current Ratio", _val(fundamentals.get("current_ratio"), ".2f")),
        ("Quick Ratio", _val(fundamentals.get("quick_ratio"), ".2f")),
        ("Dividend Yield", _pct(fundamentals.get("dividend_yield"))),
        ("Payout Ratio", _pct(fundamentals.get("payout_ratio"))),
    ],
    "Trading": [
        ("52W High", f"${fundamentals.get('52w_high'):.2f}" if fundamentals.get("52w_high") else "—"),
        ("52W Low", f"${fundamentals.get('52w_low'):.2f}" if fundamentals.get("52w_low") else "—"),
        ("50-Day MA", f"${fundamentals.get('50dma'):.2f}" if fundamentals.get("50dma") else "—"),
        ("200-Day MA", f"${fundamentals.get('200dma'):.2f}" if fundamentals.get("200dma") else "—"),
        ("Beta", _val(fundamentals.get("beta"), ".2f")),
        ("Short Ratio", _val(fundamentals.get("short_ratio"), ".1f")),
    ],
    "Income": [
        ("EPS (TTM)", f"${fundamentals.get('eps'):.2f}" if fundamentals.get("eps") else "—"),
        ("Forward EPS", f"${fundamentals.get('forward_eps'):.2f}" if fundamentals.get("forward_eps") else "—"),
        ("Shares Out.", _big(fundamentals.get("shares_outstanding"))),
        ("Float", _big(fundamentals.get("float_shares"))),
        ("Employees", f"{fundamentals.get('employees'):,}" if fundamentals.get("employees") else "—"),
        ("Enterprise Val.", _big(fundamentals.get("enterprise_value"))),
    ],
    "Analyst": [
        ("# Analysts", str(fundamentals.get("analyst_count") or "—")),
        ("Mean Target", f"${fundamentals.get('target_mean'):.2f}" if fundamentals.get("target_mean") else "—"),
        ("High Target", f"${fundamentals.get('target_high'):.2f}" if fundamentals.get("target_high") else "—"),
        ("Low Target", f"${fundamentals.get('target_low'):.2f}" if fundamentals.get("target_low") else "—"),
        ("Consensus", str(fundamentals.get("recommendation") or "—").title()),
        ("Industry", industry[:28]),
    ],
}

group_names = list(stats_groups.keys())
for row_start in range(0, len(group_names), 3):
    row_groups = group_names[row_start:row_start + 3]
    cols = st.columns(len(row_groups))
    for col, group_name in zip(cols, row_groups):
        with col:
            st.markdown(f"**{group_name}**")
            for label, value in stats_groups[group_name]:
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:13px;">
                    <span style="color:#aaa;">{label}</span>
                    <span style="font-weight:500;">{value}</span>
                </div>
                """, unsafe_allow_html=True)

st.divider()

# Business summary
desc = fundamentals.get("description") or info.get("longBusinessSummary", "")
if desc:
    with st.expander("Business Summary"):
        st.write(desc)

st.divider()

# AI analysis tabs
st.subheader("AI Analysis")
st.caption("Powered by Claude — educational context only, not investment advice")

tab_bull, tab_deep, tab_news = st.tabs(["🐂 Bull / Bear Case", "🔬 Deep Analysis", "📰 Headlines"])

with tab_bull:
    if st.button("Generate Bull/Bear Analysis", key="bull_bear_btn"):
        with st.spinner("Analyzing with Claude…"):
            result = bull_bear_case(ticker, info, tech_score, fund_score)
        st.markdown(f'<div class="ai-output">{result.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

with tab_deep:
    if st.button("Generate Deep Analysis", key="deep_btn"):
        with st.spinner("Analyzing with Claude…"):
            result = deep_analysis(ticker, info, fundamentals)
        st.markdown(f'<div class="ai-output">{result.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

with tab_news:
    news_items = ticker_news(ticker, limit=10)
    if news_items:
        for item in news_items:
            title = item.get("title", "")
            publisher = item.get("publisher", "")
            time_ago = item.get("time_ago", "")
            summary = item.get("summary", "")
            link = item.get("link", "#")
            s = summary[:180] + "…" if len(summary) > 180 else summary
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:12px 16px;margin-bottom:8px;">
                <a href="{link}" target="_blank" style="color:#5c9bd6;text-decoration:none;font-weight:600;font-size:14px;">{title}</a>
                <div style="color:#888;font-size:12px;margin-top:4px;">{publisher} · {time_ago}</div>
                {"<div style='color:#ccc;font-size:13px;margin-top:6px;'>"+s+"</div>" if s else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent news found for this ticker.")

st.markdown(f'<div class="disclosure">{DISCLOSURE}</div>', unsafe_allow_html=True)
