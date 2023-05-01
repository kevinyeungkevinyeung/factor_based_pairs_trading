import pandas as pd
from factor_data import FactorData
from price_data import PriceData
from factor_model import FactorModel
from pca import PCA
from clustering import Cluster
from find_pairs import PairsTrade
from allocator import Allocator
from pma import PMA

pd.set_option('display.max_columns', None)
from matplotlib import style
import matplotlib.pyplot as plt
plt.style.use('bmh')

start = "2019-01-01"
end = "2021-01-01"

display = False

price_data = PriceData(["all"], start=start, end=end, refresh=False)
lookback_data = PriceData(["all"], start='2021-01-01', end='2021-06-01',ticker_ref_date="2021-01-01", refresh=False)
factors = FactorData("all", frequency="m", start=start, end=end)

# print(price_data.asset_return.head())
# print(factors.factor_data.head())

_factor_model = FactorModel(
                            price_data.asset_return, 
                            factors.factor_data,
                            ts_pvalues_threshold=0.1,
                            factor_hard_cap=25,
                            coff_std_limit=5
)

print(_factor_model.clustering_coefficients)

_pca = PCA(_factor_model.clustering_coefficients)

print(_pca.pca.head())


