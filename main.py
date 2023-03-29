# from factor_data import FactorData

# factor = FactorData("a")

# factor.factor_data


import pandas as pd
from factor_data import FactorData
from price_data import PriceData

# data = FactorData("three_factor",frequency="m")

aapl = PriceData("AAPL")

aapl.get_stock_price()

df_price = aapl.df.copy()



