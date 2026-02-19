# config.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

finpy_stock_data = RAW_DIR / "finpy_stock_data"
Pytse_stock_data = RAW_DIR / "Pytse_stock_data"

# ایجاد پوشه‌ها اگر وجود ندارند
for path in [DATA_DIR, RAW_DIR, PROCESSED_DIR, finpy_stock_data,Pytse_stock_data]:
    path.mkdir(parents=True, exist_ok=True)
