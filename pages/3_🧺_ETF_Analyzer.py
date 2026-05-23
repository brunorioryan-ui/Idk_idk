import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="ETF Analyzer", page_icon="🧺", layout="wide")

st.markdown("""
<style>
    .main .block-container { font-size: 17px; }
    .disclosure { color: #888; font-size: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; margin-top: 20px; }
    .ai-output { background: rgba(255,255,255,0.03); border-left: 3px solid #5c9bd6; border-radius: 4px; padding: 16px; font-size: 15px; line-height: 1.6; }
    .holding-row { display: flex; align-items: center; gap: 10px; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📈 Market Analyst")
    st.caption("Educational & research use only")
    st.divider()

from lib.market_data import get_quote, get_history, get_etf_details, PERIOD_MAP, get_prev_close, is_etf
from lib.charts import render_price_chart, render_gauge
from lib.logos import logo_img_tag
from lib.risk import compute_etf_risk_score
from lib.etf_peers import find_peer_group, get_cheaper_alternatives
from lib.claude_analyst import etf_analysis
from lib.config import DISCLOSURE

st.title("🧺 ETF Analyzer")

col_in, col_per = st.columns([2, 3])
with col_in:
    ticker = st.text_input("ETF ticker", value="SPY", placeholder="e.g. SPY, QQQ, VTI").upper().strip()
with col_per:
    period = st.segmented_control("Period", list(PERIOD_MAP.keys()), default="1Y", key="etf_period")

if not period:
    period = "1Y"
yf_period, yf_interval = PERIOD_MAP[period]

if not ticker:
    st.info("Enter an ETF ticker to get started.")
    st.stop()

with st.spinner(f"Loading {ticker}..."):
    quote = get_quote(ticker)
    df = get_history(ticker, period=yf_period, interval=yf_interval)
    etf_data = get_etf_details(ticker)

price = quote.get("price")
if price is None:
    st.error(f"Could not load data for **{ticker}**.")
    st.stop()

name = etf_data.get("name") or quote.get("name", ticker)
chg_pct = quote.get("change_pct", 0) or 0
chg = quote.get("change", 0) or 0
sign = "+" if chg_pct >= 0 else ""

expense_ratio = etf_data.get("expense_ratio")
aum = etf_data.get("aum")
category = etf_data.get("category") or "ETF"
ytd = etf_data.get("ytd_return")
three_yr = etf_data.get("three_year_return")
five_yr = etf_data.get("five_year_return")
beta_val = etf_data.get("beta")
holdings = etf_data.get("holdings", [])
sector_weights = etf_data.get("sector_weights", {})

logo = logo_img_tag(ticker, size=56)

def _pct_fmt(v):
    if v is None:
        return "—"
    return f"{v*100:.2f}%"

def _big(v):
    if not v:
        return "—"
    if v >= 1e12:
        return f"${v/1e12:.2f}T"
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    return f"${v/1e6:.1f}M"

header_col, metric_col = st.columns([1, 2])
with header_col:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px;">
        {logo}
        <div>
            <div style="font-size:20px;font-weight:700;">{name}</div>
            <div style="color:#aaa;font-size:14px;">{ticker} · {category}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with metric_col:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Price", f"${price:,.2f}", f"{sign}{chg:.2f} ({sign}{chg_pct:.2f}%)")
    m2.metric("Expense Ratio", _pct_fmt(expense_ratio))
    m3.metric("AUM", _big(aum))
    m4.metric("Beta (3Y)", f"{beta_val:.2f}" if beta_val else "—")

st.divider()

# Chart
view = st.segmented_control("Chart view", ["Performance", "Price", "Candlestick", "Area"], default="Performance", key="etf_chart_view")
baseline_price = None
if period == "1D":
    baseline_price = get_prev_close(ticker)
show_vol = st.checkbox("Volume overlay", value=True, key="etf_vol")

if not df.empty:
    fig = render_price_chart(df, ticker, view=view or "Performance",
                             show_volume=show_vol, baseline_price=baseline_price, height=440)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Returns and risk
col_ret, col_risk = st.columns([1, 1])

with col_ret:
    st.subheader("Returns")
    returns_data = [
        ("YTD", _pct_fmt(ytd)),
        ("3Y Avg Ann.", _pct_fmt(three_yr)),
        ("5Y Avg Ann.", _pct_fmt(five_yr)),
        ("Expense Ratio", _pct_fmt(expense_ratio)),
    ]
    for label, val in returns_data:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);font-size:15px;">
            <span style="color:#aaa;">{label}</span>
            <span style="font-weight:600;">{val}</span>
        </div>
        """, unsafe_allow_html=True)

