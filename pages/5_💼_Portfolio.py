import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Portfolio", page_icon="💼", layout="wide")

st.markdown("""
<style>
    .main .block-container { font-size: 17px; }
    .disclosure { color: #888; font-size: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; margin-top: 20px; }
    .ai-output { background: rgba(255,255,255,0.03); border-left: 3px solid #5c9bd6; border-radius: 4px; padding: 16px; font-size: 15px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📈 Market Analyst")
    st.caption("Educational & research use only")
    st.divider()

from lib.portfolio import load_portfolio, add_holding, remove_holding, build_portfolio_df
from lib.market_data import get_quotes_bulk, get_history_bulk
from lib.charts import render_gauge
from lib.risk import compute_portfolio_risk, compute_etf_risk_score
from lib.claude_analyst import portfolio_analysis
from lib.config import DISCLOSURE

st.title("💼 Portfolio Tracker")
st.caption("Your holdings are saved locally in data/portfolio.json (gitignored)")

# Add/edit holding form
with st.expander("➕ Add or Update Holding", expanded=False):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        new_ticker = st.text_input("Ticker", placeholder="AAPL").upper().strip()
    with c2:
        new_shares = st.number_input("Shares", min_value=0.0001, value=1.0, step=0.01)
    with c3:
        new_cost = st.number_input("Cost Basis ($/share)", min_value=0.01, value=100.0, step=0.01)
    with c4:
        st.write("")
        st.write("")
        if st.button("Save", key="add_holding_btn"):
            if new_ticker:
                add_holding(new_ticker, new_shares, new_cost)
                st.success(f"Saved {new_ticker}")
                st.rerun()

# Load portfolio
holdings_raw = load_portfolio()

if not holdings_raw:
    st.info("No holdings yet. Add some using the form above.")
    st.markdown(f'<div class="disclosure">{DISCLOSURE}</div>', unsafe_allow_html=True)
    st.stop()

tickers = [h["ticker"] for h in holdings_raw]
with st.spinner("Loading market data…"):
    quotes = get_quotes_bulk(tickers)
    histories = get_history_bulk(tickers, period="1y", interval="1d")

portfolio_df = build_portfolio_df(quotes)

if portfolio_df.empty:
    st.warning("Could not load market data for portfolio holdings.")
    st.stop()

# Summary metrics
total_value = portfolio_df["current_value"].sum()
total_cost = portfolio_df["total_cost"].sum()
total_gain = portfolio_df["gain_loss"].sum()
total_gain_pct = (total_gain / total_cost * 100) if total_cost else 0
gain_color = "#26a69a" if total_gain >= 0 else "#ef5350"
sign = "+" if total_gain >= 0 else ""

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Value", f"${total_value:,.2f}")
col2.metric("Total Cost", f"${total_cost:,.2f}")
col3.metric("Total Gain/Loss", f"{sign}${abs(total_gain):,.2f}", f"{sign}{total_gain_pct:.2f}%", delta_color="normal")
col4.metric("# Positions", str(len(portfolio_df)))

st.divider()

# Holdings table with remove buttons
st.subheader("Holdings")
for _, row in portfolio_df.iterrows():
    c1, c2, c3, c4, c5, c6, c_del = st.columns([1, 1.5, 1, 1, 1, 1, 0.5])
    g_color = "#26a69a" if row["gain_loss"] >= 0 else "#ef5350"
    g_sign = "+" if row["gain_loss"] >= 0 else ""
    with c1:
        st.markdown(f"**{row['ticker']}**")
        st.caption(row["name"][:20])
    with c2:
        st.markdown(f"{row['shares']:.4f} shares")
        st.caption(f"@ ${row['cost_basis']:.2f}")
    with c3:
        st.markdown(f"${row['price']:.2f}")
        st.caption("Current price")
    with c4:
        st.markdown(f"${row['current_value']:,.2f}")
        st.caption("Value")
    with c5:
        st.markdown(f"<span style='color:{g_color}'>{g_sign}${abs(row['gain_loss']):,.2f}</span>", unsafe_allow_html=True)
        st.caption(f"{g_sign}{row['gain_loss_pct']:.2f}%")
    with c6:
        st.markdown(row.get("sector") or "—")
        st.caption("Sector")
    with c_del:
        st.write("")
        if st.button("✕", key=f"del_{row['ticker']}", help=f"Remove {row['ticker']}"):
            remove_holding(row["ticker"])
            st.rerun()

st.divider()

# Charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Allocation")
    fig_alloc = go.Figure(go.Pie(
        labels=portfolio_df["ticker"].tolist(),
        values=portfolio_df["current_value"].tolist(),
        hole=0.45,
        marker=dict(colors=["#5c9bd6", "#26a69a", "#ffa726", "#ab47bc", "#ef5350",
                             "#42a5f5", "#66bb6a", "#ffca28", "#ec407a", "#26c6da"]),
        textinfo="label+percent",
        textfont=dict(size=13),
    ))
    fig_alloc.update_layout(
        template="plotly_dark", height=350,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_alloc, use_container_width=True)

with chart_col2:
    st.subheader("Sector Breakdown")
    sector_groups = portfolio_df.groupby("sector")["current_value"].sum()
    sector_groups = sector_groups[sector_groups > 0]
    if not sector_groups.empty:
        fig_sector = go.Figure(go.Pie(
            labels=sector_groups.index.tolist(),
            values=sector_groups.values.tolist(),
            hole=0.45,
            marker=dict(colors=["#5c9bd6", "#26a69a", "#ffa726", "#ab47bc", "#ef5350",
                                 "#42a5f5", "#66bb6a", "#ffca28", "#ec407a", "#26c6da",
                                 "#9ccc65", "#26a69a"]),
            textinfo="label+percent",
            textfont=dict(size=13),
        ))
        fig_sector.update_layout(
            template="plotly_dark", height=350,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_sector, use_container_width=True)

st.divider()

# Portfolio risk
st.subheader("Portfolio Risk")
port_risk = compute_portfolio_risk(portfolio_df, histories)
risk_label = (
    "Conservative" if port_risk < 20
    else "Moderate-Conservative" if port_risk < 40
    else "Moderate" if port_risk < 60
    else "Aggressive" if port_risk < 80
    else "Very Aggressive"
)
fig_risk = render_gauge(port_risk, f"Portfolio Risk: {risk_label}",
                        "Volatility-weighted across holdings", height=240)
col_risk, col_info = st.columns([1, 1])
with col_risk:
    st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar": False})
with col_info:
    st.markdown(f"""
    **Risk Score: {port_risk:.0f}/100 — {risk_label}**

    Risk is estimated from the volatility, drawdown, and concentration of your holdings
    over the past year. Higher scores indicate historically higher price swings.
    """)

st.divider()

# AI analysis
st.subheader("AI Portfolio Analysis")
if st.button("Generate Portfolio Analysis", key="port_ai_btn"):
    holdings_str = "\n".join([
        f"- {r['ticker']} ({r['name'][:25]}): {r['shares']:.2f} shares at ${r['price']:.2f} = ${r['current_value']:,.2f} ({r['gain_loss_pct']:+.1f}% P&L)"
        for _, r in portfolio_df.iterrows()
    ])
    with st.spinner("Analyzing with Claude…"):
        result = portfolio_analysis(holdings_str, total_value, total_gain_pct)
    st.markdown(f'<div class="ai-output">{result.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

st.markdown(f'<div class="disclosure">{DISCLOSURE}</div>', unsafe_allow_html=True)
