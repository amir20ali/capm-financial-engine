import finpy_tse as fpy
from pathlib import Path

path = str(Path.cwd())

def get_stock_list():

    DF1 = fpy.Build_Market_StockList(bourse=True,
                                    farabourse=False,
                                    payeh=False,
                                    detailed_list=False,
                                    show_progress=False,
                                    save_excel=False,
                                    save_csv=False,
                                    save_path=path)

    Tickers = DF1.index

    return Tickers
