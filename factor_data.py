import pandas as pd
from os.path import exists
from datetime import datetime
import zipfile
import urllib.request
import os
import glob



class FactorData:

    DATA_DIR = "ff_factors/"

    INFO_DICT = {
                "three_factor":{
                                "d":{
                                    "url":"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip",
                                    "zip_name":"three_factor_daily",
                                    "store_dir":"three_factor",
                                    "file_name":"F-F_Research_Data_Factors_daily.csv",
                                    "skiprows":4
                                    },

                                "m":{
                                    "url":"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip",
                                    "zip_name":"three_factor_monthly",
                                    "store_dir":"three_factor",
                                    "file_name":"F-F_Research_Data_Factors.csv",
                                    "skiprows":3
                                }
                                
                },
                "momentum":{
                            "d":{
                                "url":"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip",
                                "zip_name":"momentum_daily",
                                "store_dir":"momentum",
                                "file_name":"F-F_Momentum_Factor_daily.csv",
                                "skiprows":13
                            },
                            "m":{
                                "url":"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip",
                                "zip_name":"momentum_monthly",
                                "store_dir":"momentum",
                                "file_name":"F-F_Momentum_Factor.csv",
                                "skiprows":13
                            }
                },
                "10industry":{
                            "d":{
                                "url":"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Industry_Portfolios_daily_CSV.zip",
                                "zip_name":"10industry_daily",
                                "store_dir":"10industry",
                                "file_name":"10_Industry_Portfolios_Daily.csv",
                                "skiprows":9
                            },
                            "m":{
                                "url":"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Industry_Portfolios_CSV.zip",
                                "zip_name":"10industry_monthly",
                                "store_dir":"10industry",
                                "file_name":"10_Industry_Portfolios.csv",
                                "skiprows":11
                            },
                            "ex_div":{
                                "url":"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Industry_Portfolios_Wout_Div_CSV.zip",
                                "zip_name":"10industry_ex_div",
                                "store_dir":"10industry",
                                "file_name":"10_Industry_Portfolios_Wout_Div.csv",
                                "skiprows":11

                }
                },
                "49industry":{
                            "d":{
                                "url":"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_daily_CSV.zip",
                                "zip_name":"49industry_daily",
                                "store_dir":"49industry",
                                "file_name":"49_Industry_Portfolios_Daily.csv",
                                "skiprows":9                         
                                },                           
                            "m":{
                                "url":"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_CSV.zip",
                                "zip_name":"49industry_monthly",
                                "store_dir":"49industry",
                                "file_name":"49_Industry_Portfolios.csv",
                                "skiprows":11
                            },
                            "ex_div":{
                                "url":"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_Wout_Div_CSV.zip",
                                "zip_name":"49industry_ex_div",
                                "store_dir":"49industry",
                                "file_name":"49_Industry_Portfolios_Wout_Div.csv",
                                "skiprows":11
                    }
                }
            }


    def __init__(self, data_type:str = "all", frequency:str="m", start:str = None, end:str = None, data:bool = True, industry:str = "10industry"):
        
        self.frequency =  frequency
        self.industry = industry

        self.start = datetime.strptime(start, "%Y-%m-%d") if start is not None else None # aviod error from datetime.strptime()
        self.end = datetime.strptime(end, "%Y-%m-%d") if end is not None else None # aviod error from datetime.strptime()

        if data_type=="all":
            self.data_dict = self.INFO_DICT
            self.get_all_factor_data()

        else:

            self.data_dict = self.INFO_DICT[data_type][self.frequency]

            self.file_path = self.DATA_DIR + "//"+ self.data_dict["store_dir"] + "//" + self.data_dict["file_name"]

            # check if the data exist or not, download the data if the data doesn't exist
            if not exists(self.file_path):
                print("Factor Data doesn't exist, Downloading from the internet.")
                self.download_data()
                self.process_data()

                print("Downloaded.")
            else:
                print(self.file_path + " Existed.")

            # get the factor data and save it to self.factor_data
    
            if data:
                self.get_factor_data()



    def get_factor_data(self):

        factor_data = pd.read_csv(self.file_path, index_col=0,low_memory=False)

        factor_data.index = pd.to_datetime(factor_data.index, format="%Y-%m-%d")

        if self.start is not None:
            factor_data = factor_data.loc[factor_data.index>=self.start]
        if self.end is not None:
            factor_data = factor_data.loc[factor_data.index<=self.end]

        self.factor_data = factor_data

    def get_all_factor_data(self) -> None:

        list_of_df = []

        file_list = [f for f in self.data_dict.keys() if "industry" not in f] + [self.industry]
        for key in file_list:

            file_path = self.DATA_DIR + "/" + self.data_dict[key][self.frequency]["store_dir"] + "/" + self.data_dict[key][self.frequency]["file_name"]

            df_data = pd.read_csv(file_path,index_col=0)
            df_data.index = pd.to_datetime(df_data.index,format='%Y-%m-%d')
            list_of_df.append(df_data)

        _data = pd.concat(list_of_df,axis=1)

        if self.start is not None:
            _data = _data.loc[_data.index>=self.start]
        if self.end is not None:
            _data = _data.loc[_data.index<=self.end]


        if self.frequency=='m':
            _data.index = _data.index.strftime('%Y-%m')
        self.factor_data = _data.apply(pd.to_numeric, 
                            errors='coerce') \
                     .div(100)


        print("Concatenated all factor dataframe")
    


    def process_data(self) -> None:

        date_str = "%Y%m%d" if self.frequency == "d" else "%Y%m"

        raw_data_path = "raw_data/" + self.data_dict["store_dir"] + "/" + self.data_dict["file_name"]

        output_path  =  "ff_factors/" + self.data_dict["store_dir"] + "/" + self.data_dict["file_name"]

        df_process =  pd.read_csv(raw_data_path ,skiprows=self.data_dict["skiprows"], index_col=0,low_memory=False)
        df_process.index = pd.to_datetime(df_process.index, format=date_str,errors="coerce")# return na if the .index format isn't %Y%m%d,  then drop all the na
        df_process =  df_process.dropna() 
        df_process = df_process[~df_process.index.duplicated(keep='first')]

        df_process.to_csv(output_path)




    def download_data(self) -> None:
        """
        Fresh the Fama French 3 factors data and store in the data directory
        """

        zip_path = "zip_files/" + self.data_dict["zip_name"]

        zip_file = urllib.request.urlretrieve(self.data_dict["url"], zip_path)

        # Use the zilfile package to load the contents, here we are
        # Reading the file
        zip_file = zipfile.ZipFile(zip_path, 'r')
        # Next we extact the file data
        # We will call it ff_factors.csv
        zip_file.extractall('raw_data/' + self.data_dict["store_dir"])
        # Make sure you close the file after extraction
        zip_file.close()

        # delete all the file insider zip_files/
        files = glob.glob('zip_files/*')
        for f in files:
            os.remove(f)

