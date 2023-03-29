import pandas as pd
import os
from dotenv import dotenv_values
import requests


cred = dotenv_values(".env")

class PriceData:

    def __init__(self, ticker_list=[], refresh=False):

        self.api_key =  cred["FMP_API_KEY"]
        self.ticker_list = ['AAPL',"MSFT"]

        self.sp_con_url = "https://financialmodelingprep.com/api/v3/historical/sp500_constituent?apikey={}"

        if refresh:
            self.get_stock_price()



    def get_stock_price(self):

        list_of_df = []
        for ticker in self.ticker_list:
            response = requests.get(F"""https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={self.api_key}""")
            data = response.json()

            self.json = data

            df_price = pd.DataFrame(data["historical"])

            df_price = df_price[["date","open","high","low","close","adjClose","volume","vwap"]].set_index("date").sort_index()
            df_price.index = pd.to_datetime(df_price.index, format="%Y-%m-%d")

            df_price["symbol"] = ticker 

            list_of_df.append(df_price)


        self.df = pd.concat(list_of_df, axis=0)