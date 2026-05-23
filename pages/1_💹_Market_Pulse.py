import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Market Pulse", page_icon="💹", layout="wide")

st.markdown("""
<style>
    .main .block-container { font-size: 17px; }
    .index-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 10px 14px; }
    .mover-row { display: flex; align-items: center; gap: 8px; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
    .news-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; }
    .disclosure { color: #888; font-size: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📈 Market Analyst")
    st.caption("Educational & research use only")
    st.divider()

from lib.market_data import (
    get_quotes_bulk, get_history, get_history_bulk, get_prev_close,
    INDEX_TICKERS, SECTOR_ETFS, PERIOD_MAP, get_top_movers
)
from lib.charts import render_price_chart, render_sparkline
from lib.logos import logo_img_tag
from lib.news import market_news
from lib.config import DISCLOSURE

st.title("💹 Market Pulse")

# Period selector
period_options = list(PERIOD_MAP.keys())
period = st.segmented_control("Period", period_options, default="1M", key="pulse_period")
if not period:
    period = "1M"
yf_period, yf_interval = PERIOD_MAP[period]

# Index cards with sparklines
st.subheader("Market Overview")
index_tickers = list(INDEX_TICKERS.keys())
quotes = get_quotes_bulk(index_tickers)
histories = get_history_bulk(index_tickers, period=yf_period, interval=yf_interval)

cols = st.columns(5)
for i, ticker in enumerate(index_tickers):
    q = quotes.get(ticker, {})
    df = histories.get(ticker, pd.DataFrame())
    price = q.get("price")
    chg_pct = q.get("change_pct", 0) or 0
    name = INDEX_TICKERS[ticker]
    color = "#26a69a" if chg_pct >= 0 else "#ef5350"
    sign = "+" if chg_pct >= 0 else ""

    with cols[i % 5]:
        price_str = f"{price:,.2f}" if price else "—"
        st.markdown(f"""
        <div class="index-card">
            <div style="color:#aaa;font-size:12px;">{name}</div>
            <div style="font-size:17px;font-weight:700;">{price_str}</div>
            <div style="color:{color};font-size:13px;">{sign}{chg_pct:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

        if not df.empty:
            baseline = None
            if period == "1D":
                baseline = get_prev_close(ticker)
            close_vals = df["Close"].dropna().tolist()
            base = baseline if baseline is not None else (close_vals[0] if close_vals else None)
            if base and close_vals:
                spark = render_sparkline(df.index.tolist(), close_vals, baseline=base, height=55)
                st.plotly_chart(spark, use_container_width=True, config={"displayModeBar": False})

st.divider()

# S&P 500 big chart
st.subheader("S&P 500 (^GSPC)")
view = st.segmented_control("Chart view", ["Performance", "Price", "Candlestick", "Area"], default="Performance", key="gspc_view")
df_sp = histories.get("^GSPC", pd.DataFrame())
if df_sp.empty:
    df_sp = get_history("^GSPC", period=yf_period, interval=yf_interval)

baseline_price = None
if period == "1D":
    baseline_price = get_prev_close("^GSPC")

show_vol = st.checkbox("Show volume", value=True, key="gspc_vol")
if not df_sp.empty:
    fig = render_price_chart(df_sp, "^GSPC", view=view or "Performance",
                             show_volume=show_vol, baseline_price=baseline_price, height=480)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Sector heatmap
st.subheader("Sector Performance")
sector_tickers = list(SECTOR_ETFS.keys())
sector_quotes = get_quotes_bulk(sector_tickers)

sector_data = []
for ticker, name in SECTOR_ETFS.items():
    q = sector_quotes.get(ticker, {})
    chg = q.get("change_pct", 0) or 0
    sector_data.append({"name": name, "ticker": ticker, "change": chg})

sector_data.sort(key=lambda x: x["change"], reverse=True)
colors = ["#26a69a" if d["change"] >= 0 else "#ef5350" for d in sector_data]
text_labels = [f"{d['ticker']}<br>{d['change']:+.2f}%" for d in sector_data]

fig_sector = go.Figure(go.Bar(
    x=[d["name"] for d in sector_data],
    y=[d["change"] for d in sector_data],
    marker_color=colors,
    text=text_labels,
    textposition="outside",
    hovertemplate="%{x}: %{y:.2f}%<extra></extra>",
))
fig_sector.add_hline(y=0, line_color="rgba(255,255,255,0.3)")
fig_sector.update_layout(
    template="plotly_dark",
    height=350,
    margin=dict(l=10, r=10, t=20, b=60),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(tickangle=-30),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)"),
    showlegend=False,
)
st.plotly_chart(fig_sector, use_container_width=True)

st.divider()

# Top movers
st.subheader("Top Movers")
movers = get_top_movers()
col_g, col_l, col_a = st.columns(3)

def _fmt_cap(val):
    if not val:
        return "—"
    if val >= 1e12:
        return f"${val/1e12:.2f}T"
    if val >= 1e9:
        return f"${val/1e9:.2f}B"
    return f"${val/1e6:.1f}M"

def render_mover_list(col, title, movers_list, color_fn):
    with col:
        st.markdown(f"**{title}**")
        for q in movers_list:
            ticker = q.get("ticker", "")
            name = q.get("name", ticker)[:22]
            price = q.get("price")
            chg_pct = q.get("change_pct", 0) or 0
            color = color_fn(chg_pct)
            sign = "+" if chg_pct >= 0 else ""
            logo = logo_img_tag(ticker, size=28)
            price_str = f"${price:,.2f}" if price else "—"
            st.markdown(f"""
            <div class="mover-row">
                {logo}
                <div style="flex:1;min-width:0;">
                    <div style="font-weight:600;font-size:14px;">{ticker}</div>
                    <div style="color:#aaa;font-size:12px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">{name}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:14px;">{price_str}</div>
                    <div style="color:{color};font-size:13px;">{sign}{chg_pct:.2f}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

render_mover_list(col_g, "🟢 Top Gainers", movers["gainers"], lambda c: "#26a69a")
render_mover_list(col_l, "🔴 Top Losers", movers["losers"], lambda c: "#ef5350")

with col_a:
    st.markdown("**🔥 Most Active**")
    for q in movers["active"]:
        ticker = q.get("ticker", "")
        name = q.get("name", ticker)[:22]
        price = q.get("price")
        vol = q.get("volume") or 0
        chg_pct = q.get("change_pct", 0) or 0
        color = "#26a69a" if chg_pct >= 0 else "#ef5350"
        sign = "+" if chg_pct >= 0 else ""
        logo = logo_img_tag(ticker, size=28)
        vol_str = f"{vol/1e6:.1f}M" if vol >= 1e6 else f"{vol:,}"
        price_str = f"${price:,.2f}" if price else "—"
        st.markdown(f"""
        <div class="mover-row">
            {logo}
            <div style="flex:1;min-width:0;">
                <div style="font-weight:600;font-size:14px;">{ticker}</div>
                <div style="color:#aaa;font-size:12px;">{name}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:14px;">{price_str}</div>
                <div style="color:{color};font-size:13px;">Vol: {vol_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Market headlines
st.subheader("Market Headlines")
headlines = market_news(limit=6)
if headlines:
    for item in headlines[:3]:
        title = item.get("title", "")
        publisher = item.get("publisher", "")
        time_ago = item.get("time_ago", "")
        summary = item.get("summary", "")
        link = item.get("link", "#")
        summary_short = summary[:160] + "…" if len(summary) > 160 else summary
        st.markdown(f"""
        <div class="news-card">
            <a href="{link}" target="_blank" style="color:#5c9bd6;text-decoration:none;font-weight:600;font-size:15px;">{title}</a>
            <div style="color:#888;font-size:12px;margin-top:4px;">{publisher} · {time_ago}</div>
            <div style="color:#ccc;font-size:13px;margin-top:6px;">{summary_short}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No headlines available at this time.")

st.markdown(f'<div class="disclosure">{DISCLOSURE}</div>', unsafe_allow_html=True)
