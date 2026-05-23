import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Stock Market Analyst",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main .block-container { font-size: 17px; }
    .metric-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
    }
    .metric-card .label { color: #aaa; font-size: 13px; margin-bottom: 4px; }
    .metric-card .value { font-size: 22px; font-weight: 700; }
    .index-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 10px 14px;
    }
    .chip {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 13px;
        margin: 2px;
        background: rgba(255,255,255,0.07);
    }
    .news-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .mover-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .disclosure {
        color: #888;
        font-size: 12px;
        border-top: 1px solid rgba(255,255,255,0.1);
        padding-top: 12px;
        margin-top: 20px;
    }
    div[data-testid="stSidebar"] .stMarkdown h2 {
        font-size: 18px;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar branding
with st.sidebar:
    st.markdown("## 📈 Market Analyst")
    st.caption("Educational & research use only")
    st.divider()

# Main landing page
from lib.market_data import get_quotes_bulk, get_history, INDEX_TICKERS, PERIOD_MAP
from lib.charts import render_price_chart, render_sparkline
from lib.config import DISCLOSURE
from lib.logos import logo_img_tag

st.title("📈 Stock Market Analyst")
st.caption("Personal research dashboard — educational use only")

# Quick snapshot: key market indices
st.subheader("Market Snapshot")

key_tickers = ["^GSPC", "^NDX", "^DJI", "^RUT", "^VIX", "^TNX", "GC=F", "CL=F", "BTC-USD", "DX-Y.NYB"]
quotes = get_quotes_bulk(key_tickers)

cols = st.columns(5)
for i, ticker in enumerate(key_tickers):
    q = quotes.get(ticker, {})
    price = q.get("price")
    chg_pct = q.get("change_pct", 0) or 0
    name = INDEX_TICKERS.get(ticker, ticker)
    color = "#26a69a" if chg_pct >= 0 else "#ef5350"
    sign = "+" if chg_pct >= 0 else ""

    with cols[i % 5]:
        price_str = f"{price:,.2f}" if price else "—"
        if ticker in ("^TNX", "^VIX", "DX-Y.NYB"):
            price_str = f"{price:.2f}" if price else "—"
        st.markdown(f"""
        <div class="index-card">
            <div style="color:#aaa;font-size:12px;">{name}</div>
            <div style="font-size:18px;font-weight:700;">{price_str}</div>
            <div style="color:{color};font-size:13px;">{sign}{chg_pct:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# S&P 500 chart
st.subheader("S&P 500 — ^GSPC")
df_sp = get_history("^GSPC", period="1y", interval="1d")
if not df_sp.empty:
    view = st.segmented_control("View", ["Performance", "Price", "Area"], default="Performance", key="landing_view")
    fig = render_price_chart(df_sp, "^GSPC", view=view or "Performance", show_volume=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Navigate to pages
st.subheader("Explore the Dashboard")
c1, c2, c3 = st.columns(3)
with c1:
    st.page_link("pages/1_💹_Market_Pulse.py", label="💹 Market Pulse", icon="💹")
    st.caption("Indices, sectors, gainers & losers")
    st.page_link("pages/2_🔍_Stock_Analyzer.py", label="🔍 Stock Analyzer", icon="🔍")
    st.caption("Deep dive on any stock")
with c2:
    st.page_link("pages/3_🧺_ETF_Analyzer.py", label="🧺 ETF Analyzer", icon="🧺")
    st.caption("ETF risk, holdings & peers")
    st.page_link("pages/4_🌍_Macro.py", label="🌍 Macro", icon="🌍")
    st.caption("FRED economic indicators")
with c3:
    st.page_link("pages/5_💼_Portfolio.py", label="💼 Portfolio", icon="💼")
    st.caption("Track your holdings")
    st.page_link("pages/6_📰_News.py", label="📰 News", icon="📰")
    st.caption("Market & company headlines")

st.markdown(f'<div class="disclosure">{DISCLOSURE}</div>', unsafe_allow_html=True)
