import pandas as pd
from exchange import Exchange

class PMA:

    SHORT_FEE = 0.05 / 250
    CASH_INTEREST = 0.03 / 250

    def __init__(self, initial_amount, allocation_per_trade=50000):

        self.allocation_per_trade = allocation_per_trade

        self.allocation = pd.DataFrame(columns=['trade_id','ticker','number_of_shares','executed_price','executed_total','trade_date',"latest_price","P/L"])

        self.aum = initial_amount
        self.cash_amount = initial_amount
        self.total_long_position = 0
        self.total_short_position = 0

        self.aum_history = pd.DataFrame(columns=["date","aum"])
        self.trade_history = pd.DataFrame(columns=["trade_id","ticker","amount","trade_date","P/L"])

        self.stop_loss = pd.DataFrame(columns=["trade_id","long","short","levels"])
        self.active_pairs = []


        pass

    def add_to_pma(self, orders, info, trade_date):
        
        if not self.allocation.empty:
            
            orders["amount"] = self.cash_amount / sum(orders['unit_amount'].abs()) * orders["unit_amount"]

            display(orders.head())

            orders = self.calculate_per_buy_order(orders, info)
        
        
            print(sum(orders["amount"].abs()))
        
        else:
            
            keep_list = []

            orders = self.calculate_per_buy_order(orders, info)
            
            # self.active_pairs =  self.active_pairs + list(info["long"] + "-" + info["short"])

            # send the trades to exchange for processing
            orders_summary, exchange_fee = Exchange(orders, trade_date).send_to_exchange()

            orders_summary = orders_summary[["trade_id","ticker","number_of_shares","executed_price","trade_date","executed_total"]]
            orders_summary["P/L"] = 0 # new trades don't have any P/L
            orders_summary['latest_price'] = orders_summary["executed_price"] # the latest is the executed_price for all new trades

            self.allocation = pd.concat([self.allocation,orders_summary],axis=0)

            # to track which pairs currently in the portfolio
            pairs_list = list(info["long"] + "-" + info["short"])

            self.active_pairs = self.active_pairs + pairs_list

        # record net spend to cash
        self.cash_amount = self.cash_amount - orders_summary["executed_total"].sum()


        # record the exchange fees
        self.cash_amount = self.cash_amount - exchange_fee
        self.aum = self.aum - exchange_fee


        display(orders_summary)
        display(exchange_fee)



    def calculate_per_buy_order(self, orders, info):

        # allocate money to every pairs
        orders["amount"] = self.cash_amount / sum(orders['unit_amount'].abs()) * orders["unit_amount"]

        # cap the maximum amount of allocation to each pairs
        df_abs = orders.copy()
        df_abs["amount"] = df_abs["amount"].abs()

        grouped_orders = df_abs[["trade_id","amount"]].groupby("trade_id",as_index=False).sum()
        orders_reduce = grouped_orders.loc[grouped_orders["amount"]>self.allocation_per_trade*2]

        orders_reduce["excessed_amount"] = orders_reduce['amount'] - self.allocation_per_trade * 2
        orders_reduce["reduce_ratio"] = orders_reduce["excessed_amount"] / orders_reduce["amount"]

        # reduce the excess amount from the orders
        for num in range(len(orders_reduce)):

            orders.loc[orders["trade_id"]==orders_reduce["trade_id"].iloc[num],"amount"] = orders["amount"] * (1-orders_reduce["reduce_ratio"].iloc[num])

        orders.loc[orders["amount"]>0, "type"] = "buy"
        orders.loc[orders["amount"]<0, "type"] = "sell"

        return orders


    def run_pma(self):

        grouped_allocation = self.allocation[["ticker","executed_total"]].groupby("ticker",as_index=False).sum()
        self.total_long_position = grouped_allocation.loc[grouped_allocation["executed_total"]>0]["executed_total"].sum()
        self.total_short_position = grouped_allocation.loc[grouped_allocation["executed_total"]<0]["executed_total"].sum()

        short_borrowing_fee = -(self.total_short_position * self.SHORT_FEE)
        interest_income = self.cash_position * self.CASH_INTEREST

        self.cash_amount = self.cash_amount + short_borrowing_fee + interest_income


