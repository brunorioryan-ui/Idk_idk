import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _interpolate_zero_crossings(x_vals, y_vals):
    """Insert linearly interpolated zero-crossing points into a series."""
    new_x, new_y = [], []
    for i in range(len(y_vals)):
        new_x.append(x_vals[i])
        new_y.append(y_vals[i])
        if i < len(y_vals) - 1:
            y0, y1 = y_vals[i], y_vals[i + 1]
            if y0 is not None and y1 is not None and y0 * y1 < 0:
                t = y0 / (y0 - y1)
                if hasattr(x_vals[i], "timestamp"):
                    x_cross = x_vals[i] + (x_vals[i + 1] - x_vals[i]) * t
                else:
                    x_cross = x_vals[i] + (x_vals[i + 1] - x_vals[i]) * t
                new_x.append(x_cross)
                new_y.append(0.0)
    return new_x, new_y


def split_traces(x_vals, y_vals, name="", baseline=0.0):
    """Split a series into green (above baseline) and red (below baseline) segments."""
    relative = [v - baseline if v is not None else None for v in y_vals]
    interp_x, interp_y = _interpolate_zero_crossings(list(x_vals), relative)

    green_x, green_y = [], []
    red_x, red_y = [], []

    for i in range(len(interp_y)):
        v = interp_y[i]
        if v is None:
            green_x.append(None)
            green_y.append(None)
            red_x.append(None)
            red_y.append(None)
        elif v >= 0:
            green_x.append(interp_x[i])
            green_y.append(v + baseline)
            red_x.append(interp_x[i])
            red_y.append(None)
        else:
            red_x.append(interp_x[i])
            red_y.append(v + baseline)
            green_x.append(interp_x[i])
            green_y.append(None)

    return green_x, green_y, red_x, red_y


def render_price_chart(
    df: pd.DataFrame,
    ticker: str = "",
    view: str = "Performance",
    show_volume: bool = True,
    baseline_price: float | None = None,
    height: int = 500,
) -> go.Figure:
    """Render a price chart with 4 view modes: Performance, Price, Candlestick, Area."""
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", height=height)
        return fig

    df = df.copy()
    df.index = pd.to_datetime(df.index)

    close = df["Close"].values.tolist()
    x = df.index.tolist()

    # Determine baseline for intraday / performance views
    if baseline_price is not None:
        base = baseline_price
    else:
        base = close[0] if close else 0

    rows = 2 if (show_volume and "Volume" in df.columns and view != "Candlestick") else 1
    row_heights = [0.75, 0.25] if rows == 2 else [1.0]

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    if view == "Performance":
        pct = [(c / base - 1) * 100 if base else 0 for c in close]
        gx, gy, rx, ry = split_traces(x, close, baseline=base)
        gp = [(c / base - 1) * 100 if c is not None and base else None for c in gy]
        rp = [(c / base - 1) * 100 if c is not None and base else None for c in ry]

        fig.add_trace(
            go.Scatter(x=gx, y=gp, mode="lines", line=dict(color="#26a69a", width=2),
                       name="Above baseline", showlegend=False),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=rx, y=rp, mode="lines", line=dict(color="#ef5350", width=2),
                       name="Below baseline", showlegend=False),
            row=1, col=1,
        )
        fig.add_hline(y=0, line_color="rgba(255,255,255,0.3)", line_dash="dash", row=1, col=1)
        yaxis_title = "% Change"
        last_val = pct[-1] if pct else 0
        badge_text = f"{last_val:+.2f}%"
        badge_color = "#26a69a" if last_val >= 0 else "#ef5350"

    elif view == "Price":
        fig.add_trace(
            go.Scatter(x=x, y=close, mode="lines", line=dict(color="#5c9bd6", width=2),
                       name="Price", showlegend=False),
            row=1, col=1,
        )
        yaxis_title = "Price"
        last_val = close[-1] if close else 0
        badge_text = f"${last_val:,.2f}"
        badge_color = "#5c9bd6"

    elif view == "Candlestick":
        fig.add_trace(
            go.Candlestick(
                x=x,
                open=df["Open"].tolist(),
                high=df["High"].tolist(),
                low=df["Low"].tolist(),
                close=close,
                increasing_line_color="#26a69a",
                decreasing_line_color="#ef5350",
                name=ticker,
                showlegend=False,
            ),
            row=1, col=1,
        )
        yaxis_title = "Price"
        last_val = close[-1] if close else 0
        chg = (last_val / base - 1) * 100 if base else 0
        badge_text = f"${last_val:,.2f} ({chg:+.2f}%)"
        badge_color = "#26a69a" if chg >= 0 else "#ef5350"

    elif view == "Area":
        gx, gy, rx, ry = split_traces(x, close, baseline=base)

        fig.add_trace(
            go.Scatter(
                x=gx, y=gy, mode="lines", fill="tozeroy",
                line=dict(color="#26a69a", width=1.5),
                fillcolor="rgba(38,166,154,0.15)",
                name="Up", showlegend=False,
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=rx, y=ry, mode="lines", fill="tozeroy",
                line=dict(color="#ef5350", width=1.5),
                fillcolor="rgba(239,83,80,0.15)",
                name="Down", showlegend=False,
            ),
            row=1, col=1,
        )
        fig.add_hline(y=base, line_color="rgba(255,255,255,0.3)", line_dash="dash", row=1, col=1)
        yaxis_title = "Price"
        last_val = close[-1] if close else 0
        chg = (last_val / base - 1) * 100 if base else 0
        badge_text = f"{chg:+.2f}%"
        badge_color = "#26a69a" if chg >= 0 else "#ef5350"
    else:
        yaxis_title = "Price"
        badge_text = ""
        badge_color = "#5c9bd6"

    # Volume bar chart
    if rows == 2 and "Volume" in df.columns and view != "Candlestick":
        vol = df["Volume"].tolist()
        vol_colors = []
        for i in range(len(close)):
            if i == 0:
                vol_colors.append("#5c9bd6")
            else:
                vol_colors.append("#26a69a" if close[i] >= close[i - 1] else "#ef5350")
        fig.add_trace(
            go.Bar(x=x, y=vol, marker_color=vol_colors, name="Volume", showlegend=False, opacity=0.7),
            row=2, col=1,
        )
        fig.update_yaxes(title_text="Volume", row=2, col=1, showgrid=False)

    # Badge annotation at last point
    if x and badge_text:
        fig.add_annotation(
            x=x[-1], y=1.02, xref="x", yref="paper",
            text=f"<b>{badge_text}</b>",
            showarrow=False,
            font=dict(size=13, color=badge_color),
            bgcolor="rgba(30,30,30,0.8)",
            bordercolor=badge_color,
            borderwidth=1,
            borderpad=4,
            xanchor="right",
        )

    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis_title=yaxis_title,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.07)", row=1, col=1)

    return fig


