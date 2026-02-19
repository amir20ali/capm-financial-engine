import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ------------------ LOAD DATA ------------------
stock_name = "فولاد"

file_path = (
    Path.cwd()
    / "1. Extraction/1. pytse_client Library/Stock Data"
    / f"{stock_name}-ت.csv"
)

df = pd.read_csv(file_path)

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

# ------------------ PREPARE HOVER TEXT ------------------
hover_text = (
    "Date (Jalali): " + df["jdate"].astype(str) + "<br>"
    "Open: " + df["open"].map("{:,.0f}".format) + "<br>"
    "High: " + df["high"].map("{:,.0f}".format) + "<br>"
    "Low: " + df["low"].map("{:,.0f}".format) + "<br>"
    "Close: " + df["close"].map("{:,.0f}".format)
)

# ------------------ SUBPLOTS ------------------
fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=[0.75, 0.25]
)

# ------------------ CANDLESTICK ------------------
fig.add_trace(
    go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
        increasing_fillcolor="#26a69a",
        decreasing_fillcolor="#ef5350",
        text=hover_text,
        hoverinfo="text"
    ),
    row=1,
    col=1
)

# ------------------ VOLUME ------------------
fig.add_trace(
    go.Bar(
        x=df["date"],
        y=df["volume"],
        marker_color="rgba(150,150,150,0.4)",
        hoverinfo="skip"
    ),
    row=2,
    col=1
)

# ------------------ AXES ------------------
fig.update_yaxes(
    row=1,
    col=1,
    tickformat=",",
    showgrid=True,
    gridcolor="rgba(255,255,255,0.08)"
)

fig.update_yaxes(
    row=2,
    col=1,
    showgrid=False
)

fig.update_xaxes(
    showgrid=False,
    rangeslider_visible=False
)

# Jalali ticks (sparse)
step = max(len(df) // 10, 1)
fig.update_xaxes(
    tickmode="array",
    tickvals=df["date"].iloc[::step],
    ticktext=df["jdate"].iloc[::step]
)

# ------------------ LAYOUT ------------------
fig.update_layout(
    title=f"{stock_name} – TradingView Style Chart",
    template="plotly_dark",
    hovermode="x unified" ,
    dragmode="pan",
    uirevision=True,
    margin=dict(l=60, r=40, t=60, b=40),
    showlegend=False
)

# ------------------ EXPORT HTML ------------------
fig.write_html(
    "candlestick.html",
    include_plotlyjs="cdn",
    full_html=True,
    auto_open=True,
    config={
        "scrollZoom": True,   # ✅ mouse wheel zoom
        "displaylogo": False,
        "modeBarButtonsToRemove": [
            "lasso2d",
            "select2d",
            "autoScale2d"
        ]
    }
)

print("✅ candlestick.html created and opened in browser")





'''
import pandas as pd
from pathlib import Path
import mplfinance as mpf
import plotly.graph_objects as go

stock_name = "پارسان"

file_path = str(Path.cwd()) + "/1. Extraction/1. pytse_client Library/Stock Data/" + stock_name + "-ت" + ".csv"
print(file_path)
df = pd.read_csv(file_path)

# Set date as index
df.set_index('date', inplace=True)

# Rename columns to standard OHLC names
df.rename(columns={
    'close': 'Close',   # or 'close' if you have it
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'volume': 'Volume'
}, inplace=True)

print(df.head())


mpf.plot(df, type='candle', style = 'charles')
'''
