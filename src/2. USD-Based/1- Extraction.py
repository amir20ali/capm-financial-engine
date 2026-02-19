import finpy_tse as fpy
from pathlib import Path


DF = fpy.Get_USD_RIAL(
    ignore_date=True,
    show_weekday=False,
    double_date=True)

# Move index to column
DF = DF.reset_index()

# Rename J-Date and Date
DF = DF.rename(columns={
    "J-Date": "jdate",
    "Date": "date"
})

# Convert all headers to lowercase
DF.columns = DF.columns.str.lower()

save_path = (
    Path.cwd()
    / "2. USD-Based/USD Data"
    / "USDRate.csv"
)
DF.to_csv(save_path,index=False, encoding="utf-8-sig")


