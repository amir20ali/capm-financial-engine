import finpy_tse as fpy
import pandas as pd

def get_stock_list(path):

    DF1 = fpy.Build_Market_StockList(bourse=True,
                                    farabourse=False,
                                    payeh=False,
                                    detailed_list=False,
                                    show_progress=False,
                                    save_excel=False,
                                    save_csv=False,
                                    save_path=path)

    Tickers = DF1.index

    pd.Series(Tickers, name="ticker").to_csv(path / "stock_list.csv", index=False, header=False, encoding="utf-8-sig")

    return Tickers

