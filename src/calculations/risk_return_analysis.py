import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

def risk_return_analysis(all_Asset_Returns, risk_free_stock, PROCESSED_DIR):

    df = all_Asset_Returns.copy()

    # ستون زمان را حذف می‌کنیم
    date_col = df.columns[0]
    returns = df.drop(columns=[date_col])

    # تبدیل به عدد
    #returns = returns.apply(pd.to_numeric, errors='coerce').fillna(0)

    # ---- بازده کل دوره ----
    total_return = (1 + returns).prod() - 1

    if risk_free_stock in total_return.index:
        risk_free_rate = total_return.loc[risk_free_stock]
    else:
        raise KeyError(f"'{risk_free_stock}' not found in total_return.index")
    
    # Calculate excess returns
    excess_returns = total_return.subtract(risk_free_rate)

    # ---- ریسک (انحراف معیار) ----
    volatility = returns.std()

    # اگر دیتای روزانه است → سالانه کنیم: از تعداد مشاهدات واقعی برای هر دارایی استفاده می‌کنیم
    counts = returns.count()
    total_vol = volatility * (counts ** 0.5)

    # ساخت DataFrame نهایی
    # محافظت در برابر تقسیم بر صفر هنگام محاسبه Sharpe Ratio
    sharpe_ratio = excess_returns / total_vol.replace(0, pd.NA)

    result = pd.DataFrame({
        "Return": total_return,
        "Risk": total_vol,
        "Sharpe Ratio": sharpe_ratio,
        "Counts": counts
    })

    # Sort output by Sharpe Ratio descending
    result = result.sort_values("Sharpe Ratio", ascending=False)

    # ---- رسم نمودار ----
    plot_risk_return(result)

    # خروجی مرتب شده روی Sharpe Ratio

    result.to_excel(
        PROCESSED_DIR / 'Risk, Return and Sharpe Ratio.xlsx',
        index=True,
        float_format='%.5f'
    )

    print("✅ Risk/Return analysis saved to PROCESSED_DIR")

    return result


def plot_risk_return(result):

    pio.renderers.default = "browser"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=result["Risk"],
        y=result["Return"],
        mode='markers+text',
        text=result.index,   # نمایش نام سهام
        textposition="top center",
        marker=dict(
            size=14,
            color=result["Sharpe Ratio"],   # رنگ بر اساس Sharpe Ratio
            colorscale="RdYlGn",            # سبز خوب، قرمز بد
            colorbar=dict(title="Sharpe Ratio"),
            showscale=True,
            line=dict(width=1, color='black')
        )
    ))

    fig.update_layout(
        template="plotly_white",
        height=650,
        width=950,
        title=dict(
            text="Risk vs Return (Portfolio View)",
            x=0.02
        ),
        xaxis=dict(
            title="Risk (Volatility)",
            tickformat=".0%",
            showgrid=True,
            gridcolor="rgba(200,200,200,0.3)"
        ),
        yaxis=dict(
            title="Return",
            tickformat=".0%", 
            showgrid=True,
            gridcolor="rgba(200,200,200,0.3)"
        ),
        font=dict(size=14),
        hovermode="closest"
    )

    fig.show()