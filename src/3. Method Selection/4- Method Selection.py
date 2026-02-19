from pathlib import Path
from datetime import date


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


# ==============================
# Q1: Data Source
# ==============================

data_sources = [
    "Pytse Client Library",
    "Finpy TSE Library",
    "Local / Custom Folder"
]

ds_choice = select_from_menu(
    "Select data source",
    data_sources
)

if ds_choice == 0:
    data_source = "Pytse Client Library"
elif ds_choice == 1:
    data_source = "Finpy TSE Library"
else:
    print("\nEnter folder path step-by-step:")
    folder_name = input("Folder name (relative to project): ").strip()
    data_source = Path.cwd() / folder_name

data_source = str(data_source)

# ==============================
# Q2: Analysis Period
# ==============================

period_options = [f"{i * 0.5} Years" for i in range(1, 21)]
period_index = select_from_menu(
    "Select analysis period",
    period_options
)

analysis_years = (period_index + 1) * 0.5


# ==============================
# Q3: Frequency
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
# Q4: Start Date (Guided)
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
# Final Summary
# ==============================

print("\n✅ Configuration Locked In")
print("=" * 30)
print(f"Data Source      : {data_source}")
print(f"Period (Years) : {analysis_years}")
print(f"Frequency Code : {frequency}")
print(f"Start Date     : {start_date}")
print(f"USD Base     : {USD_Base}")