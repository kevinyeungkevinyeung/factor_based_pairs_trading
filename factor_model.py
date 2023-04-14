import pandas as pd

class FactorModel:

    def __init__(self, df_return, df_factors, ts_pvalues_threshold=1, factor_hard_cap=15, coff_std_limit=3):

        self._returns = df_return.copy()
        self.factors = df_factors.copy()
        self.ts_pvalues_threshold = ts_pvalues_threshold # all the regression ceoficients with higher pvalues than this parameter will be convert to 0
        self.coff_std_limit = 4 # all regress cofficients that are beyond (mean - coff_std_limt) or beyond (mean + coff_std_limit) will be set to the limit
        self.factor_hard_cap = factor_hard_cap

        # loop thru all the ticker and get the ts regression coefficient for each ticker
        self.get_ts_factor()

        self.process_ts_factor()

    def get_ts_factor(self):
        
        print("""
Running Time Series Regression......
                """)

        import statsmodels.api as smf

        params_list = []
        pvalues_list = []

        for ticker in self._returns.columns:
            df_regress = pd.concat([
                                    self._returns[ticker],
                                    self.factors
                                    ],axis=1).dropna()

            Y = df_regress.iloc[:,0]
            X = df_regress.iloc[:,1:]

            X = smf.add_constant(X)

            model = smf.OLS(Y,X)

            result = model.fit()

            params_list.append(result.params.to_frame().rename(columns={0:ticker}).T)

            pvalues_list.append(result.pvalues.to_frame().rename(columns={0:ticker}).T)

        self.ts_coef = pd.concat(params_list,axis=0)

        self.ts_pvalues = pd.concat(pvalues_list,axis=0)

        print(F"""
{len(self.ts_coef)} of ticker's Time Series Factors have been generated.

-----------------------------------------------------------------------

                """
        )

    def process_ts_factor(self):

        print("""Postprocessing Factor Data ......
        
        """)

        pvalues_std = self.ts_coef.std()
        pvalues_mean = self.ts_coef.mean()

        # enforce the hard cap for each columns, drop the row if any of the factor excessed the hard cap
        for col in self.ts_coef.columns:
            self.ts_coef = self.ts_coef.loc[(self.ts_coef[col]>-self.factor_hard_cap) & (self.ts_coef[col]<self.factor_hard_cap)]


        pvalues_floor = (pvalues_mean - (pvalues_std * self.coff_std_limit)).to_dict()
        pvalues_cap = (pvalues_mean + (pvalues_std * self.coff_std_limit)).to_dict()


        # loop thru the columns to drop outlier from the dataset
        df_para_processed = self.ts_coef.copy()

        for col in df_para_processed.columns:

            # set outiers at positive side to cap values
            df_para_processed.loc[(df_para_processed[col]>pvalues_cap[col]),col] = pvalues_cap[col]
            
            # set outiers at the negative side to floor values
            df_para_processed.loc[(df_para_processed[col]<pvalues_floor[col]),col] = pvalues_floor[col]

        # set 
        df_para_processed[df_para_processed>self.ts_pvalues_threshold] = 0

        self.factor_cofficients_processed = df_para_processed

        self.clustering_coefficients = df_para_processed.iloc[:,2:]

        print("Done.")
            



