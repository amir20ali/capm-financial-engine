import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.optimize import minimize

from src.calculations.risk_return_analysis import PERIODS_PER_YEAR


def efficient_frontier(watchout_Assets, all_Asset_Returns, risk_free_stock, frequency,
                       PROCESSED_DIR, n_points=50, min_obs=10, estimation="full"):
    """
    Long-only Markowitz frontier for the watchout assets, on ONE annual scale:

        portfolio return = w' mu
        portfolio risk   = sqrt(w' Sigma w)

    estimation = "full"   (default)
        mu_i    = mean(r_i) * k           each asset over ALL its own periods
        sigma_i = std(r_i)  * sqrt(k)     each asset over ALL its own periods
        rho     = correlation matrix from the COMMON sample (dates where all assets have data)
        Sigma   = diag(sigma) @ rho @ diag(sigma)
        rf      = mean(rf_t) * k          over all RF periods
        -> asset stars are EXACTLY the values in "Risk, Return and Sharpe Ratio.xlsx"
           (same numbers as the Risk vs Return chart), and Sigma is always valid.

    estimation = "common"
        mu, Sigma and rf all from the common sample only (textbook, but returns can
        differ a lot from the risk/return table when assets have different histories).

    In both cases a portfolio with 100% in one asset lands exactly on that asset's star.

    The whole curve is kept (also the part below the minimum-variance point);
    that lower part is drawn in grey and flagged Efficient = False in Excel.
    """
    if frequency not in PERIODS_PER_YEAR:
        raise ValueError("frequency must be one of: D, W, M")
    k = PERIODS_PER_YEAR[frequency]

    # ------------------------------------------------------------------
    # 1. Common sample: only periods where ALL selected assets and RF have a return
    # ------------------------------------------------------------------
    date_col = all_Asset_Returns.columns[0]
    returns = (all_Asset_Returns
               .set_index(date_col)
               .apply(pd.to_numeric, errors="coerce"))

    if risk_free_stock not in returns.columns:
        raise KeyError(f"'{risk_free_stock}' not found in the returns columns")

    assets = [a for a in watchout_Assets if a in returns.columns and a != risk_free_stock]
    missing = [a for a in watchout_Assets if a not in returns.columns]
    if missing:
        print(f"   ⚠️  Assets not found in the data and skipped: {missing}")
    if len(assets) < 2:
        raise ValueError("❌ Need at least 2 watchout assets with data")

    # "full":   common dates are needed ONLY for the correlations between the assets,
    #           so RF is not required here (RF is not part of the correlation matrix).
    # "common": everything, including RF, comes from the same dates.
    if estimation == "common":
        sample = returns[assets + [risk_free_stock]].dropna()
    else:
        sample = returns[assets].dropna()
    n_obs, n_assets = len(sample), len(assets)

    print(f"   Estimation: {estimation}. Common sample (for correlations): {n_obs} periods ({sample.index[0]} → {sample.index[-1]}) "
          f"for {n_assets} assets")
    if n_obs < max(min_obs, n_assets + 1):
        raise ValueError(
            f"❌ Only {n_obs} common periods for {n_assets} assets. "
            "Remove assets with short history or use a longer window / higher frequency."
        )

    R = sample[assets]
    if estimation == "full":
        full = returns[assets]
        mu = (full.mean() * k).values                # same as the risk/return table
        vol = (full.std() * np.sqrt(k)).values       # same as the risk/return table
        corr = R.corr().values                       # co-movement from common dates
        Sigma = np.outer(vol, vol) * corr
        rf = returns[risk_free_stock].mean() * k
    elif estimation == "common":
        mu = (R.mean() * k).values
        Sigma = (R.cov() * k).values
        rf = sample[risk_free_stock].mean() * k
    else:
        raise ValueError('estimation must be "full" or "common"')

    # With a common sample Sigma is always valid; guard only against near-singularity
    min_eig = np.linalg.eigvalsh(Sigma).min()
    if min_eig < 1e-10:
        ridge = 1e-6 * np.trace(Sigma) / n_assets
        Sigma = Sigma + np.eye(n_assets) * ridge
        print(f"   ⚠️  Covariance nearly singular (min eigenvalue {min_eig:.2e}); "
              f"added ridge {ridge:.2e}")

    # ------------------------------------------------------------------
    # 2. Helpers
    # ------------------------------------------------------------------
    def port_return(w):
        return float(w @ mu)

    def port_risk(w):
        return float(np.sqrt(max(w @ Sigma @ w, 0.0)))

    def variance(w):
        return float(w @ Sigma @ w)

    def variance_grad(w):
        return 2.0 * Sigma @ w

    bounds = [(0.0, 1.0)] * n_assets                 # long only, no leverage
    sum_to_one = {"type": "eq", "fun": lambda w: w.sum() - 1.0,
                  "jac": lambda w: np.ones_like(w)}
    w0 = np.full(n_assets, 1.0 / n_assets)
    opts = {"ftol": 1e-12, "maxiter": 1000}

    # ------------------------------------------------------------------
    # 3. Frontier: minimise variance for each target return
    # ------------------------------------------------------------------
    targets = np.linspace(mu.min(), mu.max(), n_points)
    rows, failed = [], 0

    for target in targets:
        cons = [sum_to_one,
                {"type": "eq", "fun": lambda w, t=target: w @ mu - t,
                 "jac": lambda w: mu}]
        res = minimize(variance, w0, jac=variance_grad, method="SLSQP",
                       bounds=bounds, constraints=cons, options=opts)
        if res.success and abs(port_return(res.x) - target) < 1e-6:
            w = np.clip(res.x, 0, None)
            w = w / w.sum()
            rows.append((port_return(w), port_risk(w), w))
        else:
            failed += 1

    if not rows:
        raise ValueError("❌ Optimization failed for all target returns!")
    if failed:
        print(f"   ⚠️  {failed} optimizations failed")

    # Global minimum-variance portfolio (no return target)
    gmv = minimize(variance, w0, jac=variance_grad, method="SLSQP",
                   bounds=bounds, constraints=[sum_to_one], options=opts).x
    gmv_ret, gmv_risk = port_return(gmv), port_risk(gmv)

    # Tangency (maximum-Sharpe) portfolio
    def neg_sharpe(w):
        return -(port_return(w) - rf) / max(port_risk(w), 1e-12)

    tan = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds,
                   constraints=[sum_to_one], options=opts).x
    tan_ret, tan_risk = port_return(tan), port_risk(tan)
    tan_sharpe = (tan_ret - rf) / tan_risk

    frontier_returns = np.array([r[0] for r in rows])
    frontier_risks = np.array([r[1] for r in rows])
    weights = np.array([r[2] for r in rows])
    sharpe = (frontier_returns - rf) / frontier_risks
    efficient = frontier_returns >= gmv_ret - 1e-12

    # ------------------------------------------------------------------
    # 4. Plot
    # ------------------------------------------------------------------
    asset_risk = np.sqrt(np.diag(Sigma))
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=frontier_risks[~efficient], y=frontier_returns[~efficient],
        mode="lines+markers", name="Inefficient part (below min-variance)",
        line=dict(color="lightgray", dash="dash"),
        marker=dict(size=6, color="lightgray"),
        hovertemplate="Risk: %{x:.2%}<br>Return: %{y:.2%}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=frontier_risks[efficient], y=frontier_returns[efficient],
        mode="lines+markers", name="Efficient frontier",
        line=dict(color="rgba(60,60,60,0.5)"),
        marker=dict(size=8, color=sharpe[efficient], colorscale="Viridis",
                    showscale=True, colorbar=dict(title="Sharpe<br>Ratio"),
                    line=dict(width=0.5, color="black")),
        customdata=sharpe[efficient],
        hovertemplate="Risk: %{x:.2%}<br>Return: %{y:.2%}<br>Sharpe: %{customdata:.2f}<extra></extra>",
    ))

    # Capital Market Line from the risk-free rate through the tangency portfolio
    x_max = max(frontier_risks.max(), asset_risk.max()) * 1.05
    fig.add_trace(go.Scatter(
        x=[0, x_max], y=[rf, rf + tan_sharpe * x_max],
        mode="lines", name="Capital Market Line",
        line=dict(color="orange", dash="dot"),
    ))

    fig.add_trace(go.Scatter(
        x=asset_risk, y=mu, mode="markers+text", text=assets,
        textposition="top center", name="Watchout assets",
        marker=dict(size=12, color="red", symbol="star", line=dict(width=1, color="darkred")),
        hovertemplate="<b>%{text}</b><br>Risk: %{x:.2%}<br>Return: %{y:.2%}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[gmv_risk], y=[gmv_ret], mode="markers", name="Minimum-variance portfolio",
        marker=dict(size=14, color="blue", symbol="diamond"),
    ))
    fig.add_trace(go.Scatter(
        x=[tan_risk], y=[tan_ret], mode="markers", name=f"Max-Sharpe portfolio ({tan_sharpe:.2f})",
        marker=dict(size=14, color="green", symbol="diamond"),
    ))
    fig.add_trace(go.Scatter(
        x=[0], y=[rf], mode="markers", name=f"Risk-free ({rf:.2%})",
        marker=dict(size=10, color="orange"),
    ))

    fig.update_layout(
        title=f"Efficient Frontier (annualised, estimation: {estimation})",
        xaxis=dict(title="Annualised Risk (Standard Deviation)", tickformat=".0%"),
        yaxis=dict(title="Annualised Expected Return", tickformat=".0%"),
        hovermode="closest", width=1200, height=700, template="plotly_white",
        legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="black", borderwidth=1),
    )
    fig.show()

    # ------------------------------------------------------------------
    # 5. Save to Excel
    # ------------------------------------------------------------------
    portfolios = pd.DataFrame(weights, columns=assets)
    portfolios.insert(0, "Efficient", efficient)
    portfolios.insert(0, "Sharpe Ratio", sharpe)
    portfolios.insert(0, "Risk", frontier_risks)
    portfolios.insert(0, "Return", frontier_returns)
    portfolios.index = [f"Portfolio_{i + 1}" for i in range(len(portfolios))]

    special = pd.DataFrame(
        [[gmv_ret, gmv_risk, (gmv_ret - rf) / gmv_risk, True, *gmv],
         [tan_ret, tan_risk, tan_sharpe, True, *tan]],
        columns=portfolios.columns, index=["Min_Variance", "Max_Sharpe"],
    )

    inputs = pd.DataFrame({"Ann. Return": mu, "Ann. Risk": asset_risk,
                           "Sharpe Ratio": (mu - rf) / asset_risk}, index=assets)
    info = pd.DataFrame({"Value": [estimation, str(sample.index[0]), str(sample.index[-1]), n_obs, k, rf]},
                        index=["Estimation", "Common sample start", "Common sample end",
                               "Common periods", "Periods per year", "Risk-free rate (ann.)"])

    path = PROCESSED_DIR / "Efficient_Frontier_Portfolios.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.concat([special, portfolios]).to_excel(writer, sheet_name="Portfolios", float_format="%.5f")
        inputs.to_excel(writer, sheet_name="Asset inputs", float_format="%.5f")
        pd.DataFrame(Sigma, index=assets, columns=assets).to_excel(
            writer, sheet_name="Covariance (ann.)", float_format="%.6f")
        info.to_excel(writer, sheet_name="Sample info")
    print(f"✅ Efficient Frontier portfolios saved to {path}")

    return frontier_returns, frontier_risks, fig
