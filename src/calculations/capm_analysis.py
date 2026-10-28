import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

from src.calculations.risk_return_analysis import PERIODS_PER_YEAR

# Minimum number of periods with asset, market and risk-free data for a regression
MIN_OBS = {"D": 120, "W": 26, "M": 12}

# Series that are not stocks (left out of the cross-sectional SML regression)
NON_STOCKS = ["USD", "usd", "CWI", "EWI", "ACT50", "LCI30"]


def capm_analysis(all_Asset_Returns, market, risk_free_stock, frequency, PROCESSED_DIR):
    """
    CAPM with `market` (e.g. 'CWI') as the market portfolio.

    1) Time-series regression for every asset, on excess returns:
           r_i,t - rf_t = alpha_i + beta_i * (r_m,t - rf_t) + e_i,t
       All numbers of one asset are computed on the SAME periods (where the asset,
       the market and RF all have a return), so:
           Return - CAPM Expected Return = Alpha                     (exactly)
           Total Vol^2 = Systematic Vol^2 + Residual Vol^2           (exactly)
           Systematic Vol^2 / Total Vol^2 = R-squared                (exactly)

    2) Cross-sectional SML regression (one point per stock):
           Excess Return_i = g0 + g1 * Beta_i
       CAPM predicts g0 = 0 and g1 = market risk premium. This is a simple
       check that is consistent with the SML, NOT a complete test of CAPM.
    """
    k = PERIODS_PER_YEAR[frequency]

    date_col = all_Asset_Returns.columns[0]
    returns = all_Asset_Returns.set_index(date_col).apply(pd.to_numeric, errors="coerce")
    rf = returns[risk_free_stock]
    excess = returns.drop(columns=[risk_free_stock]).sub(rf, axis=0)   # NaN where RF is missing

    # ---------------- 1. Time-series regression per asset ----------------
    rows = {}
    for asset in excess.columns:
        if asset == market:
            continue

        pair = excess[[asset, market]].dropna()
        n = len(pair)
        if n < MIN_OBS[frequency]:
            continue

        y, x = pair[asset], pair[market]
        reg = stats.linregress(x, y)

        t_alpha = reg.intercept / reg.intercept_stderr
        p_alpha = 2 * stats.t.sf(abs(t_alpha), n - 2)

        resid = y - reg.intercept - reg.slope * x
        rf_ann = rf.loc[pair.index].mean() * k
        premium = x.mean() * k                               # market risk premium on these periods
        var_sys = reg.slope ** 2 * x.var() * k
        var_res = resid.var() * k

        rows[asset] = {
            "Beta": reg.slope,
            "Beta p-value": reg.pvalue,
            "Alpha (ann.)": reg.intercept * k,
            "Alpha p-value": p_alpha,
            "Return (ann.)": rf_ann + y.mean() * k,
            "CAPM Expected Return (ann.)": rf_ann + reg.slope * premium,
            "Excess Return (ann.)": y.mean() * k,
            "Treynor Ratio": y.mean() * k / reg.slope if reg.slope > 0 else np.nan,
            "R-squared": reg.rvalue ** 2,
            "Annualized Total Volatility": np.sqrt(var_sys + var_res),
            "Annualized Systematic Volatility": np.sqrt(var_sys),
            "Annualized Residual Volatility": np.sqrt(var_res),
            "Observations": n,
        }

    if not rows:
        raise ValueError(f"❌ No asset has {MIN_OBS[frequency]} periods together with {market} and RF")

    result = pd.DataFrame.from_dict(rows, orient="index").sort_values("Beta", ascending=False)

    # ---------------- 2. Cross-sectional SML regression ----------------
    market_ex = excess[market].dropna()
    rf_all = rf.loc[market_ex.index].mean() * k
    premium_all = market_ex.mean() * k

    stocks = result[~result.index.isin(NON_STOCKS)]
    sml = stats.linregress(stocks["Beta"], stocks["Excess Return (ann.)"])
    dof = len(stocks) - 2
    t_g0 = sml.intercept / sml.intercept_stderr                   # H0: g0 = 0
    t_g1 = (sml.slope - premium_all) / sml.stderr                 # H0: g1 = market premium

    summary = pd.Series({
        "Market proxy": market,
        "Frequency": frequency,
        "Risk-free rate (ann.)": rf_all,
        "Market risk premium (ann.)": premium_all,
        "Stocks in SML regression": len(stocks),
        "Average beta": stocks["Beta"].mean(),
        "Stocks with significant alpha (p < 0.05)": int((stocks["Alpha p-value"] < 0.05).sum()),
        "g0 (intercept)": sml.intercept,
        "g0 std. error": sml.intercept_stderr,
        "p-value  H0: g0 = 0": 2 * stats.t.sf(abs(t_g0), dof),
        "g1 (slope)": sml.slope,
        "g1 std. error": sml.stderr,
        "p-value  H0: g1 = market premium": 2 * stats.t.sf(abs(t_g1), dof),
        "Cross-sectional R-squared": sml.rvalue ** 2,
        "Note": "Simple cross-sectional regression consistent with the SML, not a complete "
                "CAPM test (betas are estimated with error and stock returns are correlated).",
    }, name="Value")

    print(f"   CAPM: market premium {premium_all:.2%} | SML slope {sml.slope:.2%} "
          f"| SML intercept {sml.intercept:.2%} | {len(stocks)} stocks")

    # ---------------- 3. Chart and Excel ----------------
    plot_sml(stocks, premium_all, sml, market)

    path = PROCESSED_DIR / "CAPM_Results.xlsx"
    with pd.ExcelWriter(path) as writer:
        result.to_excel(writer, sheet_name="CAPM by asset")
        summary.to_excel(writer, sheet_name="SML regression")
    print(f"✅ CAPM results saved to {path}")

    return result, summary


def plot_sml(stocks, premium, sml, market):
    betas = np.array([min(0, stocks["Beta"].min()) - 0.1, max(1.5, stocks["Beta"].max()) + 0.1])
    colors = np.where(stocks["Alpha p-value"] < 0.05, "crimson", "gray")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=betas, y=betas * premium, mode="lines",
                             name="Theoretical SML", line=dict(color="black")))
    fig.add_trace(go.Scatter(x=betas, y=sml.intercept + sml.slope * betas, mode="lines",
                             name="Fitted line", line=dict(color="orange", dash="dash")))
    fig.add_trace(go.Scatter(x=stocks["Beta"], y=stocks["Excess Return (ann.)"], mode="markers",
                             name="Stocks (red = significant alpha)", text=stocks.index,
                             marker=dict(size=8, color=colors, opacity=0.7),
                             hovertemplate="<b>%{text}</b><br>Beta: %{x:.2f}"
                                           "<br>Excess return: %{y:.2%}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[1], y=[premium], mode="markers", name=f"Market ({market})",
                             marker=dict(size=14, color="green", symbol="diamond")))

    fig.update_layout(title="Security Market Line (excess returns)",
                      xaxis_title="Beta", yaxis=dict(title="Annualized Excess Return", tickformat=".0%"),
                      template="plotly_white", width=1100, height=650)
    fig.show()
