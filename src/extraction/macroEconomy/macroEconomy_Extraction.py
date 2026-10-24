import finpy_tse as fpy

def get_macroeconomy_data(save_path):
    
    
    USD_DF = fpy.Get_USD_RIAL(
        ignore_date=True,
        show_weekday=False,
        double_date=True)
    

    CWI_DF= fpy.Get_CWI_History(
        ignore_date=True,
        just_adj_close=False,
        show_weekday=False,
        double_date=True)

    EWI_DF = fpy.Get_EWI_History(
        ignore_date=True,
        just_adj_close=False,
        show_weekday=False,
        double_date=True)
    

    ACT50_DF = fpy.Get_ACT50_History(
    ignore_date=True,
    just_adj_close=False,
    show_weekday=False,
    double_date=True)

    LCI30_DF = fpy.Get_LCI30_History(
    ignore_date=True,
    just_adj_close=False,
    show_weekday=False,
    double_date=True)

    RF_DF = fpy.Get_Price_History(
    stock='کارا',
    ignore_date=True,
    adjust_price=False,
    show_weekday=False,
    double_date=True)

    dataframes = {
    "USD": USD_DF,
    "CWI": CWI_DF,
    "LCI30": LCI30_DF,
    "ACT50": ACT50_DF,
    "EWI": EWI_DF,
    "RF" : RF_DF
    }


    for name, DF in dataframes.items():
        # Move index to column
        DF = DF.reset_index()

        # Rename J-Date and Date
        DF = DF.rename(columns={
            "J-Date": "jdate",
            "Date": "date"
        })

        # Convert all headers to lowercase
        DF.columns = DF.columns.str.lower()

        DF.to_csv(save_path/ f"{name}.csv",index=False, encoding="utf-8-sig")


