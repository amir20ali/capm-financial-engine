import pytse_client as tse

def pytse_Client_Extraction(stocks, save_path):
    #tadil shode
    tse.download(symbols=stocks, write_to_csv=True, include_jdate=True,
                  adjust=True, base_path= save_path)



