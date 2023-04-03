# from factor_data import FactorData

# factor = FactorData("a")

# factor.factor_data


import pandas as pd
from factor_data import FactorData
from price_data import PriceData

# data = FactorData("three_factor",frequency="m")

price = PriceData(["AAPL","MSFT"],start="2017-01-01",end="2021-01-01",refresh=False)

price.get_price_data()

print(price.price)




