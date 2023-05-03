import pandas as pd
import os
from dotenv import dotenv_values
import requests
from datetime import datetime

cred = dotenv_values(".env")

class PriceData:

    DATA_DIR = "raw_data/"

    def __init__(self, ticker_list=[], data_type='adjClose',ticker_ref_date=None, start=None, end=None, refresh=False, display=False):

        self.start = start if start is not None else "2000-01-01"
        self.end = end if end is not None else str(datetime.today())[:10]
        self.data_type = data_type
        self.price = None
        self.display = display
        self.con_ref_date = end if ticker_ref_date == None else ticker_ref_date
        
        if ticker_list and ticker_list[0] == "all":
            self.ticker_list = self.get_constituent_by_date()

        if ticker_list and "all" not in ticker_list:
            self.ticker_list = ticker_list
        else:
            self.ticker_list = self.get_full_sp500_ticker_list()

        self.get_return_data()

        if refresh:
            self.pull_stock_price()


    def pull_stock_price(self):

        for ticker in self.ticker_list:

            try:
                print(F"Getting {ticker} Price Data...")
                response = requests.get(F"""https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from=2000-01-01&apikey={self.api_key}""")
                data = response.json()

                df_price = pd.DataFrame(data["historical"])

                df_price = df_price[["date","open","high","low","close","adjClose","volume","vwap"]].set_index("date").sort_index()
                df_price.index = pd.to_datetime(df_price.index, format="%Y-%m-%d")

                df_price.to_csv(self.DATA_DIR + "price/" + ticker +".csv")
            except:
                if self.display:
                    print(F"Unable to Fetch {ticker} Price Data.")
                pass

    def get_full_sp500_ticker_list(self):

        import itertools
        df_data  = pd.read_csv("raw_data/historical_constituents/sp500-historical-constituents.csv",index_col=0)

        df_data.head()

        df_data.index =  pd.to_datetime(df_data.index,format="%Y-%m-%d")


        ticker_list = [row.split(",") for row in list(df_data["tickers"])]

        return list(set(itertools.chain.from_iterable(ticker_list)))
    
    def get_constituent_by_date(self):

        df_con = pd.read_csv("raw_data/historical_constituents/sp500-historical-constituents.csv",index_col=0)
        df_con.index = pd.to_datetime(df_con.index, format="%Y-%m-%d")

        return df_con.loc[df_con.loc[df_con.index<self.con_ref_date].index.max()].values[0].split(",")
    
    def get_price_data(self):

        # print("Get Price Data from Local Folder")

        list_of_df = []
        for ticker in self.ticker_list:
            try:
                df_price = pd.read_csv(F"{self.DATA_DIR}price/{ticker}.csv", index_col=0)

                df_price =  df_price.rename(columns={self.data_type:ticker})[ticker]

                df_price.index = pd.to_datetime(df_price.index, format="%Y-%m-%d")

                list_of_df.append(df_price)
            except:
                if self.display:
                    print(F"{ticker} price data not available")

        df_combined = pd.concat(list_of_df,axis=1)

        df_combined =  df_combined.loc[(df_combined.index>=self.start)&(df_combined.index<=self.end)]

        df_combined = df_combined.dropna(axis=1)

        self.price  = df_combined

    def get_return_data(self,interval="m"):

        if self.price is  None:
            self.get_price_data()

        # print(F"Generated {'Monthly' if interval=='m' else 'Daily'} Return.")

        df_price = self.price.copy()

        if interval == "m":
            df_ret = df_price.resample("m").last().pct_change().dropna()
            df_ret.index = df_ret.index.strftime('%Y-%m')
            self.asset_return = df_ret
        elif interval == 'd':
            self.asset_return = df_price.pct_change().dropna()
    
