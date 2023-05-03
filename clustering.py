from matplotlib import pyplot as plt
import numpy as np
from statistics import mean, median

class Cluster:

    def __init__(self, pca_data, method="GMM", number_of_cluster=None, cluster_floor=5, cluster_cap=None, graph=True):

        self.method = method
        self.pca_data = pca_data
        self.graph = graph
        self.cluster_floor = cluster_floor
        self.cluster_cap = cluster_cap

    
        if method == "GMM":
            self.number_of_cluster = self.get_gmm_optimal_k() if number_of_cluster==None else number_of_cluster
            self.run_gmm_clustering()
        elif method == "DBSCAN":
            self.run_dscan_clustering()
        else:
            self.run_gmm_clustering()

    def run_dscan_clustering(self):

        from sklearn.cluster import DBSCAN

        self.pca_data = self.pca_data.iloc[:,:3]


        # cluster the data into five clusters

        eps_list = sorted([n/200 for n in range(1,200)],reverse=True)

        max_eps = 0
        max_cluster = 0
        cap = self.cluster_cap or 15
        store_list = []
        for eps in eps_list:
            dbscan = DBSCAN(eps=eps, min_samples=len(self.pca_data.columns)+1).fit(self.pca_data)
            if max_cluster < len(set(dbscan.labels_)) and len(set(dbscan.labels_))<=cap:
                store_list = []
                
                max_eps = eps
                max_cluster = len(set(dbscan.labels_))
                
                store_list.append(eps)
            elif max_cluster == len(set(dbscan.labels_)) and len(set(dbscan.labels_))<=cap:
                store_list.append(eps)



        
        dbscan = DBSCAN(eps=median(store_list), min_samples=len(self.pca_data.columns)+1).fit(self.pca_data)
            
        self.pca_data['cluster'] = dbscan.labels_ # getting the labels

        self.pca_data = self.pca_data.loc[self.pca_data["cluster"]>=0]

        print(F"EPS = {median(store_list)}, # of Cluster = {max_cluster} and # of Ticker {len(self.pca_data)}")

        self.pca_data.plot.scatter(x="PC1",y="PC2",c="cluster",colormap='viridis')
        plt.show()
 
        # from mpl_toolkits import mplot3d

        # fig = plt.figure(figsize=(10,10))
        # ax = plt.axes(projection='3d')

        # ax.scatter3D(self.pca_data["PC1"], self.pca_data["PC2"], self.pca_data["PC3"],c= self.pca_data['cluster'])
        # plt.show()


        self.cluster_dict = dict(zip(self.pca_data.index, self.pca_data.cluster))


    def run_gmm_clustering(self):

        from sklearn.mixture import GaussianMixture as GMM

        gmm = GMM(n_components=self.number_of_cluster).fit(self.pca_data)

        self.pca_data['cluster'] = gmm.predict(self.pca_data)

        if self.graph:
            from mpl_toolkits import mplot3d

            fig = plt.figure(figsize=(10,10))
            ax = plt.axes(projection='3d')

            ax.scatter3D(self.pca_data["PC1"], self.pca_data["PC2"], self.pca_data["PC3"],c= self.pca_data['cluster'])


        self.cluster_dict = dict(zip(self.pca_data.index, self.pca_data.cluster))

    def get_gmm_optimal_k(self):
        from sklearn.cluster import KMeans
        import matplotlib.pyplot as plt
        

        sum_of_squared_distances = []

        data = self.pca_data[[col for col in self.pca_data.columns if 'PC' in col]]


        cluster_cap  = self.cluster_cap or int(np.sqrt(len(self.pca_data))) ## the maximum amount of cluster is the sqrt of the sample size
    
        K = range(1,cluster_cap)
        for num_clusters in K:

            kmeans = KMeans(n_clusters=num_clusters)
            kmeans.fit(data)
            sum_of_squared_distances.append(kmeans.inertia_)
            
        second_der = np.array(sum_of_squared_distances)
        evaluation = np.diff(np.diff(second_der))

        if (evaluation<0).any():
            optimal_k = 0
            while True:
                optimal_k += 1
                if evaluation[optimal_k]>0:
                    pass
                else:
                    break
        else:
            optimal_k = 10    
            
        if self.graph:
            plt.plot(K,sum_of_squared_distances,'bx-')
            plt.xlabel('Values of K') 
            plt.ylabel('Sum of squared distances/Inertia') 
            plt.title(F'Elbow Method For Optimal k = {optimal_k}')
            plt.axvline(x=optimal_k,color="red")
            plt.show()
            plt.close()

        if optimal_k <= self.cluster_floor:
            optimal_k = self.cluster_floor
        if optimal_k >= cluster_cap:
            optimal_k = cluster_cap

        return optimal_k
