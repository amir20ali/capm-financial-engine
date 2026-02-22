from config import Pytse_stock_data,finpy_stock_data, macroeconomy_data,PROCESSED_DIR, stock_list
from src.stock_list.get_stock_list import get_stock_list
from src.extraction.finpy_tse.finpy_tse_Extraction import finpy_tse_Extraction
from src.extraction.pytse_client.pytse_Client_Extraction import pytse_Client_Extraction
from src.extraction.macroEconomy.macroEconomy_Extraction import get_macroeconomy_data
from src.calculations.all_Assets_Prices import arrange_Assets_Prices

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

        get_macroeconomy_data(macroeconomy_data)
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
    # Q5: USD Base
    # ==============================

    answers = [
        "Yes",
        "NO"
    ]

    ds_choice = select_from_menu(
        "Prcie based on USD?",
        answers
    )

    if ds_choice == 0:
        USD_Base = True
    else: USD_Base = False


    # ==============================
    # Summary
    # ==============================

    print("\n✅ Configuration Locked In")
    print("=" * 30)
    print(f"Data Source      : {data_source}")
    print(f"Start Date     : {start_date}")
    print(f"end Date     : {end_date}")
    print(f"Frequency Code : {frequency}")
    print(f"USD Base     : {USD_Base}")

    arrange_Assets_Prices(stock_list ,data_source, start_date, end_date, frequency, USD_Base, PROCESSED_DIR)



    '''
    fetch_and_save_prices(stocks, RAW_DIR / "stock_prices")

    dollar = get_dollar_price()
    market = get_market_index()

    inputs = CAPMInputs(
        start_date="2019-01-01",
        end_date="2024-01-01",
        risk_free_rate=0.25,
        frequency="monthly",
        market_col="close"
    )

    # load prices → compute returns → CAPM
    ...

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
