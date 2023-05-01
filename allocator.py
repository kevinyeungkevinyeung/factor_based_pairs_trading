import pandas as pd
from price_data import PriceData

class Allocator:

    def __init__(self, trades, trade_date,investment_amount=1000000):
        
        self.trades = trades
        self.trade_date = trade_date
        self.investment_amount = investment_amount
        self.tickers = list(set(list(self.trades['long']) + list(self.trades['short']))) # get unique ticker from the trade file

        self.price = PriceData(self.tickers, start='2020-01-01', end='2020-03-01',ticker_ref_date="2022-01-01", refresh=False).price

        self.last_price = self.price.iloc[-1].to_dict()



    def calculate_trades(self):


        trades_list = []
        info_list = []
        _id = 0
        for num in range(len(self.trades)):

            trade_details = self.trades.iloc[num].to_dict()

            spread = self.price[trade_details["short"]].iloc[-1] - (trade_details["hedge_ratio"] * self.price[trade_details["long"]].iloc[-1])

            trade_id = F"{self.trade_date}--{str(_id)}"

            if spread >  trade_details["long_entry"] and spread < trade_details["long_stop_loss"]:

                info_list.append(
                                    {
                                        "trade_id":trade_id,
                                        "long":trade_details["long"],
                                        "short":trade_details["short"],
                                        "long_amount":1,
                                        "short_amount":trade_details["short_amount"],
                                        'latest_zscore':(spread-trade_details["mean"]) / trade_details["std"],
                                        "stop_loss_threshold":trade_details["long_stop_loss"],
                                        "hedge_ratio":trade_details["hedge_ratio"]
                                    }
                )

                trades_list.append(
                                    {
                                        "trade_id":trade_id,
                                        "date":self.trade_date,
                                        "ticker":trade_details["long"],
                                        "unit_amount":1
                                    }
                )

                trades_list.append(
                                    {
                                        "trade_id":trade_id,
                                        "date":self.trade_date,
                                        "ticker":trade_details["short"],
                                        "unit_amount":trade_details["short_amount"]
                                    }
                )

                _id += 1
                
            elif spread < trade_details['short_entry'] and spread > trade_details['short_stop_loss']:

                info_list.append(
                                    {
                                        "trade_id":trade_id,
                                        "long":trade_details["short"],
                                        "short":trade_details["long"],
                                        "long_amount":trade_details["short_amount"],
                                        "short_amount":1,
                                        'latest_zscore':(spread-trade_details["mean"]) / trade_details["std"],
                                        "stop_loss_threshold":trade_details["short_stop_loss"],
                                        "hedge_ratio":trade_details["hedge_ratio"]
                                    }
                )

                trades_list.append(
                                    {
                                        "trade_id":trade_id,
                                        "date":self.trade_date,
                                        "ticker":trade_details["short"],
                                        "unit_amount":trade_details["short_amount"]
                                    }
                )

                trades_list.append(
                                    {
                                        "trade_id":trade_id,
                                        "date":self.trade_date,
                                        "ticker":trade_details["long"],
                                        "unit_amount":1
                                    }
                )

                _id += 1

        self.info = pd.DataFrame(info_list)
        self.orders = pd.DataFrame(trades_list)

    
        
        