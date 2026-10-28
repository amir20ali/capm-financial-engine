from pathlib import Path

import pytse_client as tse

ADJ_SUFFIX = "-ت"   # pytse-client adds this to the file name when adjust=True


def pytse_Client_Extraction(stocks, save_path):
    """
    Download adjusted daily prices with pytse-client and save them as
    <save_path>/<ticker>.csv  (same naming as the finpy-tse source).
    """
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)

    # 1) Fast path: download everything in one call (10 parallel threads).
    #    pytse-client stops with an Exception if ONE symbol is unknown,
    #    so on failure fall back to downloading the symbols one by one.
    try:
        tse.download(symbols=list(stocks), write_to_csv=True, include_jdate=True,
                     adjust=True, base_path=str(save_path))
    except Exception as e:
        print(f"⚠️  Batch download failed ({e}). Downloading one by one ...")
        failed = []
        for stock in stocks:
            try:
                tse.download(symbols=stock, write_to_csv=True, include_jdate=True,
                             adjust=True, base_path=str(save_path))
            except Exception as ex:
                failed.append(stock)
                print(f"   ❌ {stock}: {ex}")
        if failed:
            print(f"⚠️  {len(failed)} symbols could not be downloaded: {failed}")

    # 2) Rename "<ticker>-ت.csv"  ->  "<ticker>.csv"
    renamed = 0
    for file in save_path.glob(f"*{ADJ_SUFFIX}.csv"):
        ticker = file.name[: -len(f"{ADJ_SUFFIX}.csv")]
        file.replace(save_path / f"{ticker}.csv")   # overwrites an older file
        renamed += 1
    print(f"✅ pytse-client data saved to {save_path} ({renamed} files)")
