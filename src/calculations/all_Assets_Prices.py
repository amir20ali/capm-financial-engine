import pandas as pd
from datetime import timedelta


def period_prices_cal(stock_name, stock_data, start_date, end_date, frequency):
        # ---------- Filter & start date ----------
        first_available_date = stock_data["date"].min()

     
        if first_available_date <= start_date:
            stock_data = stock_data[
                (stock_data["date"] >= start_date) &
                (stock_data["date"] <= end_date)
            ].copy()
        else:
            stock_data = stock_data[
                (stock_data["date"] >= first_available_date + timedelta(days=60)) &
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
            .last()
            .to_frame(stock_name)
        )
    
        return period_prices, period_col




def arrange_Assets_Prices(stock_list ,data_source, 
                            start_date, end_date, frequency, 
                            meconomy_Base, meconomy_path, meconomy_List,
                            PROCESSED_DIR ):

    start_date = pd.to_datetime(start_date)
    end_date   = pd.to_datetime(end_date)

    stock_names = pd.read_csv(stock_list / "stock_list.csv")
    stock_names = stock_names['ticker'].tolist()
 
    all_Assets_Prices = pd.DataFrame()
    #all_prices_list = []

    for stock_name in stock_names:

        # ---------- Load data ----------
        stock_path = data_source / f"{stock_name}.csv"
        stock_data = pd.read_csv(stock_path)
        
        stock_data["date"] = pd.to_datetime(stock_data["date"])

        [period_prices, period_col] = period_prices_cal(stock_name, stock_data, start_date, end_date, frequency)

        if all_Assets_Prices.empty:
            all_Assets_Prices = period_prices
        else:
            all_Assets_Prices = pd.merge(
                all_Assets_Prices,
                period_prices,
                on=period_col,
                how="outer"
            )

    for Meconomy in meconomy_List[1:]:
        Path = meconomy_path / f"{Meconomy}.csv"
        meconomy_data = pd.read_csv(Path)
        
        meconomy_data["date"] = pd.to_datetime(meconomy_data["date"])
        
        [period_prices, period_col] = period_prices_cal(Meconomy, meconomy_data, start_date, end_date, frequency)

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
    #all_Assets_Prices = all_Assets_Prices.iloc[1:].reset_index(drop=True)

    all_Assets_Prices = all_Assets_Prices.reset_index(drop=False)

    if meconomy_Base == "None" :

        # Save the combined DataFrame to a Excel file
        all_Assets_Prices.to_excel(PROCESSED_DIR / 'all_Assets_Prices.xlsx', index=False, float_format='%.5f')
        print("✅ All assets Prices saved to PROCESSED_DIR")
        return all_Assets_Prices
    
    
    else:

        if meconomy_Base not in all_Assets_Prices.columns:
            raise ValueError(f"{meconomy_Base} not found in columns")

        # تقسیم تمام ستون‌ها به ستون base
        base_series = all_Assets_Prices[meconomy_Base]
        base_series = base_series.replace(0, pd.NA)

        # فقط ستون‌های عددی را تقسیم کن
        numeric_cols = all_Assets_Prices.select_dtypes(include="number").columns

        all_Assets_Prices[numeric_cols] = all_Assets_Prices[numeric_cols].div(base_series, axis=0)

        # اگر نمی‌خواهی ستون base باقی بماند:
        # all_Assets_Prices.drop(columns=[meconomy_Base], inplace=True)

        all_Assets_Prices.to_excel(
            PROCESSED_DIR / 'all_Assets_Prices.xlsx',
            index=False,
            float_format='%.10f'
        )
        print("✅ All assets Prices saved to PROCESSED_DIR")

        return all_Assets_Prices

