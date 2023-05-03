import pandas as pd
from price_data import PriceData
from datetime import datetime, timedelta
import numpy as np

class Exchange:

    SPREAD = 0.005
    EXCHANGE_FEE = 0.005
    def __init__(self, ):

        print("Sent Trade to Exchange....")
        

    def send_buy_orders(self, orders, trade_date):

        #
        self.orders = orders.copy()
        self.trade_date = trade_date

        end_date = str(datetime.strptime(trade_date, '%Y-%m-%d') + timedelta(days=10))[:10]

        self.price = PriceData(list(orders["ticker"].unique()), start=trade_date, end=end_date, refresh=False).price
        self.price = self.price.loc[self.price.index!=trade_date]

        price_dict = self.price.iloc[0].to_dict()
        self.orders['price'] = self.orders["ticker"].map(price_dict)

        self.orders = self.orders.loc[~self.orders["price"].isna()]

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

        cash_spent = sum(self.orders['executed_total'])


        return self.orders, cash_spent, exchange_fee
    
    def send_sell_orders(self, sell_orders, trade_date):

        self.sell_orders = sell_orders

        end_date = str(datetime.strptime(trade_date, '%Y-%m-%d') + timedelta(days=10))[:10]

        self.price = PriceData(list(sell_orders["ticker"].unique()), start=trade_date, end=end_date, refresh=False).price
        self.price = self.price.loc[self.price.index!=trade_date]

        price_dict = self.price.iloc[0].to_dict()
        self.sell_orders['price'] = self.sell_orders["ticker"].map(price_dict)
        self.sell_orders = self.sell_orders.loc[~self.sell_orders["price"].isna()]

        self.sell_orders.loc[self.sell_orders['order']>0,"sold_price"] = self.sell_orders["price"] * (1+self.SPREAD)
        self.sell_orders.loc[self.sell_orders['order']<0,"sold_price"] = self.sell_orders["price"] * (1-self.SPREAD)

        self.sell_orders["sell_total"] = self.sell_orders["order"] * self.sell_orders["price"]

        net_orders = self.sell_orders[["ticker","sell_total"]].groupby("ticker",as_index=False).sum()
        exchange_fee = sum(net_orders['sell_total'].abs()) * self.EXCHANGE_FEE

        cash_spent = sum(self.sell_orders["sell_total"])

        return self.sell_orders, cash_spent, exchange_fee

        