with col_risk:
    risk_score, risk_label = compute_etf_risk_score(df, holdings, beta_val)
    fig_risk = render_gauge(risk_score, f"Risk: {risk_label}",
                            "Volatility · Drawdown · Concentration", height=230)
    st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar": False})

st.divider()

# Sector breakdown
col_sector, col_holdings = st.columns([1, 1])

with col_sector:
    st.subheader("Sector Breakdown")
    if sector_weights:
        sorted_sw = sorted(sector_weights.items(), key=lambda x: x[1], reverse=True)
        fig_sw = go.Figure(go.Bar(
            x=[v for _, v in sorted_sw],
            y=[s for s, _ in sorted_sw],
            orientation="h",
            marker_color="#5c9bd6",
            hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
        ))
        fig_sw.update_layout(
            template="plotly_dark",
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)"),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig_sw, use_container_width=True)
    else:
        st.info("Sector breakdown not available for this ETF.")

with col_holdings:
    st.subheader("Top Holdings")
    if holdings:
        h_col1, h_col2 = st.columns(2)
        for i, h in enumerate(holdings[:20]):
            sym = h.get("symbol", "")
            h_name = h.get("name", sym)[:20]
            weight = h.get("weight", 0)
            logo_h = logo_img_tag(sym, size=24)
            target_col = h_col1 if i % 2 == 0 else h_col2
            with target_col:
                st.markdown(f"""
                <div class="holding-row">
                    {logo_h}
                    <div style="flex:1;min-width:0;">
                        <span style="font-weight:600;font-size:13px;">{sym}</span>
                        <span style="color:#aaa;font-size:11px;"> {h_name}</span>
                    </div>
                    <div style="font-size:13px;font-weight:600;color:#5c9bd6;">{weight:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Holdings data not available for this ETF.")

st.divider()

# Peer comparison
st.subheader("Peer Comparison")
peer_group, peers = find_peer_group(ticker)
if peers:
    st.caption(f"Peer group: **{peer_group}**")
    from lib.market_data import get_etf_details as _ged
    peer_rows = []
    for p in peers[:6]:
        pd_data = _ged(p)
        pq = get_quote(p)
        peer_rows.append({
            "Ticker": p,
            "Name": (pd_data.get("name") or p)[:30],
            "Expense Ratio": pd_data.get("expense_ratio"),
            "AUM": pd_data.get("aum"),
            "YTD Return": pd_data.get("ytd_return"),
            "3Y Avg": pd_data.get("three_year_return"),
        })

    own_row = {
        "Ticker": f"**{ticker}** ★",
        "Name": name[:30],
        "Expense Ratio": expense_ratio,
        "AUM": aum,
        "YTD Return": ytd,
        "3Y Avg": three_yr,
    }
    all_rows = [own_row] + peer_rows

    import pandas as pd
    df_peers = pd.DataFrame(all_rows)
    df_display = df_peers.copy()
    df_display["Expense Ratio"] = df_display["Expense Ratio"].apply(lambda v: f"{v*100:.2f}%" if v else "—")
    df_display["AUM"] = df_display["AUM"].apply(_big)
    df_display["YTD Return"] = df_display["YTD Return"].apply(lambda v: f"{v*100:.2f}%" if v else "—")
    df_display["3Y Avg"] = df_display["3Y Avg"].apply(lambda v: f"{v*100:.2f}%" if v else "—")
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Cheaper alternatives
    cheaper = get_cheaper_alternatives(ticker, expense_ratio, peer_rows)
    if cheaper:
        best = cheaper[0]
        savings_bps = best.get("savings_bps", 0)
        savings_100k = best.get("savings_100k", 0)
        best_er = best.get("Expense Ratio")
        er_str = f"{best_er*100:.2f}%" if best_er else "lower"
        st.info(
            f"💡 **{best['Ticker']}** has a {er_str} expense ratio — "
            f"**{savings_bps:.1f} bps cheaper**, saving ~${savings_100k:,.0f}/yr on a $100K position."
        )
else:
    st.info("No peer comparison data available for this ETF.")

st.divider()

# AI analysis
st.subheader("AI Analysis")
st.caption("Claude-generated educational overview — not investment advice")

if st.button("Generate ETF Analysis", key="etf_ai_btn"):
    with st.spinner("Analyzing with Claude…"):
        result = etf_analysis(ticker, etf_data, risk_score, risk_label)
    st.markdown(f'<div class="ai-output">{result.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

st.markdown(f'<div class="disclosure">{DISCLOSURE}</div>', unsafe_allow_html=True)
