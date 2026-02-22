import pandas as pd
from datetime import timedelta


def arrange_Assets_Prices(stock_list ,data_source, start_date, end_date, frequency, USD_Base, PROCESSED_DIR):

    stock_names = pd.read_csv(stock_list / "stock_list.csv")

    for stock_name in stock_names:

        # ---------- Load data ----------
        stock_path = data_source / f"{stock_name}-ت.csv"
        stock_data = pd.read_csv(stock_path)

        stock_data["date"] = pd.to_datetime(stock_data["date"])

        # ---------- Determine start date ----------
        first_available_date = stock_data["date"].min()

        if first_available_date <= start_date:
            start_date = start_date
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


        if all_Assets_Prices.empty:
            all_Assets_Prices = period_prices
        else:
            all_Assets_Prices = pd.merge(
                all_Assets_Prices,
                period_prices,
                on=period_col,
                how="outer"
            )

    # =========================
    # -------- Result ---------
    # =========================

    #Drop the first row
    all_Assets_Prices = all_Assets_Prices.iloc[1:].reset_index(drop=True)

    # Save the combined DataFrame to a Excel file
    all_Assets_Prices.to_excel(PROCESSED_DIR / 'all_Assets_Prices.xlsx', index=False, float_format='%.5f')