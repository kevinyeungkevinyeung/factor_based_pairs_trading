import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class PairsTrade:

    def __init__(self, model_data, clustering, price_data, lookback_data, allocation_date, entry_zscore=2, stop_loss_zscore=3,test_percentile=0.25, display=False):

        self.display = display

        self.test_percentile = test_percentile

        self.lookback_data = lookback_data
        self.model_data = model_data
        self.price_data = price_data
        self.clustering = clustering

        self.entry_zscore = entry_zscore
        self.stop_loss_zscore = stop_loss_zscore

        self.allocation_date = allocation_date

        self.price = price_data.price.copy()
        self.price_lb = lookback_data.price.copy()
        
        self.cluster_dict = clustering.cluster_dict
        self.lookback_return_dict = (self.lookback_data.price.iloc[-1]/self.lookback_data.price.iloc[0] - 1).to_dict()

        self.factors = model_data.clustering_coefficients
        self.factors["cluster"] = self.factors.index.map(self.cluster_dict)
        self.factors["lookback_return"] = self.factors.index.map(self.lookback_return_dict)

        self.factors_full = model_data.ts_coef
        self.factors_full["cluster"] = self.factors_full.index.map(self.cluster_dict)
        self.factors_full["lookback_return"] = self.factors_full.index.map(self.lookback_return_dict)
        
        
        self.find_pairs()

        self.generate_allocation_list()


    def find_pairs(self):

        
        # factors without const and market return
        import statsmodels.api as sm
        from statsmodels.tsa.stattools import adfuller

        df_count = self.factors[['cluster',"lookback_return"]].groupby('cluster',as_index=False).count()


        num_of_ticker_dict = dict(zip(df_count.cluster,df_count.lookback_return))


        data_list = []
        for cluster in df_count.cluster:
            
            print(F"--------- Runing Cluster {cluster} ---------------")
            

            df_pairs = self.factors.loc[self.factors.cluster==cluster].sort_values("lookback_return")

            num_selected = int(np.ceil(num_of_ticker_dict[cluster] * self.test_percentile))

            long_pairs = df_pairs.head(num_selected).index.values
            short_pairs = df_pairs.tail(num_selected).index.values

            for l in long_pairs:
                for s in short_pairs:
                    try:
                        x = self.price[l]
                        y = self.price[s]

                        x1 = self.price_lb[l]
                        y1 = self.price_lb[s]

                        model = sm.OLS(x,y)
                        model = model.fit()

                        spread = y - (model.params[0] * x)

                        spread_1 = y1 - (model.params[0]* x1)

                        adf = adfuller(spread, maxlag=1)


                        stationary = True if adf[1] <0.05 else False

                        mean = spread.mean()
                        std = spread.std()

                        entry_point_lower = mean - std * self.entry_zscore
                        entry_point_upper = mean + std * self.entry_zscore

                        stop_lost_lower = mean - std * self.stop_loss_zscore
                        stop_lost_upper = mean + std * self.stop_loss_zscore


                        spread = spread.to_frame()
                        spread.columns = ["spread"]
                        spread_1 = spread_1.to_frame()
                        spread_1.columns = ["out_of_sample"]

                        spread["mean"] = mean
                        spread["stop_lost_lower"] = stop_lost_lower
                        spread["stop_lost_upper"] = stop_lost_upper
                        spread["entry_lower"] = entry_point_lower
                        spread["entry_upper"] = entry_point_upper

                        spread_1["mean"] = mean
                        spread_1["stop_lost_lower"] = stop_lost_lower
                        spread_1["stop_lost_upper"] = stop_lost_upper
                        spread_1["entry_lower"] = entry_point_lower
                        spread_1["entry_upper"] = entry_point_upper

                        spread = pd.concat([spread,spread_1],axis=0)

                        last_value = spread_1["out_of_sample"].iloc[-1]

                        latest_zscore = (last_value-mean)/std

                        if self.display and stationary:
                            plt.figure(figsize=(15,10))
                            plt.title(F"Long {l}, Short {s} {'is' if stationary else 'is not'} stationary")
                            plt.plot(spread.index,spread.spread, label="in-sample spread")
                            plt.plot(spread.index,spread.out_of_sample, label="out-of-sample")
                            plt.plot(spread.index,spread.stop_lost_lower,"--", label="Stop Lost -- Lower",color='red')
                            plt.plot(spread.index,spread.stop_lost_upper,"--", label="Stop Lost -- Upper",color='red')
                            plt.plot(spread.index,spread.entry_lower,"--", label="Entry Point -- Lower",color='green')
                            plt.plot(spread.index,spread.entry_upper,"--", label="Entry Point -- Upper",color='green')
                            plt.plot(spread.index,spread["mean"],label="mean")

                            plt.legend()
                            plt.show()

                        data_list.append({
                                            "date":self.allocation_date,
                                            "long":l,
                                            "short":s,
                                            "hedge_ratio":model.params[0], # spread = y - (hedge_ratio * x)
                                            "is_contin":stationary,
                                            'adf_p_values':adf[1],
                                            "long_lb_return":self.lookback_return_dict[l],
                                            "short_lb_return":self.lookback_return_dict[s],
                                            "latest_zscore":latest_zscore,
                                            "cluster":cluster,
                                            "long_entry":entry_point_upper,
                                            "short_entry":entry_point_lower,
                                            "long_stop_loss":stop_lost_upper,
                                            "short_stop_loss":stop_lost_lower,
                                            "mean":mean,
                                            "std":std

                        })
                    except:
                        pass

        df_contin = pd.DataFrame(data_list,columns=[
                                                "date",
                                                "long",
                                                "short",
                                                "hedge_ratio",
                                                "is_contin",
                                                "adf_p_values",
                                                "long_lb_return",
                                                "short_lb_return",
                                                "latest_zscore",
                                                "long_entry",
                                                "short_entry",
                                                "long_stop_loss",
                                                "short_stop_loss",
                                                "cluster",
                                                "mean",
                                                "std"
                                                ]
                                                ) 

        

        condition = (df_contin["is_contin"]==True)#&((df_contin["latest_zscore"]>-3)&(df_contin["latest_zscore"]<3))&((df_contin["latest_zscore"]>2)|(df_contin["latest_zscore"]<-2))
        self.pairs = df_contin.loc[condition] ## only enter to trades that have extreme zscore

    def generate_allocation_list(self):

        short_ratio_list = []
        allocation_list = []
        for long, short in self.pairs[["long","short"]].values:
            
            df_pair_factors = self.factors_full[self.factors_full.index.isin([long,short])]
            
            long_market_beta = df_pair_factors.loc[long]["Mkt-RF"]
            short_market_beta = df_pair_factors.loc[short]["Mkt-RF"]
            
            market_neutral_ratio = long_market_beta / short_market_beta
            
            short_ratio_list.append(market_neutral_ratio)
            
            allocation_list.append(
                                    {
                                    "ticker":long,
                                    "weight":1
                                    }
            )

            allocation_list.append({
                                    "ticker":short,
                                    "weight":market_neutral_ratio * -1
            })
            
        self.pairs["short_amount"] = short_ratio_list
        self.pairs["short_amount"] = self.pairs["short_amount"] * -1

        self.allocation = pd.DataFrame(allocation_list)

        self.weight_per_position = 1 / self.allocation["weight"]

        

        # self.allocation["percentage"] = 


        