import pandas as pd
from price_data import PriceData
from datetime import datetime, timedelta
import numpy as np

class Exchange:

    SPREAD = 0.005
    EXCHANGE_FEE = 0.005
    def __init__(self, orders, trade_date):

        print("Sent Trade to Exchange....")
        
        self.orders = orders.copy()
        self.trade_date = trade_date

        end_date = str(datetime.strptime(trade_date, '%Y-%m-%d') + timedelta(days=10))[:10]



        self.price = PriceData(list(orders["ticker"].unique()), start=trade_date, end=end_date, refresh=False).price

        

    def send_to_exchange(self):

        price_dict = self.price.iloc[0].to_dict()
        self.orders['price'] = self.orders["ticker"].map(price_dict)

        # add spread into price

        self.orders.loc[self.orders['type']=='buy',"executed_price"] = self.orders["price"] * (1+self.SPREAD)
        self.orders.loc[self.orders['type']=='sell',"executed_price"] = self.orders["price"] * (1-self.SPREAD)

        # round the trades, sell = ceil cause negative number, and buy = floor
        self.orders.loc[self.orders["type"]=="buy","number_of_shares"] = np.floor(self.orders["amount"] / self.orders["price"])
        self.orders.loc[self.orders["type"]=="sell","number_of_shares"] = np.ceil(self.orders["amount"] / self.orders["price"])
        
        self.orders["executed_total"] = self.orders["executed_price"] * self.orders["number_of_shares"]

        self.orders = self.orders.rename(columns={"date":"trade_date"})

        # calculate exchange fee
        # some ticker might be short and long in one trade, so need to net out all the positions
        net_orders = self.orders[["ticker","executed_total"]].groupby("ticker",as_index=False).sum()

        exchange_fee = sum(net_orders['executed_total'].abs()) * self.EXCHANGE_FEE

        return self.orders, exchange_fee