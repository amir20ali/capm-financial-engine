import pandas as pd
from datetime import timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# -------- Inputs ---------
# =========================

file_path = Path(r"D:\Resources 2024-16-07\Business\Finance\T-Portfolio\CAPM Project\1. Extraction & Validation\1. pytse_client Library\Stock Data")
analysis_years = 5
frequency = "D"   
analysis_start_date = pd.Timestamp("2021-01-01")

stock_names = ["فولاد", "فملی", "پارسان", "تاپیکو", "فارس", "بوعلی"]

# =========================  
# ---- Pre-Calculations ---
# =========================

end_date = analysis_start_date + pd.DateOffset(years=analysis_years)

# Container for all stock returns
all_stocks_returns = pd.DataFrame()

# =========================
# --------- Loop ----------
# =========================

for stock_name in stock_names:

    # ---------- Load data ----------
    stock_path = file_path / f"{stock_name}-ت.csv"
    stock_data = pd.read_csv(stock_path)

    stock_data["date"] = pd.to_datetime(stock_data["date"])

    # ---------- Determine start date ----------
    first_available_date = stock_data["date"].min()

    if first_available_date <= analysis_start_date:
        start_date = analysis_start_date
    else:
        start_date = first_available_date + timedelta(days=60)    # 60 days after the first recorded date

    # ---------- Filter ----------
    stock_data = stock_data[
        (stock_data["date"] >= start_date) &
        (stock_data["date"] <= end_date)
    ].copy()

    stock_data.set_index("date", inplace=True)

    # =========================
    # ---- Period Handling ----
    # =========================

    if frequency == "D":
        period = "D"
        period_col = "day"
    elif frequency == "W":
        period = "W"
        period_col = "week"
    elif frequency == "M":
        period = "M"
        period_col = "month"
    else:
        raise ValueError("frequency must be one of: D, W, M")

    stock_data[period_col] = stock_data.index.to_period(period)

    # =========================
    # ---- Return Calculation -
    # =========================

    period_prices = (
        stock_data
        .groupby(period_col)["close"]
        .first()
        .to_frame("price")
    )

    period_prices["next_price"] = period_prices["price"].shift(-1)

    period_prices[stock_name] = (
        (period_prices["next_price"] - period_prices["price"])
        / period_prices["price"]
        * 100
    ).shift(1)

    stock_returns = period_prices[[stock_name]].reset_index()

    # =========================
    # ---- Merge Results ------
    # =========================

    if all_stocks_returns.empty:
        all_stocks_returns = stock_returns
    else:
        all_stocks_returns = pd.merge(
            all_stocks_returns,
            stock_returns,
            on=period_col,
            how="outer"
        )

# =========================
# -------- Result ---------
# =========================

#Drop the first row
all_stocks_returns = all_stocks_returns.iloc[1:].reset_index(drop=True)

# Save the combined DataFrame to a Excel file
output_file_path = 'all_stocks_returns.xlsx'
all_stocks_returns.to_excel(output_file_path, index=False, float_format='%.5f')


# =========================
# -------- Plot ---------
# =========================

# Loop through each stock name and plot its return distribution separately
for stock_name in stock_names:
    plt.figure()  # Create a new figure for each stock
    
    # Plot the histogram of weekly returns
    sns.histplot(all_stocks_returns[stock_name])
    
    # Calculate mean and standard deviation
    mean = all_stocks_returns[stock_name].mean()
    std_dev = all_stocks_returns[stock_name].std()
    
    # Display mean and standard deviation on the plot
    plt.axvline(mean, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean:.2f}')
    plt.axvline(mean - std_dev, color='green', linestyle='dashed', linewidth=1, label=f'Std Dev: {std_dev:.2f}')
    plt.axvline(mean + std_dev, color='green', linestyle='dashed', linewidth=1)
    
    plt.xlabel('Returns (%)')
    plt.ylabel('Frequency')
    plt.title(f'Returns Distribution of {stock_name}')
    plt.legend()
    plt.show()
