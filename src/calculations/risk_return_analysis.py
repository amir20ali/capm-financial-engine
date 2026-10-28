import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# Number of return periods in one year, used to annualise.
# TSE has roughly 240 trading days a year.
PERIODS_PER_YEAR = {"D": 240, "W": 52, "M": 12}


def risk_return_analysis(all_Asset_Returns, risk_free_stock, frequency, PROCESSED_DIR):
    """
    Annualised return, risk and Sharpe ratio for every asset.

    Return       = mean(r_t) * k                       (annualised arithmetic mean)
    Risk         = std(r_t) * sqrt(k)                  (annualised volatility)
    rf           = mean(rf_t) * k                      (annualised risk-free rate, all RF periods)
    Sharpe Ratio = (Return - rf) / Risk
    Total Return = prod(1 + r_t) - 1                   (over the whole window, for information)

    k = number of periods per year (240 daily, 52 weekly, 12 monthly).
    Every asset uses ALL of its own periods, and one risk-free rate is used for
    every asset - the same numbers as on the efficient-frontier chart.
    """
    if frequency not in PERIODS_PER_YEAR:
        raise ValueError("frequency must be one of: D, W, M")
    k = PERIODS_PER_YEAR[frequency]

    df = all_Asset_Returns.copy()

    # Remove the period column and make sure everything is numeric
    date_col = df.columns[0]
    returns = df.drop(columns=[date_col]).apply(pd.to_numeric, errors="coerce")

    if risk_free_stock not in returns.columns:
        raise KeyError(f"'{risk_free_stock}' not found in the returns columns")

    # One annualised risk-free rate for the whole window
    rf = returns[risk_free_stock].mean() * k
    print(f"   Risk-free rate (annualised): {rf:.2%}")

    counts = returns.count()
    ann_return = returns.mean() * k
    ann_risk = returns.std() * np.sqrt(k)
    sharpe_ratio = (ann_return - rf) / ann_risk.replace(0, np.nan)
    sharpe_ratio[risk_free_stock] = np.nan     # Sharpe of the risk-free asset itself is not meaningful

    # prod() of an empty column is 1 -> would show a fake 0% return, so mask it
    total_return = ((1 + returns).prod() - 1).where(counts > 0)

    result = pd.DataFrame({
        "Return": ann_return,          # annualised
        "Risk": ann_risk,              # annualised
        "Sharpe Ratio": sharpe_ratio,  # annualised
        "Total Return": total_return,  # whole window, not annualised
        "Counts": counts,
    })

    # Sort output by Sharpe Ratio descending (assets without data go to the end)
    result = result.sort_values("Sharpe Ratio", ascending=False, na_position="last")

    plot_risk_return(result.dropna(subset=["Return", "Risk"]))

    result.to_excel(
        PROCESSED_DIR / "Risk, Return and Sharpe Ratio.xlsx",
        index=True,
        float_format="%.5f",
    )
    print("✅ Risk/Return analysis saved to PROCESSED_DIR")

    return result


def plot_risk_return(result):

    pio.renderers.default = "browser"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=result["Risk"],
        y=result["Return"],
        mode="markers+text",
        text=result.index,
        textposition="top center",
        marker=dict(
            size=14,
            color=result["Sharpe Ratio"],
            colorscale="RdYlGn",
            colorbar=dict(title="Sharpe Ratio"),
            showscale=True,
            line=dict(width=1, color="black"),
        ),
    ))

    fig.update_layout(
        template="plotly_white",
        height=650,
        width=950,
        title=dict(text="Risk vs Return (annualised)", x=0.02),
        xaxis=dict(title="Annualised Risk (Volatility)", tickformat=".0%",
                   showgrid=True, gridcolor="rgba(200,200,200,0.3)"),
        yaxis=dict(title="Annualised Return", tickformat=".0%",
                   showgrid=True, gridcolor="rgba(200,200,200,0.3)"),
        font=dict(size=14),
        hovermode="closest",
    )

    fig.show()
