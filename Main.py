from config import Pytse_stock_data,finpy_stock_data, meconomy_path,PROCESSED_DIR, stock_list
from src.stock_list.get_stock_list import get_stock_list
from src.extraction.finpy_tse.finpy_tse_Extraction import finpy_tse_Extraction
from src.extraction.pytse_client.pytse_Client_Extraction import pytse_Client_Extraction
from src.extraction.macroEconomy.macroEconomy_Extraction import get_macroeconomy_data
from src.calculations.all_Assets_Prices import arrange_Assets_Prices
from src.calculations.calculate_Returns import calculate_Returns
from src.calculations.investment_Result import investment_Result
from src.calculations.risk_return_analysis import risk_return_analysis
from src.calculations.efficient_frontier_calculation import efficient_frontier

from datetime import date

#from src.macro_data import get_dollar_price, get_market_index
#from src.inputs import CAPMInputs
#from src.capm import compute_returns

def run_pipeline():    
    
    Extraction_choice = select_from_menu(
        "Do you want to extract the data now?",
        ["Yes","No"]
    )
    
    data_sources = [
    "Pytse Client Library",
    "Finpy TSE Library",
    ]

    ds_choice = select_from_menu(
        "Select data source",
        data_sources
    )

    if Extraction_choice == 0:

        get_macroeconomy_data(meconomy_path)
        stocks = get_stock_list(stock_list)

        if ds_choice == 0:
            data_source = Pytse_stock_data
            pytse_Client_Extraction(stocks.tolist() , Pytse_stock_data)
        else: 
            data_source = finpy_stock_data
            finpy_tse_Extraction(stocks , finpy_stock_data)
    else: 

         if ds_choice == 0:
            data_source = Pytse_stock_data
         else: 
            data_source = finpy_stock_data

    #Reading Macroeconomy List
    meconomy_List = ["None"] + [file.stem for file in meconomy_path.glob("*.csv")]

    # ==============================
    # Q2: Start Date (Guided)
    # ==============================

    print("\nSelect analysis start date")

    year = select_integer("Year", 1990, date.today().year)
    month = select_integer("Month", 1, 12)
    day = select_integer("Day", 1, 31)

    while True:
        try:
            start_date = date(year, month, day)
            break
        except ValueError:
            print("❌ Invalid date combination. Please re-enter.")
            day = select_integer("Day", 1, 31)

    # ==============================
    # Q3: end Date (Guided)
    # ==============================

    print("\nSelect analysis end date")

    year = select_integer("Year", 1990, date.today().year)
    month = select_integer("Month", 1, 12)
    day = select_integer("Day", 1, 31)

    while True:
        try:
            end_date = date(year, month, day)
            break
        except ValueError:
            print("❌ Invalid date combination. Please re-enter.")
            day = select_integer("Day", 1, 31)



    # ==============================
    # Q4: Frequency
    # ==============================

    frequencies = ["Daily", "Weekly", "Monthly"]
    freq_index = select_from_menu(
        "Select analysis frequency",
        frequencies
    )

    frequency_map = {
        0: "D",
        1: "W",
        2: "M"
    }

    frequency = frequency_map[freq_index]

    # ==============================
    # Q5: Base
    # ==============================

    answers = meconomy_List

    ds_choice = select_from_menu(
        "Which Macro Economy data should be the base?",
        answers
    )

    meconomy_Base = meconomy_List[ds_choice]


    # ==============================
    # Summary
    # ==============================

    print("\n✅ Configuration Locked In")
    print("=" * 30)
    print(f"Data Source      : {data_source}")
    print(f"Start Date     : {start_date}")
    print(f"end Date     : {end_date}")
    print(f"Frequency Code : {frequency}")
    print(f"Price Base     : {meconomy_Base}")

    all_Assets_Prices = arrange_Assets_Prices(stock_list ,data_source, 
                                              start_date, end_date, frequency, 
                                              meconomy_Base, meconomy_path, meconomy_List,
                                              PROCESSED_DIR)
    
    all_Asset_Returns = calculate_Returns(all_Assets_Prices, PROCESSED_DIR)

    risk_free_stock = 'RF'

    risk_return_data = risk_return_analysis(all_Asset_Returns, risk_free_stock, PROCESSED_DIR)


    #covariance & Correlation matrix calculation and saving
    numeric_returns = all_Asset_Returns.select_dtypes(include=['number'])
    if numeric_returns.empty or numeric_returns.shape[1] < 1:
        print("❌ No numeric return columns found; covariance not computed.")
    else:
        cov_matrix = numeric_returns.cov()
        cov_matrix.to_excel(
            PROCESSED_DIR / 'cov_matrix.xlsx',
            index=True,
            float_format='%.5f'
        )
        print("✅ Covariance matrix saved to PROCESSED_DIR")

        corr_matrix = numeric_returns.corr()
        corr_matrix.to_excel(
            PROCESSED_DIR / 'corr_matrix.xlsx',
            index=True,
            float_format='%.5f'
        )
        print("✅ Correlation matrix saved to PROCESSED_DIR")

    #more Correlation analysis
    # ...

    watchout_Assets=[
        'usd',
        'CWI',
        'EWI',
        'فولاد',
        'فارس',
        'تاپیکو',
        'شستا',
        'دعبید',
        'شپدیس',
        'همراه',
        'حفارس',
        'شکربن',
        'کچاد',
        'سصفها',
    ]

    #add share
    investment_Result(watchout_Assets, all_Asset_Returns)

    frontier_returns, frontier_risks, fig = efficient_frontier(watchout_Assets, risk_return_data, risk_free_stock, cov_matrix, PROCESSED_DIR)



# ==============================
# Calculating portfolio performance
# ==============================

# Function to calculate portfolio return and risk (standard deviation)
'''
def portfolio_performance(weights, expected_returns, cov_matrix):
    port_return = np.sum(weights * expected_returns)
    port_std_dev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    return port_return, port_std_dev

'''

# ==============================
# Core Selection Utilities
# ==============================

def select_from_menu(title, options):
        """
        options: list of display strings
        returns: index (int)
        """
        print(f"\n{title}")
        print("-" * len(title))

        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")

        while True:
            choice = input("Select an option number: ")
            if choice.isdigit():
                choice = int(choice)
                if 1 <= choice <= len(options):
                    return choice - 1
            print("❌ Invalid selection. Please choose a valid number.")


def select_integer(prompt, min_val, max_val):
        while True:
            value = input(f"{prompt} ({min_val}–{max_val}): ")
            if value.isdigit():
                value = int(value)
                if min_val <= value <= max_val:
                    return value
            print("❌ Invalid input.")
    
   

if __name__ == "__main__":
    run_pipeline()
