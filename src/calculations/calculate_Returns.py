import pandas as pd

def calculate_Returns(all_Assets_Prices, PROCESSED_DIR):

    if all_Assets_Prices.empty:
        empty_result = pd.DataFrame(columns=all_Assets_Prices.columns)
        empty_result.to_excel(
            PROCESSED_DIR / 'all_Assets_Returns.xlsx',
            index=False,
            float_format='%.5f'
        )
        return empty_result

    first_col = all_Assets_Prices.iloc[:-1, 0]

    numeric_prices = all_Assets_Prices.iloc[:, 1:]
    numeric_prices = (
        numeric_prices
        .replace(',', '', regex=True)
        .apply(pd.to_numeric, errors='coerce')
    )

    filled_prices = numeric_prices.ffill()
    returns = filled_prices.shift(-1).div(filled_prices).sub(1)

    next_actual_missing = numeric_prices.shift(-1).isna()
    returns = returns.mask(next_actual_missing)

    result = pd.concat([first_col, returns.iloc[:-1]], axis=1)

    result.to_excel(
        PROCESSED_DIR / 'all_Assets_Returns.xlsx',
        index=False,
        float_format='%.5f'
    )
    print("✅ All assets returns saved to PROCESSED_DIR")

    return result