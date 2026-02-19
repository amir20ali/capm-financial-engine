import finpy_tse as fpy
from pathlib import Path

def finpy_tse_Extraction(stocks, save_path):

    for stock in stocks:

        DF= fpy.Get_Price_History(
            stock=stock,
            #start_date='1403-01-01',
            #end_date='1404-01-01',
            ignore_date=True,
            adjust_price=True,
            show_weekday=False,
            double_date=True)

        # Move index to column
        DF = DF.reset_index()

        # Rename J-Date and Date
        DF = DF.rename(columns={
            "J-Date": "jdate",
            "Date": "date"
        })

        # Delete unwanted columns
        cols_to_drop = ["Open", "High", "Low", "Close", "Final"]
        DF = DF.drop(columns=[col for col in cols_to_drop if col in DF.columns])

        # Remove "Adj " from adjusted column names
        DF.columns = DF.columns.str.replace("Adj ", "", regex=False)

        # Convert all headers to lowercase
        DF.columns = DF.columns.str.lower()

        print(DF.head())

        DF.to_csv(save_path / f"{stock}.csv", encoding="utf-8-sig")



