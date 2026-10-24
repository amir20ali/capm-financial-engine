import finpy_tse as fpy

T = fpy.Get_Price_History(
    stock='کارا',
    start_date='1403-01-01',
    end_date='1404-01-01',
    ignore_date=False,
    adjust_price=False,
    show_weekday=False,
    double_date=False)

print(T)