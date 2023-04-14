
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class PCA:

    def __init__(self, data, cum_explain_threshold=0.75, display=True):

        self.data = data
        self.cum_explain_threshold = cum_explain_threshold

        self.calculate_pca()


    def calculate_pca(self):

        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA

        sc = StandardScaler()
        x = sc.fit_transform(self.data)

        # run the pca algo, the number of pc is equal to the number of factor
        pca = PCA(n_components=x.shape[1])
        pca.fit(x)

        explained_variance = pca.explained_variance_ratio_

        self.cum_explain = np.cumsum(explained_variance)

        # set a threshold for number of PC
        number_of_pc = sum(self.cum_explain<self.cum_explain_threshold) + 1 if sum(self.cum_explain<self.cum_explain_threshold)>=3 else 3 # minimum amount of pc will be 3

        df_pca = pd.DataFrame(pca.fit_transform(x),columns=["PC"+str(num+1) for num in range(x.shape[1])])

        df_pca = df_pca[["PC" + str(num+1) for num in range(number_of_pc)]]

        df_pca.index = self.data.index # put the ticker bk, instead of using numeric index

        self.pca = df_pca

        if display:
            print("""
Cumulative sum of proportion of variance""")
            df_display = pd.DataFrame(self.cum_explain,index=["PC"+str(num) for num in range(len(self.cum_explain))]).T
            display(df_display)
