import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Macro", page_icon="🌍", layout="wide")

st.markdown("""
<style>
    .main .block-container { font-size: 17px; }
    .disclosure { color: #888; font-size: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; margin-top: 20px; }
    .ai-output { background: rgba(255,255,255,0.03); border-left: 3px solid #5c9bd6; border-radius: 4px; padding: 16px; font-size: 15px; line-height: 1.6; }
    .indicator-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 12px 16px; text-align: center; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📈 Market Analyst")
    st.caption("Educational & research use only")
    st.divider()

from lib.macro import get_fred_series, get_yield_curve, get_cpi_yoy, get_core_cpi_yoy, get_fred_api
from lib.config import DISCLOSURE
from lib.claude_analyst import macro_pulse

st.title("🌍 Macro Indicators")
st.caption("Data from FRED (Federal Reserve Bank of St. Louis)")

_, fred_err = get_fred_api()
if fred_err:
    st.warning(f"**FRED API not configured.** {fred_err}\n\nAdd `FRED_API_KEY=your_key` to your `.env` file. Get a free key at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html).")
    st.markdown(f'<div class="disclosure">{DISCLOSURE}</div>', unsafe_allow_html=True)
    st.stop()

# Summary cards row
st.subheader("Key Indicators")
indicators_summary = {}

with st.spinner("Loading FRED data…"):
    gdp = get_fred_series("GDP", limit=1)
    unrate = get_fred_series("UNRATE", limit=1)
    cpi_yoy = get_cpi_yoy(limit=2)
    core_cpi = get_core_cpi_yoy(limit=2)
    fedfunds = get_fred_series("FEDFUNDS", limit=1)
    t10y2y = get_fred_series("T10Y2Y", limit=1)

cards = [
    ("Real GDP", gdp, "Bil. $", ".0f"),
    ("Unemployment", unrate, "%", ".1f"),
    ("CPI YoY", cpi_yoy, "%", ".2f"),
    ("Core CPI YoY", core_cpi, "%", ".2f"),
    ("Fed Funds", fedfunds, "%", ".2f"),
    ("10Y-2Y Spread", t10y2y, "%", ".2f"),
]

cols = st.columns(6)
for col, (label, series, unit, fmt) in zip(cols, cards):
    if series is not None and len(series) > 0:
        val = float(series.iloc[-1])
        prev_val = float(series.iloc[-2]) if len(series) >= 2 else None
        delta = val - prev_val if prev_val is not None else None
        indicators_summary[label] = f"{val:{fmt}} {unit}"
        with col:
            st.markdown(f"""
            <div class="indicator-card">
                <div style="color:#aaa;font-size:12px;">{label}</div>
                <div style="font-size:20px;font-weight:700;margin-top:4px;">{val:{fmt}}<span style="font-size:12px;color:#aaa;"> {unit}</span></div>
                {"<div style='font-size:12px;color:" + ("#26a69a" if delta >= 0 else "#ef5350") + ";'>" + ("+" if delta >= 0 else "") + f"{delta:.2f}" + " vs prior</div>" if delta is not None else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        with col:
            st.markdown(f'<div class="indicator-card"><div style="color:#aaa;font-size:12px;">{label}</div><div style="font-size:20px;">—</div></div>', unsafe_allow_html=True)

st.divider()

# Charts
def line_chart(series, title, ylabel, color="#5c9bd6", height=280):
    if series is None or len(series) == 0:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index, y=series.values,
        mode="lines", line=dict(color=color, width=2),
        fill="tozeroy", fillcolor=f"{color}22",
        showlegend=False,
    ))
    fig.update_layout(
        template="plotly_dark", height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        title=dict(text=title, font=dict(size=14)),
        yaxis_title=ylabel,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)"),
    )
    return fig

c1, c2 = st.columns(2)
with c1:
    s = get_fred_series("GDP", limit=40)
    fig = line_chart(s, "Real GDP (Quarterly, Bil. $)", "Bil. $", "#5c9bd6")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with c2:
    s = get_fred_series("UNRATE", limit=120)
    fig = line_chart(s, "Unemployment Rate (%)", "%", "#ffa726")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    s_cpi = get_cpi_yoy(limit=120)
    s_core = get_core_cpi_yoy(limit=120)
    fig = go.Figure()
    if s_cpi is not None and len(s_cpi) > 0:
        fig.add_trace(go.Scatter(x=s_cpi.index, y=s_cpi.values, mode="lines",
                                 line=dict(color="#ef5350", width=2), name="CPI YoY"))
    if s_core is not None and len(s_core) > 0:
        fig.add_trace(go.Scatter(x=s_core.index, y=s_core.values, mode="lines",
                                 line=dict(color="#ffa726", width=2), name="Core CPI YoY"))
    fig.add_hline(y=2.0, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                  annotation_text="2% target", annotation_position="bottom right")
    fig.update_layout(
        template="plotly_dark", height=280,
        margin=dict(l=10, r=10, t=30, b=10),
        title=dict(text="Inflation (CPI YoY %)", font=dict(size=14)),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

with c4:
    s = get_fred_series("FEDFUNDS", limit=120)
    fig = line_chart(s, "Federal Funds Rate (%)", "%", "#26a69a")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

c5, c6 = st.columns(2)
with c5:
    s = get_fred_series("T10Y2Y", limit=500)
    if s is not None and len(s) > 0:
        colors = ["#26a69a" if v >= 0 else "#ef5350" for v in s.values]
        fig = go.Figure(go.Bar(
            x=s.index, y=s.values,
            marker_color=colors,
            showlegend=False,
        ))
        fig.add_hline(y=0, line_color="rgba(255,255,255,0.3)")
        fig.update_layout(
            template="plotly_dark", height=280,
            margin=dict(l=10, r=10, t=30, b=10),
            title=dict(text="10Y-2Y Yield Spread (%)", font=dict(size=14)),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)"),
        )
        st.plotly_chart(fig, use_container_width=True)

with c6:
    s = get_fred_series("RSAFS", limit=60)
    fig = line_chart(s, "Retail Sales (Bil. $)", "Bil. $", "#ab47bc")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

c7, c8 = st.columns(2)
with c7:
    s = get_fred_series("INDPRO", limit=120)
    fig = line_chart(s, "Industrial Production Index", "Index", "#42a5f5")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with c8:
    # Yield curve
    st.subheader("Yield Curve (Current)")
    yc = get_yield_curve()
    if yc is not None:
        maturities = ["3M", "1Y", "2Y", "5Y", "10Y", "30Y"]
        yields = [yc.iloc[0].get(m) for m in maturities]
        valid = [(m, y) for m, y in zip(maturities, yields) if y is not None]
        if valid:
            x_labels = [v[0] for v in valid]
            y_vals = [v[1] for v in valid]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=x_labels, y=y_vals,
                mode="lines+markers",
                line=dict(color="#5c9bd6", width=2),
                marker=dict(size=8, color="#5c9bd6"),
                showlegend=False,
            ))
            fig.update_layout(
                template="plotly_dark", height=250,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)", title="Yield (%)"),
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Yield curve data unavailable.")

st.divider()

# AI macro pulse
st.subheader("AI Macro Pulse-Check")
st.caption("Claude-generated educational economic overview — not investment advice")

if st.button("Generate Macro Analysis", key="macro_ai_btn"):
    with st.spinner("Analyzing macro environment with Claude…"):
        result = macro_pulse(indicators_summary)
    st.markdown(f'<div class="ai-output">{result.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

st.markdown(f'<div class="disclosure">{DISCLOSURE}</div>', unsafe_allow_html=True)
