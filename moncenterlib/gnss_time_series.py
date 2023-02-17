import pandas as pd
import os


class GnssTimeSeries:
    def read_pos(self, input_dir, name_point):

        df = pd.DataFrame()

        input_files = [os.path.join(input_dir, file) for file in os.listdir(input_dir)]

        if not input_files == []:
            for file in input_files:
                data = ''
                with open(file, 'r') as f:
                    data = f.read()
                data = data.split('\n')

                # ищем откуда начинаются решения
                start_data_index = 0
                try:
                    for i in data:
                        if not i[0] == '%':
                            start_data_index = data.index(i)
                            break
                except Exception:
                    continue

                # считываем название колонок
                name_col = ['name_point'] + ['0'] + data[start_data_index - 1].split()[1:]
                data = data[start_data_index:-2]
                data = [[name_point] + data[i].split() for i in range(len(data))]

                # загоняем в датафрейм. Так как у нас дата разбилась на дату и время их надо еще объединить в одну колонку
                df_temp = pd.DataFrame(data, columns=name_col)
                df_temp['GPST'] = df_temp['0'] + ' ' + df_temp['GPST']
                df_temp.pop('0')

                # изменяем тип данных колонок
                df_temp[df_temp.columns[0]] = df_temp[df_temp.columns[0]].astype(str)
                df_temp[df_temp.columns[2:5]] = df_temp[df_temp.columns[2:5]].astype(float)
                df_temp[df_temp.columns[5:7]] = df_temp[df_temp.columns[5:7]].astype(int)
                df_temp[df_temp.columns[7:]] = df_temp[df_temp.columns[7:]].astype(float)
                df_temp[df_temp.columns[1]] = pd.to_datetime(df_temp['GPST'], format="%Y/%m/%d %H:%M:%S.%f")

                df = pd.concat([df, df_temp])

            df = df.sort_values(by='GPST')
            df.reset_index(drop=True, inplace=True)

            return df

    def get_daily_dataframe(self, data, filter='ratio', name_point=''):
        df_daily = pd.DataFrame(columns=data.columns.values)
        date_uniq = data["GPST"].map(pd.Timestamp.date).unique()
        date_uniq = [i.strftime("%Y-%m-%d") for i in date_uniq]

        if filter == 'ratio':
            for d in date_uniq:
                df_slice = data[(data['GPST'] >= f'{d} 00:00:00') & (data['GPST'] <= f'{d} 23:59:59') & (data['name_point'] == name_point)]
                df_daily = pd.concat([df_daily, df_slice[df_slice['ratio'] == df_slice['ratio'].max()]])
            df_daily.reset_index(drop=True, inplace=True)

        elif filter == 'rms':
            for d in date_uniq:
                df_slice = data[(data['GPST'] >= f'{d} 00:00:00') & (data['GPST'] <= f'{d} 23:59:59') & (data['name_point'] == name_point)]
                row_min = None
                val_min = df_slice.iloc[[0]]
                val_min = float(val_min['sdx(m)'] ** 2 + val_min['sdy(m)'] ** 2 + val_min['sdz(m)'] ** 2)
                for index, row in df_slice.iterrows():
                    rms = row['sdx(m)'] ** 2 + row['sdy(m)'] ** 2 + row['sdz(m)'] ** 2
                    if rms < val_min:
                        val_min = rms
                        row_min = row
                df_daily.loc[len(df_daily)] = row_min
            df_daily.reset_index(drop=True, inplace=True)
        
        elif filter == 'mean':
            pass
        
        return df_daily
    
    
    def get_weekly_dataframe(self, data):
        pass

