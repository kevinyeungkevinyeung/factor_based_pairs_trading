import pandas as pd
from exchange import Exchange
from price_data import PriceData
from datetime import datetime, timedelta

class PMA:



    SHORT_FEE = 0.05 / 365
    CASH_INTEREST = 0.03 / 365

    def __init__(self, initial_amount, start_date,allocation_per_trade=100000):


        self.aum = initial_amount
        self.cash_amount = initial_amount
        self.total_short_position = pd.DataFrame(columns=["date","amount","number"])
        self.total_short_position = pd.concat([
                                                self.total_short_position,
                                                pd.DataFrame([{"date":start_date,
                                                               "amount":0,
                                                               "number":0
                                                               }])
        ],axis=0)


        self.total_long_position = pd.DataFrame(columns=["date","amount","number"])
        self.total_long_position = pd.concat([
                                                self.total_long_position,
                                                pd.DataFrame([{"date":start_date,
                                                               "amount":0,
                                                               "number":0
                                                               }])
        ],axis=0)

        self.number_of_trade = pd.DataFrame(columns=["date","amount"])
        self.number_of_trade = pd.concat([
                                                self.number_of_trade,
                                                pd.DataFrame([{"date":start_date,
                                                               "amount":0
                                                               }])
        ],axis=0)


        self.allocation_per_trade = allocation_per_trade

        self.allocation = pd.DataFrame(columns=['trade_id','ticker','number_of_shares','executed_price','executed_total','trade_date'])
        self.aum_history = pd.DataFrame(columns=["date","aum"])
        self.aum_history = pd.concat([
                                        self.aum_history,
                                        pd.DataFrame([{"date":start_date,"aum":initial_amount}])   
        ],axis=0)

        self.historical_info = pd.DataFrame(columns=["trade_id","long","short","long_amount","short_amount","latest_zscore","stop_loss_threshold","hedge_ratio"])

        self.info = pd.DataFrame()


    def add_to_pma(self, orders, info, trade_date):

        """
            1.get order and trade file
            2.check if trades already in the existing allocation
            3.drop all the allocation that aren't in the new trades file
            4.give the trade to the allocation
    
        """
        # new trade info
        info['check'] = list(info["long"] + "-" + info["short"])
        new_info_dict = dict(zip(info["check"],info["trade_id"]))

        # old trade info
        old_info = self.historical_info.copy()
        old_info["check"] = list(old_info["long"]+ "-" + old_info["short"])
        old_info_dict = dict(zip(old_info["check"],old_info["trade_id"]))

        # stocks that in the allocation but not in the new order list
        # get the trade id of the trades that need to be sold
        drop_list  = [old_info_dict[ticker] for ticker in list(old_info["check"]) if ticker not in list(info['check'])]
        
        # stock that need to be added to the allocation
        # get the trade id of the trades that need to be added to the allocation
        add_list = [new_info_dict[ticker] for ticker in list(info["check"]) if ticker not in list(old_info['check'])]

        #drop the ticker that shouldn't be added to the allocation
        info = info.loc[info["trade_id"].isin(add_list)]
        orders = orders.loc[orders["trade_id"].isin(add_list)]

        # get all the info for the trades that need to be sold
        sell_info = old_info.loc[old_info["trade_id"].isin(drop_list)]
        sell_allocation = self.allocation.copy()
        sell_allocation = sell_allocation.loc[sell_allocation["trade_id"].isin(drop_list)]

        sell_allocation["order"] = sell_allocation["number_of_shares"] * -1

        del info["check"], old_info["check"]

        ###############
        # Sell Orders #
        ###############
        if not sell_allocation.empty:
            pre_sell_cash = self.cash_amount
            pre_sell_allocation= len(self.allocation)

            # send the sell order to exchagne
            sell_orders_summary, cash, exchange_fee = Exchange().send_sell_orders(sell_allocation, trade_date)

            # record the post sell transaction
            # add cash back to investable cash amount
            self.cash_amount = self.cash_amount + (cash * -1) # negative cash mean inflow, and positive cash mean outflow
            self.cash_amount = self.cash_amount - exchange_fee

            
            # delete the sold tickers from the allocation

            sold_list = list(sell_orders_summary["trade_id"])
            self.historical_info = self.historical_info.loc[~self.historical_info["trade_id"].isin(list(sell_orders_summary["trade_id"].unique()))]
            self.allocation = self.allocation.loc[~self.allocation["trade_id"].isin(list(sell_orders_summary["trade_id"].unique()))]

            post_sell_allocation = len(self.allocation)
            post_sell_cash = self.cash_amount
            print(F"""
        
                  Closed {pre_sell_allocation-post_sell_allocation} Trades, Number of Allocation Reduced from {pre_sell_allocation} to {post_sell_allocation}
                  Cash Amount went from {round(pre_sell_cash,2)} to {round(post_sell_cash,2)}
                  With Exchange Fee of {round(exchange_fee,2)}

                  """)


        ###############
        # Buy  Orders #
        ############### 
        if not orders.empty:
            
            # record number of trade per day
            self.number_of_trade = pd.concat([
                                                self.number_of_trade,
                                                pd.DataFrame([{"date":trade_date,
                                                               "amount":len(orders)
                                                               }])
        ],axis=0)

            pre_buy_allocation = len(self.allocation)
            pre_buy_cash = self.cash_amount

            ## send buy order to exchange
            orders = self.calculate_per_buy_order(orders, info)

            # send the trades to exchange for processing
            orders_summary, buy_amount ,exchange_fee = Exchange().send_buy_orders(orders, trade_date)

            ## record the cash change 
            self.cash_amount = self.cash_amount + (-1*buy_amount)
            self.cash_amount = self.cash_amount - exchange_fee
       
            orders_summary = orders_summary[["trade_id","ticker","number_of_shares","executed_price","trade_date","executed_total"]]

            # add the record to class atrr
            self.allocation = pd.concat([self.allocation,orders_summary],axis=0).reset_index(drop=True)
            self.historical_info = pd.concat([
                                    self.historical_info,
                                    info.loc[info["trade_id"].isin(list(orders_summary['trade_id']))]
                                   ],axis=0).reset_index(drop=True)
            
            post_buy_allocation = len(self.allocation)
            post_buy_cash = self.cash_amount



            print(F"""
        
                  Added {post_buy_allocation-pre_buy_allocation} Trades, Number of Allocation Increased from {pre_buy_allocation} to {post_buy_allocation}
                  Cash Amount went from {round(pre_buy_cash,2)} to {round(post_buy_cash,2)}
                  With Exchange Fee of {round(exchange_fee,2)}
                  """)


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


    def run_pma(self, trade_date):


        allocation = self.allocation.copy()

        start_date = str(datetime.strptime(trade_date, '%Y-%m-%d') - timedelta(days=10))[:10]
        self.price = PriceData(list(allocation["ticker"].unique()), start=start_date, end=trade_date, refresh=False).price

        price_dict = self.price.loc[self.price.index<=trade_date].iloc[0].to_dict()

        # calculate the current value of the portfolio
        allocation["current_price"] = allocation["ticker"].map(price_dict)
        allocation["P/L"] = allocation["current_price"] * allocation["number_of_shares"]

        # calculate interest income
        last_date = self.aum_history["date"].iloc[-1]
        last_date = datetime.strptime(last_date, '%Y-%m-%d')

        current_date = datetime.strptime(trade_date, '%Y-%m-%d')

        date_diff = (last_date-current_date).days
        interest_income = self.cash_amount * ((1+self.CASH_INTEREST)**(abs(date_diff)) -1)

        # calculate short interest
        total_short = abs(self.total_short_position["amount"].iloc[-1])
        total_short_fee = total_short * ((1+self.SHORT_FEE)**(date_diff) -1)

        # calcaulate aum
        portfolio_value = sum(allocation["P/L"])
        aum = portfolio_value + self.cash_amount + interest_income - total_short_fee

        self.aum_history = pd.concat([
                                        self.aum_history,
                                        pd.DataFrame([{"date":trade_date,"aum":aum}])   
        ],axis=0)

        # record total long and short 
        self.total_short_position = pd.concat([
                                                self.total_short_position,
                                                pd.DataFrame([{"date":trade_date,
                                                               "amount":allocation.loc[allocation["number_of_shares"]<=0]["executed_total"].sum(),
                                                               "number":len(allocation.loc[allocation["number_of_shares"]<=0])
                                                               }])
        ],axis=0)

        self.total_long_position = pd.concat([
                                                self.total_long_position,
                                                pd.DataFrame([{"date":trade_date,
                                                               "amount":allocation.loc[allocation["number_of_shares"]>0]["executed_total"].sum(),
                                                               "number":len(allocation.loc[allocation["number_of_shares"]>0])
                                                               }])
        ],axis=0)

        print(F"Date: {trade_date} -- AUM: {round(aum,2)}")






