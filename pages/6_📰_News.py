import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="News", page_icon="📰", layout="wide")

st.markdown("""
<style>
    .main .block-container { font-size: 17px; }
    .news-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; }
    .disclosure { color: #888; font-size: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📈 Market Analyst")
    st.caption("Educational & research use only")
    st.divider()

from lib.news import market_news, ticker_news
from lib.config import DISCLOSURE

st.title("📰 News")

tab_market, tab_ticker = st.tabs(["🌐 Market Headlines", "🔍 By Ticker"])

with tab_market:
    st.subheader("Market Headlines")
    with st.spinner("Loading news…"):
        headlines = market_news(limit=20)

    if headlines:
        for item in headlines:
            title = item.get("title", "")
            publisher = item.get("publisher", "")
            time_ago = item.get("time_ago", "")
            summary = item.get("summary", "")
            link = item.get("link", "#")
            s = summary[:220] + "…" if len(summary) > 220 else summary
            st.markdown(f"""
            <div class="news-card">
                <a href="{link}" target="_blank" style="color:#5c9bd6;text-decoration:none;font-weight:600;font-size:15px;">{title}</a>
                <div style="color:#888;font-size:12px;margin-top:4px;">{publisher} · {time_ago}</div>
                {"<div style='color:#ccc;font-size:13px;margin-top:6px;line-height:1.5;'>"+s+"</div>" if s else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No headlines available at this time.")

with tab_ticker:
    st.subheader("News by Ticker")
    search_ticker = st.text_input("Enter ticker", placeholder="e.g. AAPL, TSLA, NVDA").upper().strip()

    if search_ticker:
        with st.spinner(f"Loading news for {search_ticker}…"):
            items = ticker_news(search_ticker, limit=15)

        if items:
            for item in items:
                title = item.get("title", "")
                publisher = item.get("publisher", "")
                time_ago = item.get("time_ago", "")
                summary = item.get("summary", "")
                link = item.get("link", "#")
                s = summary[:220] + "…" if len(summary) > 220 else summary
                st.markdown(f"""
                <div class="news-card">
                    <a href="{link}" target="_blank" style="color:#5c9bd6;text-decoration:none;font-weight:600;font-size:15px;">{title}</a>
                    <div style="color:#888;font-size:12px;margin-top:4px;">{publisher} · {time_ago}</div>
                    {"<div style='color:#ccc;font-size:13px;margin-top:6px;line-height:1.5;'>"+s+"</div>" if s else ""}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No recent news found for **{search_ticker}**.")
    else:
        st.info("Enter a ticker symbol above to search for news.")

st.markdown(f'<div class="disclosure">{DISCLOSURE}</div>', unsafe_allow_html=True)
