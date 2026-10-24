import pandas as pd
import plotly.graph_objects as go

def investment_Result(watchout_Assets, all_Asset_Returns):
    df = all_Asset_Returns.copy()

    # ستون اول (زمان یا label)
    date_col = df.columns[0]
    dates = df[date_col]

    # فیلتر دارایی‌ها و تبدیل عددی
    returns = df[watchout_Assets].apply(pd.to_numeric, errors='coerce').fillna(0)

    # بازده تجمعی
    growth = (1 + returns).cumprod() - 1

    # ---- اضافه کردن سطر Start با مقدار صفر ----
    zero_row = pd.DataFrame([[0]*len(growth.columns)], columns=growth.columns)
    growth = pd.concat([zero_row, growth], ignore_index=True)

    # ستون X دلخواه (Start + بقیه ماه‌ها)
    dates = df[date_col].astype(str).reset_index(drop=True)
    x_labels = pd.concat([pd.Series(["Start"]), dates.reset_index(drop=True)], ignore_index=True)

    # ساخت DataFrame نهایی
    result = pd.concat([x_labels, growth], axis=1)
    result.columns = [date_col] + list(growth.columns)
    result.set_index(date_col, inplace=True)

    # رسم نمودار
    financial_chart(result)

    return result.reset_index()

def financial_chart(result):
    fig = go.Figure()

    # …ensure index entries are strings…
    result = result.copy()
    result.index = result.index.astype(str)

    from plotly.express import colors as pxcolors
    colors = pxcolors.qualitative.Dark24

    for i, col in enumerate(result.columns):
        fig.add_trace(
            go.Scatter(
                x=result.index,
                y=result[col],
                mode='lines',
                name=col,
                line=dict(width=3,
                          color=colors[i % len(colors)],
                          shape='spline', smoothing=1.1)
            )
        )

    fig.update_layout(
        template="plotly_white",
        height=600,
        width=1200,
        plot_bgcolor="#f8f8f8",
        hovermode="x unified",
        title=dict(text="Cumulative Return", x=0.01, xanchor="left"),
        xaxis=dict(
            type="category",
            showgrid=True,
            gridcolor="rgba(150,150,150,0.2)",
            showline=True,
            linecolor="black",
            tickangle=-45,
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(150,150,150,0.2)",
            showline=True,
            linecolor="black",
            tickformat=".1%",
            title="Cumulative Return"
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
        font=dict(family="Arial", size=14, color="black")
    )

    fig.write_html("report.html", auto_open=True)