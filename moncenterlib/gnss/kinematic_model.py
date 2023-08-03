from gnss_time_series import GnssTimeSeries
import pandas as pd
from astropy.time import Time
import os
import string
import random
from pathlib import Path


class Hector:
    def __init__(self, df):
        self.df = df
        self.df_mom = None

    def convert_df2mjd(self, first_epoch=[]):
        df_mom = self.df.iloc[:, 2:5]
        df_mom.columns = ['X', 'Y', 'Z']

        X, Y, Z = None, None, None
        if first_epoch == []:
            X, Y, Z = self.df.iloc[0][2], self.df.iloc[0][3], self.df.iloc[0][4]
        else:
            X, Y, Z = first_epoch

        dates = self.df['GPST']
        dates = dates.to_list()
        for i, date in enumerate(dates):
            dates[i] = str(date)
        t = Time(dates, scale='utc', format='iso')
        dates_mjd = t.mjd
        df_mom.insert(0, "date", dates_mjd)

        for i in range(len(df_mom)):
            df_mom.at[i, 'X'] = round(df_mom.iloc[i]['X'] - X, 6)
            df_mom.at[i, 'Y'] = round(df_mom.iloc[i]['Y'] - Y, 6)
            df_mom.at[i, 'Z'] = round(df_mom.iloc[i]['Z'] - Z, 6)
        if first_epoch == []:
            self.df_mom = df_mom.iloc[1:]
        else:
            self.df_mom = df_mom
        
        return self.df_mom

    def __create_file_df2mom(self):
        # создание временного файла конфига
        path_file_mom = ''
        while True:
            folder_conf = os.path.join(Path(__file__).resolve().parent.parent, 'conf')
            alphabet = string.ascii_letters + string.digits
            name_file = ''.join(random.choice(alphabet) for _ in range(8))
            path_file_mom = os.path.join(folder_conf, name_file) + '.mom'
            direct = Path(path_file_mom)
            if not direct.exists():
                break

        self.df_mom.to_csv(path_file_mom,
                           sep=' ',
                           index=False,
                           header=False)
        return path_file_mom

    def estimatetrend(self):
        path_file_mom = self.__create_file_df2mom()
        config = {'DataFile': '',
                  'DataDirectory': '',
                  'OutputFile': '',
                  'interpolate': '',
                  'seasonalsignal': '',
                  'halfseasonalsignal': '',
                  'estimateoffsets': '',
                  'NoiseModels': '',
                  'LikelihoodMethod': '',
                  'PhysicalUnit': '',
                  'ScaleFactor': ''}
        data_file = os.path.basename(path_file_mom)
        data_directory = path_file_mom.replace(data_file, '')
        output_file = data_directory + 'trend_' + data_file
        
        config['DataFile'] = data_file
        config['DataDirectory'] = data_directory
        config['OutputFile'] = output_file
        config['interpolate'] = 'no'
        config['seasonalsignal'] = 'yes'
        config['halfseasonalsignal'] = 'no'
        config['estimateoffsets'] = 'yes'
        config['NoiseModels'] = 'Powerlaw White'
        config['LikelihoodMethod'] = 'AmmarGrag'
        config['PhysicalUnit'] = 'm'
        config['ScaleFactor'] = '1.0'
        


GTS = GnssTimeSeries()
df = GTS.read_pos('/home/danisimo/MonCenterLib/testaa/output_pos', 'NSK1')
df_daily = GTS.get_daily_dataframe(df, 'rms', name_point='NSK1')

hector = Hector(df_daily)
df_mom = hector.convert_df2mjd()
hector.estimatetrend()