def render_gauge(value: float, title: str, subtitle: str = "", height: int = 250) -> go.Figure:
    """Render a gauge chart (0-100) with red-to-green gradient."""
    color = (
        "#ef5350" if value < 30
        else "#ffa726" if value < 50
        else "#ffee58" if value < 70
        else "#26a69a"
    )

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": f"<b>{title}</b><br><span style='font-size:11px;color:#aaa'>{subtitle}</span>",
                   "font": {"size": 14}},
            number={"font": {"size": 28, "color": color}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#666"},
                "bar": {"color": color, "thickness": 0.3},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 20], "color": "rgba(239,83,80,0.25)"},
                    {"range": [20, 40], "color": "rgba(255,152,0,0.2)"},
                    {"range": [40, 60], "color": "rgba(255,238,88,0.15)"},
                    {"range": [60, 80], "color": "rgba(38,166,154,0.2)"},
                    {"range": [80, 100], "color": "rgba(38,166,154,0.35)"},
                ],
                "threshold": {
                    "line": {"color": color, "width": 3},
                    "thickness": 0.75,
                    "value": value,
                },
            },
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def render_sparkline(x_vals, y_vals, baseline: float | None = None, height: int = 60, width: int = 120) -> go.Figure:
    """Tiny sparkline for market cards."""
    fig = go.Figure()
    if not y_vals:
        fig.update_layout(template="plotly_dark", height=height, margin=dict(l=0, r=0, t=0, b=0))
        return fig

    base = baseline if baseline is not None else y_vals[0]
    gx, gy, rx, ry = split_traces(list(x_vals), list(y_vals), baseline=base)

    fig.add_trace(go.Scatter(x=gx, y=gy, mode="lines", line=dict(color="#26a69a", width=1.5), showlegend=False))
    fig.add_trace(go.Scatter(x=rx, y=ry, mode="lines", line=dict(color="#ef5350", width=1.5), showlegend=False))

    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig
