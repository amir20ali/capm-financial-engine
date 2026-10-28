# CAPM Financial Engine — Tehran Stock Exchange

A Python pipeline that downloads price data for stocks listed on the **Tehran Stock Exchange (TSE, main Bourse market)** together with key market and macro series, and turns it into:

- per-period returns for every asset (daily, weekly or monthly),
- an **annualised** risk / return / Sharpe-ratio table for all assets,
- covariance and correlation matrices,
- a cumulative-return chart for a chosen set of "watchout" assets,
- a long-only **Markowitz efficient frontier** for those assets, with the minimum-variance portfolio, the maximum-Sharpe (tangency) portfolio, the Capital Market Line, and the weights of every portfolio on the curve,
- a **CAPM analysis** of every asset against the market index (CWI): beta, Jensen's alpha with p-values, R², Treynor ratio, systematic vs. residual volatility, the **Security Market Line** chart, and a simple cross-sectional regression consistent with the SML.

All prices can be analysed **in rial** or **re-based on another series** (for example in USD terms), which matters a lot in a high-inflation economy.

> **Status:** work in progress — see [Known limitations](#known-limitations) and [Roadmap](#roadmap).

---

## Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Quick start](#quick-start)
5. [The interactive menu, step by step](#the-interactive-menu-step-by-step)
6. [Project structure](#project-structure)
7. [Data sources](#data-sources)
8. [Risk-free rate — important limitation](#risk-free-rate--important-limitation)
9. [Outputs](#outputs)
10. [Methodology](#methodology)
11. [Configuration you may want to change](#configuration-you-may-want-to-change)
12. [FAQ / troubleshooting](#faq--troubleshooting)
13. [Known limitations](#known-limitations)
14. [Roadmap](#roadmap)
15. [Disclaimer](#disclaimer)

---

## Features

| Area | What it does |
|---|---|
| Data extraction | Builds the current list of main-Bourse tickers and downloads **dividend- and capital-increase-adjusted** price history for each one, using either `finpy-tse` or `pytse-client`. |
| Market & macro data | Downloads the USD/IRR free-market rate, the Total Index (CWI), Equal-Weighted Index (EWI), ACT50, LCI30, and a fixed-income fund used as the risk-free asset (RF). |
| Price base | Analyse prices in rial (`None`), or divide every price by any macro series (e.g. `USD`) to get returns in that unit. |
| Frequencies | Daily, weekly or monthly (last close of each period). |
| Data cleaning | Stocks with no prices in the analysis window are dropped. Prices are forward-filled across non-trading days, but no return is invented for a period with no real price. Newly listed stocks are only used from 60 days after their first trading day. |
| Risk / return | Annualised return, annualised volatility, annualised Sharpe ratio (excess over one annualised risk-free rate), total return over the window, number of observations. |
| Portfolio | Long-only efficient frontier (no short selling, no leverage, weights sum to 1), solved with SciPy SLSQP using the same returns and risks as the risk/return table; minimum-variance and maximum-Sharpe portfolios; Capital Market Line. |
| CAPM | For every asset, an OLS regression of its excess return on the market's excess return (market = CWI): beta, annualised Jensen's alpha, p-values, R², Treynor ratio, CAPM expected return, systematic and residual volatility. A cross-sectional regression of excess return on beta is compared with the SML that CAPM predicts. |
| Visualisation | Interactive Plotly charts: risk-vs-return scatter, cumulative returns, efficient frontier, Security Market Line. |

---

## Requirements

- **Python 3.10 or newer**
- Internet access to **TSETMC** (only for the data-download step)
- The following Python packages:

| Package | Version | Used for |
|---|---|---|
| `pandas` | ≥ 2.0 | all data handling |
| `numpy` | ≥ 1.24 | numerical work |
| `scipy` | ≥ 1.10 | SLSQP optimiser for the efficient frontier |
| `openpyxl` | ≥ 3.1 | reading / writing the `.xlsx` outputs |
| `plotly` | ≥ 5.15 | interactive charts (open in your web browser) |
| `finpy-tse` | ≥ 1.2.10 | stock list, adjusted prices, USD/IRR, CWI, EWI, ACT50, LCI30, RF fund |
| `pytse-client` | ≥ 0.19 | alternative source for adjusted stock prices |

Install them all with one command:

```bash
pip install "pandas>=2.0" "numpy>=1.24" "scipy>=1.10" "openpyxl>=3.1" "plotly>=5.15" "finpy-tse>=1.2.10" "pytse-client>=0.19"
```

---

## Installation

```bash
git clone https://github.com/amir20ali/capm-financial-engine.git
cd capm-financial-engine

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install "pandas>=2.0" "numpy>=1.24" "scipy>=1.10" "openpyxl>=3.1" "plotly>=5.15" "finpy-tse>=1.2.10" "pytse-client>=0.19"
```

---

## Quick start

```bash
python Main.py
```

Always run it **from the project root folder** (the folder that contains `Main.py`), otherwise the `src.` and `config` imports fail.

On the very first run answer **Yes** to "Do you want to extract the data now?". Later runs can answer **No** and reuse the files already in `data/raw/`.

---

## The interactive menu, step by step

| # | Question | Options | Notes |
|---|---|---|---|
| 1 | Do you want to extract the data now? | Yes / No | **Yes** downloads the stock list, all stock prices and all macro series. This takes a while (hundreds of tickers). **No** uses existing files. |
| 2 | Select data source | Pytse Client Library / Finpy TSE Library | Which library's stock files to use. Must match the source you downloaded with. |
| 3 | Analysis start date | Year, Month, Day (Gregorian) | Dates are **Gregorian**, not Jalali. Must be within the last ~5 years so that risk-free data exists (see below). |
| 4 | Analysis end date | Year, Month, Day (Gregorian) | Must be after the start date. |
| 5 | Analysis frequency | Daily / Weekly / Monthly | Price of each period = last close in that period. **Weekly is recommended.** |
| 6 | Which macro series should be the base? | None / USD / CWI / EWI / ACT50 / LCI30 / RF | **None** = analyse in rial. **USD** = every price is divided by the dollar rate, so returns are in USD terms. |

After the menu the pipeline runs every step automatically and opens the charts in your browser.

---

## Project structure

```
capm-financial-engine/
├── Main.py                      # entry point – interactive pipeline
├── config.py                    # folder paths (data/raw, data/processed, …)
├── README.md
├── src/
│   ├── stock_list/
│   │   └── get_stock_list.py    # list of main-Bourse tickers
│   ├── extraction/
│   │   ├── finpy_tse/           # stock price download via finpy-tse
│   │   ├── pytse_client/        # stock price download via pytse-client
│   │   └── macroEconomy/        # USD, CWI, EWI, ACT50, LCI30, RF
│   └── calculations/
│       ├── all_Assets_Prices.py             # align prices, choose frequency & base, drop empty assets
│       ├── calculate_Returns.py             # per-period returns
│       ├── risk_return_analysis.py          # annualised return, risk, Sharpe table + chart
│       ├── investment_Result.py             # cumulative-return chart
│       ├── efficient_frontier_calculation.py # Markowitz frontier, max-Sharpe portfolio, CML
│       └── capm_analysis.py                 # beta, alpha, Treynor, SML regression
└── data/                        # created automatically, not tracked by git
    ├── raw/
    │   ├── stock_list/stock_list.csv
    │   ├── finpy_stock_data/<ticker>.csv
    │   ├── Pytse_stock_data/<ticker>.csv
    │   └── macroeconomy_data/USD.csv, CWI.csv, EWI.csv, ACT50.csv, LCI30.csv, RF.csv
    └── processed/               # every result file is written here
```

The `data/` folder is created the first time you run the code (by `config.py`) and is excluded from git, so a fresh clone has **no data** until you run the extraction step.

---

## Data sources

All data comes from the public **TSETMC** website through two open-source libraries:

| Series | Library / function | Adjusted? |
|---|---|---|
| Ticker list (main Bourse only) | `finpy_tse.Build_Market_StockList(bourse=True)` | – |
| Stock prices | `finpy_tse.Get_Price_History(adjust_price=True)` **or** `pytse_client.download(adjust=True)` | Yes – adjusted for dividends and capital increases |
| USD/IRR (free market) | `finpy_tse.Get_USD_RIAL` | – |
| CWI – Total Index | `finpy_tse.Get_CWI_History` | – |
| EWI – Equal-Weighted Index | `finpy_tse.Get_EWI_History` | – |
| ACT50 – 50 most active | `finpy_tse.Get_ACT50_History` | – |
| LCI30 – 30 large companies | `finpy_tse.Get_LCI30_History` | – |
| RF – risk-free proxy | `finpy_tse.Get_Price_History(stock='کارا')`, a fixed-income fund (ETF) | No (unadjusted fund price) |

Both stock sources are saved with the same file name, `<ticker>.csv`. (pytse-client itself names adjusted files `<ticker>-ت.csv`; the extraction step renames them, and the loader accepts both names.)

---

## Risk-free rate — important limitation

The risk-free rate is **not a fixed number you type in**. It is the realised return of the fixed-income fund **«کارا»** over your analysis window, annualised (`rf = mean(rfₜ) × k`). The same rate is used for every asset in the Sharpe table and on the efficient-frontier chart, and it is printed in the console.

> ⚠️ **Risk-free (RF) data is available only for roughly the last 5 years.**
> If your analysis start date is earlier than the first available RF price, the risk-free rate is calculated only from the part of the window where RF exists, while the stocks use the whole window, so the comparison is no longer like-for-like. Choose a start date **within the last 5 years**.

Two more points to keep in mind:

- If you choose **USD** (or any other series) as the price base, the RF fund is re-based too. A rial fixed-income fund is **not risk-free in USD terms** – when the dollar rises sharply its USD return is strongly negative, which makes every Sharpe ratio look better than it is. Interpret USD-based Sharpe ratios with care.
- The RF fund price is used **unadjusted**. This is correct only as long as the fund accumulates its income in its price (no periodic cash payouts).

---

## Outputs

Everything is written to `data/processed/`:

| File | Content |
|---|---|
| `all_Assets_Prices.xlsx` | One row per period, one column per asset (stocks + macro series), after re-basing. |
| `all_Assets_Returns.xlsx` | Per-period simple returns. Empty cell = no real price in that period (halt, not listed yet, etc.). |
| `Risk, Return and Sharpe Ratio.xlsx` | For every asset: `Return`, `Risk`, `Sharpe Ratio`, `Total Return`, `Counts`, sorted by Sharpe ratio. |
| `cov_matrix.xlsx` / `corr_matrix.xlsx` | Covariance and correlation of per-period returns for all assets (pairwise, for information). |
| `Efficient_Frontier_Portfolios.xlsx` | Sheet **Portfolios**: `Min_Variance`, `Max_Sharpe` and 50 frontier portfolios with `Return`, `Risk`, `Sharpe Ratio`, `Efficient` (False = below the minimum-variance point) and the weight of each asset. Sheet **Asset inputs**: annualised return, risk and Sharpe of each asset as used by the optimiser. Sheet **Covariance (ann.)**: the matrix used by the optimiser. Sheet **Sample info**: estimation method, common-sample start/end and length, risk-free rate. |
| `CAPM_Results.xlsx` | Sheet **CAPM by asset**: one row per asset (columns below). Sheet **SML regression**: risk-free rate, market risk premium, average beta, number of stocks with significant alpha, and the cross-sectional regression (γ₀, γ₁, standard errors, p-values against the CAPM values). |
| `report.html` | Interactive cumulative-return chart (written to the folder you run from). |

### How to read the result columns

| Column | Formula | Meaning |
|---|---|---|
| `Return` | `mean(rₜ) × k` | Annualised (arithmetic) expected return |
| `Risk` | `std(rₜ) × √k` | Annualised volatility |
| `Sharpe Ratio` | `(Return − rf) / Risk`, with `rf = mean(rfₜ) × k` | Annualised Sharpe ratio, same value as on the frontier chart |
| `Total Return` | `∏(1 + rₜ) − 1` | What you actually earned over the whole window (not annualised) |
| `Counts` | number of real returns | Assets with a small count (recent listing, long halts) have unreliable statistics |

`k` = periods per year: **240** daily, **52** weekly, **12** monthly. The Sharpe ratio of the RF asset itself is left empty.

### How to read the CAPM columns

All numbers of one asset are computed on the **same periods** – those where the asset, the market and RF all have a return – so the columns fit together exactly.

| Column | Formula | Meaning |
|---|---|---|
| `Beta` | slope of `rᵢ,ₜ − rfₜ` on `r_m,ₜ − rfₜ` | Sensitivity to the market. β > 1 moves more than the market, β < 1 less, β < 0 against it. |
| `Beta p-value` | t-test, H₀: β = 0 | Below 0.05 = the asset is significantly related to the market. |
| `Alpha (ann.)` | regression intercept × k | Jensen's alpha: annual return **not explained** by the market. |
| `Alpha p-value` | t-test, H₀: α = 0 | Below 0.05 = significant alpha. With few years of data most alphas are not significant. |
| `Return (ann.)` | `rf + mean(rᵢ − rf) × k` | Average annual return on the regression periods. Can differ slightly from the risk/return table for assets with gaps. |
| `CAPM Expected Return (ann.)` | `rf + β × market premium` | Return CAPM predicts for this beta. **`Return − CAPM Expected Return = Alpha`** exactly. |
| `Excess Return (ann.)` | `mean(rᵢ − rf) × k` | Return above the risk-free rate (used on the SML chart). |
| `Treynor Ratio` | `Excess Return / β` | Excess return per unit of market risk. Empty when β ≤ 0. |
| `R-squared` | | Share of the asset's variance explained by the market. |
| `Annualized Total Volatility` | `std(rᵢ − rf) × √k` | Total risk on the regression periods. |
| `Annualized Systematic Volatility` | `|β| × std(r_m − rf) × √k` | Market-driven part of the risk. |
| `Annualized Residual Volatility` | `std(residuals) × √k` | Company-specific part of the risk (removable by diversification). |
| `Observations` | | Number of regression periods. Assets with fewer than 26 (weekly), 12 (monthly) or 120 (daily) are skipped. |

**Volatilities do not add up – variances do:** `Total² = Systematic² + Residual²`, and `Systematic² / Total² = R²`.

---

## Methodology

1. **Price alignment** – each asset's daily closes are filtered to the analysis window and grouped into periods (day / Monday–Sunday week / calendar month); the **last close** in each period is the period price. All assets are merged on the period label (outer join).
2. **New listings** – if an asset's first price is after the start date, its first 60 days are skipped to avoid the abnormal behaviour right after an IPO.
3. **Re-basing** – if a base series is selected, every price column is divided by that series on the same period.
4. **Empty assets** – assets with fewer than `min_obs` real prices in the window are removed (default 1, i.e. completely empty assets).
5. **Returns** – simple returns `Pₜ₊₁ / Pₜ − 1`. Prices are forward-filled so a return after a gap is measured from the last real price; a return is left empty when the next real price is missing. The return is labelled with the date of the **start** of the period.
6. **Risk / return table** – annualised, see the table above. Each asset uses all of its own periods, and one annualised risk-free rate is used for every asset.
7. **Covariance / correlation files** – pandas `cov()` / `corr()` on per-period returns (pairwise over overlapping dates). These files are for information only; the optimiser does **not** use them.
8. **Efficient frontier**
   - Expected returns and volatilities: `μᵢ = mean(rᵢ) × k` and `σᵢ = std(rᵢ) × √k`, each asset over **all** its own periods – exactly the numbers in `Risk, Return and Sharpe Ratio.xlsx` and the Risk vs Return chart.
   - Correlations: from the **common sample**, i.e. only the periods where every selected asset has a return (correlations must be measured on the same dates).
   - Covariance: `Σ = diag(σ) · ρ · diag(σ)`, which is always a valid matrix. Risk-free rate: `rf = mean(rfₜ) × k`.
   - So the asset stars on the frontier chart are at the same positions as in the Risk vs Return chart, and a 100 % single-asset portfolio sits exactly on that asset's star.
   - Optional: `efficient_frontier(..., estimation="common")` estimates μ, σ and ρ all from the common sample (the textbook approach). The stars then differ from the risk/return table whenever the assets have different histories.
   - For 50 target returns between the lowest and highest asset return: minimise `wᵀΣw` subject to `0 ≤ w ≤ 1`, `Σw = 1`, `wᵀμ = target`.
   - Also solved: the global minimum-variance portfolio and the maximum-Sharpe (tangency) portfolio; the Capital Market Line is drawn from `rf` through the tangency portfolio.
   - The **whole curve is kept on purpose**, including the lower branch below the minimum-variance portfolio, to show the full shape of the feasible set. That branch is drawn in grey and flagged `Efficient = False`; only the upper branch is efficient in the strict sense.
9. **CAPM** (`capm_analysis.py`)
   - Market portfolio: the Total Index **CWI** (`market_index` in `Main.py`).
   - For every asset, ordinary least squares on excess returns: `rᵢ,ₜ − rfₜ = αᵢ + βᵢ (r_m,ₜ − rfₜ) + εᵢ,ₜ`, using only the periods where the asset, the market and RF all have a return. All columns of that asset use the same periods.
   - **Cross-sectional SML regression**: across all stocks (indices and USD excluded), `Excess Returnᵢ = γ₀ + γ₁ βᵢ`. CAPM predicts `γ₀ = 0` and `γ₁ = market risk premium`; both are tested with t-tests. This is a simple check **consistent with the SML, not a complete test of CAPM** (see [Known limitations](#known-limitations)).

---

## Configuration you may want to change

| Setting | File / place | Default |
|---|---|---|
| Watchout assets (frontier & cumulative chart) | `Main.py` → `watchout_Assets = [...]` | `USD, CWI, EWI, فولاد, فارس, تاپیکو, …` |
| Market portfolio for CAPM | `Main.py` → `market_index = 'CWI'` | `CWI` (can be `EWI`, `ACT50`, `LCI30`) |
| CAPM minimum observations | `src/calculations/capm_analysis.py` → `MIN_OBS` | `D: 120, W: 26, M: 12` |
| Risk-free series name | `Main.py` → `risk_free_stock = 'RF'` | `RF` (fund «کارا») |
| Minimum prices per asset | `Main.py` → `drop_empty_assets(..., min_obs=1)` | `1` (e.g. use 26 weekly or 6 monthly) |
| Periods per year | `src/calculations/risk_return_analysis.py` → `PERIODS_PER_YEAR` | `D: 240, W: 52, M: 12` |
| Number of frontier points / minimum common periods | `efficient_frontier(..., n_points=50, min_obs=10)` | `50`, `10` |
| Frontier estimation method | `efficient_frontier(..., estimation="full")` | `"full"` (matches the risk/return table) or `"common"` |
| Risk-free fund ticker | `src/extraction/macroEconomy/macroEconomy_Extraction.py` → `stock='کارا'` | `کارا` |

Watchout names must match the column names in `all_Assets_Returns.xlsx` exactly – Persian ticker without the `-ت` suffix, and macro series by their file name (`USD`, `CWI`, `EWI`, `ACT50`, `LCI30`, `RF`). Names that are not found are skipped with a warning.

---

## FAQ / troubleshooting

**The download is very slow or fails with connection errors.**
TSETMC is often slow, rate-limited, or unreachable from outside Iran. Try again later or try with / without a VPN. With pytse-client, if one ticker cannot be found the code automatically retries the tickers one by one and lists the ones that failed.

**Can I run the project without downloading anything?**
Only if `data/raw/` already contains the files from an earlier run. The repository does not ship the raw data.

**`ModuleNotFoundError: No module named 'src'` or `'config'`.**
You are running from the wrong folder. `cd` into the project root and run `python Main.py`.

**`ModuleNotFoundError: No module named 'pandas'` (or plotly, scipy, …).**
The packages are not installed in the active environment. Activate your virtual environment and run the `pip install` command from [Requirements](#requirements).

**`KeyError` with an asset name (e.g. `'usd'` or a ticker).**
A name in `watchout_Assets` does not exist in the data. Check spelling and upper/lower case against the column names in `all_Assets_Returns.xlsx` (the dollar series is saved as `USD`). Only **main-Bourse** stocks are downloaded – Farabourse tickers are not available.

**`KeyError: 'RF' not found`.**
The RF file is missing from `data/raw/macroeconomy_data/` – run the extraction step again.

**"Only N common periods for M assets".**
The correlations on the efficient frontier need periods where all selected assets have data. One asset with a short history (recent listing, long halt) shrinks the common sample. Remove that asset, choose a longer window, or use a higher frequency.

**Can I enter dates in the Jalali (Shamsi) calendar?**
No, the menu takes Gregorian dates. For example 1404/01/01 = 2025-03-21.

**Which frequency should I choose?**
**Weekly.** Daily TSE returns are distorted by price limits (دامنه نوسان) and halts, and the USD series trades on more days than the stock market, which makes daily annualisation less accurate. Monthly gives very few observations unless you use several years.

**Why does the efficient frontier include portfolios below the minimum-risk point?**
On purpose, to show the complete curve. They are drawn in grey and marked `Efficient = False`: for the same risk you can get a higher return on the upper branch.

**Why is `Return` different from `Total Return`?**
`Return` is the annualised average return per year (used for Sharpe and the frontier). `Total Return` is what you earned over the whole window. Over a 3-year window, for example, a stock can show `Return` = 67 % a year and `Total Return` = 460 %.

**Are the returns on the efficient frontier the same as in the Risk vs Return chart?**
Yes (default `estimation="full"`): each asset's return and risk are identical in both charts. Only the correlations come from the periods common to all selected assets. If you switch to `estimation="common"`, all inputs come from the common periods and the numbers will differ from the table. The Sharpe ratios are identical too, because both use the same annualised risk-free rate.

**What does beta tell me?**
Beta measures how strongly an asset moves with the market. The market itself always has β = 1 by definition (it is shown as the green diamond on the SML chart).

**The fitted SML is much flatter than the theoretical one. Is the code wrong?**
Not necessarily. A flat fitted line is a common empirical finding, but part of it can come from the method itself: betas are estimated with error, which pulls the fitted slope towards zero and the intercept upwards. Look at the p-values for `H0: g0 = 0` and `H0: g1 = market premium` in the **SML regression** sheet, and prefer a window of several years.

**Does this project test whether CAPM holds?**
Only in a simple way. The cross-sectional regression is consistent with the SML, but it is not a complete CAPM test: beta estimation error and the correlation between stock returns are not corrected, and the market premium and risk-free rate are themselves estimates. Proper tests (GRS test on beta-sorted portfolios, Fama–MacBeth regressions) are on the roadmap.

**Why are almost no alphas significant?**
Alpha is estimated with a large standard error unless you have many years of data. A non-significant alpha means the data cannot distinguish the asset's performance from what CAPM predicts – not that alpha is exactly zero.

**Some assets disappeared from the results.**
Assets with fewer than `min_obs` prices in the window are dropped; the console prints which ones.

**Persian file names look broken / Excel shows garbled text.**
CSV files are saved as UTF-8 with BOM (`utf-8-sig`), which Excel reads correctly. In other tools choose UTF-8 encoding.

**Charts do not open.**
Charts are opened with your default web browser. On a server without a browser, remove the `fig.show()` calls and save the figures with `fig.write_html(...)` instead.

**Can I add other assets (gold, coins, funds) that are not in the stock list?**
Yes: put a CSV with at least `date` and `close` columns into `data/raw/macroeconomy_data/`. It appears automatically as a series (and as a base option).

---

## Known limitations

- CAPM uses CWI as the market portfolio, which is only a proxy of the true market (Roll's critique), and betas are estimated over the whole window (no rolling betas).
- The SML regression does not correct for beta estimation error or for correlation between stock returns, so it is not a complete test of CAPM.
- **Risk-free data covers only about the last 5 years.**
- A return that spans a long trading halt is booked in a single period, which inflates volatility.
- Only the **current** list of main-Bourse stocks is used, so delisted companies are missing (survivorship bias).
- Results are nominal; no inflation adjustment other than the optional USD base.
- Daily annualisation uses a fixed 240 periods per year, although the USD series trades on more days than the stock market.

## Roadmap

- [x] CAPM module: beta & Jensen's alpha per stock (OLS on excess returns vs CWI), Security Market Line chart, Treynor ratio
- [ ] Formal CAPM tests: GRS test on beta-sorted portfolios, Fama–MacBeth regressions
- [ ] Rolling betas
- [ ] Shrinkage covariance (Ledoit-Wolf)
- [ ] Handling of trading halts in risk statistics
- [ ] Config file / command-line arguments instead of the interactive menu
- [ ] Small sample dataset and tests

## Disclaimer

This project is for education and research. It is **not investment advice**. Data comes from public sources and may contain errors.
