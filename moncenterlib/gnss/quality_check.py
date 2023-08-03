import logging
import os
import json
from pathlib import Path
from progress.bar import IncrementalBar
import datetime as dt


class Anubis:

    """

    """

    def __init__(self, input_logger: logging = None) -> None:
        """_summary_

        Args:
            input_logger: _description_. Defaults to None.
        """

        self.match_list = dict()

        self.logger = input_logger
        if not input_logger:
            self.logger = logging.getLogger('Anubis')
            self.logger.handlers.clear()
            self.logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        print('')

    def read_dirs(self, path_obs: str, path_nav: str) -> None:
        """_summary_

        Args:
            path_obs (str): _description_
            path_nav (str): _description_

        Returns:
            _type_: _description_
        """        
        
        self.match_list = dict()
        if ' ' in path_obs or ' ' in path_nav:
            self.logger.error(
                              """Пожалуйста, уберите в пути или в названии
                                 файла пробелы. Anubis не умеет их
                                 обрабатывать""")
            raise Exception('Пожалуйста, уберите в пути пробелы. Anubis не умеет их обрабатывать')

        self.logger.info(f'Находим файлы измерений obs')
        files_obs = []
        for root, _, files in os.walk(path_obs):
            for file in files:
                path = os.path.join(root, file)
                files_obs.append(path)
        
        self.logger.info(f'Находим файлы эферид nav')
        files_nav = []
        for root, _, files in os.walk(path_nav):
            for file in files:
                path = os.path.join(root, file)
                files_nav.append(path)

        bar = IncrementalBar(f'Filter nav - Progress', max=len(files_nav),
                             suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
        bar.start()
        filter_files_nav = dict()
        for file_nav in files_nav:
            date_nav = ''
            flag_end = False
            try:
                with open(file_nav, 'r') as f_nav:
                    for n, line_nav in enumerate(f_nav, 1):
                        if 'END OF HEADER' in line_nav:
                            flag_end = True
                        elif flag_end:
                            date_nav = line_nav.split()[1:4]
                            date_nav[1] = date_nav[1].zfill(2)
                            date_nav[2] = date_nav[2].zfill(2)
                            if len(date_nav[0]) == 4:
                                date_nav = dt.datetime.strptime(
                                    f'{date_nav[0]}-{date_nav[1]}-{date_nav[2]}', '%Y-%m-%d')
                            else:
                                date_nav = dt.datetime.strptime(
                                    f'{date_nav[0]}-{date_nav[1]}-{date_nav[2]}', '%y-%m-%d')
                            
                            date_nav = date_nav.strftime('%Y-%m-%d')
                            filter_files_nav[date_nav] = file_nav
                            break
            except Exception as e:
                self.logger.error(f'Ошибка чтения файла {file_nav}-{e}')
                break
            bar.next()

        bar.finish()
        print('')

        bar = IncrementalBar(f'Match files - Progress', max=len(files_obs),
                             suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
        bar.start()
        for file_obs in files_obs:
            date_obs = ''
            marker_name = ''
            try:
                with open(file_obs, 'r') as f_obs:
                    for n, line_obs in enumerate(f_obs, 1):
                        if 'TIME OF FIRST OBS' in line_obs:
                            date_obs = line_obs.split()[:3]
                            date_obs[1] = date_obs[1].zfill(2)
                            date_obs[2] = date_obs[2].zfill(2)
                            date_obs = '-'.join(date_obs)
                        if 'MARKER NAME' in line_obs:
                            marker_name = line_obs.split()[0]
                        elif 'END OF HEADER' in line_obs:
                            break
            except Exception as e:
                self.logger.error(f'Ошибка чтения файла {file_obs}-{e}')
                continue

            if date_obs in filter_files_nav:
                bar.next()
                if marker_name in self.match_list:
                    self.match_list[marker_name].append([file_obs, filter_files_nav[date_obs]])
                else:
                    self.match_list[marker_name] = [[file_obs, filter_files_nav[date_obs]]]
        
        bar.finish()
        print('')

    def start_linux(self, obs: str = None, nav: str = None) -> dict:
        """_summary_

        Args:
            obs (str, optional): _description_. Defaults to None.
            nav (str, optional): _description_. Defaults to None.

        Returns:
            dict: _description_
        """             
        output_list = dict()

        if (obs != None and ' ' in obs) or (nav != None and ' ' in nav):
            self.logger.error(
                'Пожалуйста, уберите в пути пробелы. Anubis не умеет их обрабатывать')
            raise Exception('Пожалуйста, уберите в пути пробелы. Anubis не умеет их обрабатывать')

        if type(obs) == str and type(nav) == str:
            self.match_list = {'point': [[obs, nav]]}

        for marker_name, matchs in self.match_list.items():
            bar = IncrementalBar(f'Anubis - {marker_name} - progress',
                                 max=len(matchs),
                                 suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
            bar.start()
            print('')
            for match in matchs:
                date = ''
                if len(match) != 2:
                    self.logger.error(f'Не хватает какого то файла {match}')
                    bar.next()
                    print('')
                    continue

                anubis_path = str(Path(__file__).resolve().parent.parent.parent)
                anubis_path = anubis_path + '/bin/Anubis/anubis-3.5-lin-static-64b'
               
                cmd = f'{anubis_path} --full '
                cmd += f':inp:rinexo "{match[0]}" '
                cmd += f':inp:rinexn "{match[1]}" '
                cmd += ':qc:sec_sum=2 '
                cmd += ':qc:sec_hdr=0 '
                cmd += ':qc:sec_obs=1 '
                cmd += ':qc:sec_gap=1 '
                cmd += ':qc:sec_bnd=1 '
                cmd += ':qc:sec_pre=1 '
                cmd += ':qc:sec_mpx=1 '
                cmd += ':qc:sec_snr=1 '
                cmd += f':out:xtr {match[0]}.xtr'
                self.logger.info('Запукс Anubis')
                os.system(cmd)
                try:
                    f = open(f'{match[0]}.xtr', 'r')
                    data = f.readlines()
                    f.close()
                except Exception as e:
                    self.logger.error(
                        f'Что то случилось с открытием файла Anubis {match[0]}.xtr. {e}')
                    bar.next()
                    print('')
                    continue

                self.logger.info(
                    f'Начинаем парсить файл Anubis {match[0]}.xtr')
                meta_data = {}
                flag_gnssum = False
                flag_data_error = False
                for indx, row in enumerate(data):
                    if '=TOTSUM' in row:
                        row_split = row.split(' ')
                        row_split = list(filter(lambda i: i != '', row_split))
                        date = row_split[1] + " " + row_split[2]
                        try:
                            meta_data["total_time"] = float(row_split[5])
                            meta_data["ExptObs"] = int(row_split[8])
                            meta_data["ExisObs"] = int(row_split[9])
                            meta_data["%Ratio"] = float(row_split[10])
                            meta_data["ExptObs>10"] = int(row_split[13])
                            meta_data["ExisObs>10"] = int(row_split[14])
                            meta_data["%Ratio>10"] = float(row_split[15])
                        except Exception as e:
                            self.logger.error(
                                f'Что то не так с парсингом файла. Параметр =TOTSUM. Пропуск обработки. {e}')
                            flag_data_error = True
                            break

                    elif '#GNSSUM' in row:
                        if flag_gnssum:
                            continue
                        flag_gnssum = True

                        meta_data["missEpoch"] = dict()
                        meta_data["CodeMulti"] = dict()
                        meta_data["nSlip"] = dict()
                        count = 0
                        while True:
                            row_data = data[indx+2+count]
                            if row_data == '\n':
                                break
                            row_data = row_data.split(' ')
                            row_split = list(
                                filter(lambda i: i != '', row_data))
                            name_sys = row_split[0].replace(
                                "=", "").replace("SUM", "")
                            try:
                                meta_data["missEpoch"][name_sys] = int(
                                    row_split[11])
                                meta_data["nSlip"][name_sys] = int(
                                    row_split[14])
                            except Exception as e:
                                self.logger.error(
                                    f'Что то не так с парсингом файла. Параметр #GNSSUM. Пропуск обработки. {e}')
                                flag_data_error = True
                                break

                            try:
                                meta_data["CodeMulti"][name_sys +
                                                       "MP1"] = float(row_split[18])
                            except ValueError as e:
                                self.logger.warning(f'Попался дефис. {e}')
                                meta_data["CodeMulti"][name_sys +
                                                       "MP1"] = row_split[18]

                            try:
                                meta_data["CodeMulti"][name_sys +
                                                       "MP2"] = float(row_split[19])
                            except ValueError as e:
                                self.logger.warning(f'Попался дефис. {e}')
                                meta_data["CodeMulti"][name_sys +
                                                       "MP2"] = row_split[19]
                            count += 1

                        meta_data["missEpoch"] = json.dumps(
                            meta_data["missEpoch"])
                        meta_data["CodeMulti"] = json.dumps(
                            meta_data["CodeMulti"])
                        meta_data["nSlip"] = json.dumps(meta_data["nSlip"])
                        if flag_data_error:
                            break

                    elif '=GNSSYS' in row:
                        meta_data["SAT_healthy"] = dict()
                        row_data = row
                        row_split = row_data.split(' ')
                        row_split = list(filter(lambda i: i != '', row_split))
                        num_sys = int(row_split[3])
                        for i in range(num_sys):
                            row_data = data[indx+2+i]
                            row_split = row_data.split(' ')
                            row_split = list(
                                filter(lambda i: i != '', row_split))
                            name_sys = row_split[0].replace(
                                "=", "").replace("SAT", "")
                            try:
                                meta_data["SAT_healthy"][name_sys] = int(
                                    row_split[3])
                            except Exception as e:
                                self.logger.error(
                                    f'Что то не так с парсингом файла. Параметр SAT_healthy. Пропуск обработки. {e}')
                                flag_data_error = True
                                break
                        meta_data["SAT_healthy"] = json.dumps(
                            meta_data["SAT_healthy"])

                        if flag_data_error:
                            break

                    elif '#GNSSxx' in row:
                        meta_data["Sig2Noise"] = dict()
                        count = 0
                        while True:
                            try:
                                row_data = data[indx+1+count]
                            except Exception:
                                break

                            if row_data == '\n':
                                break
                            row_data = row_data.split(' ')
                            row_split = list(
                                filter(lambda i: i != '', row_data))
                            name_sys = row_split[0].replace("=", "")
                            try:
                                meta_data["Sig2Noise"][name_sys] = float(row_split[3])
                            except Exception as e:
                                self.logger.error(
                                    f'Что то не так с парсингом файла. Параметр Sig2Noise. Пропуск обработки. {e}')
                                
                                
                            count += 1
                        meta_data["Sig2Noise"] = json.dumps(
                            meta_data["Sig2Noise"])
                        if flag_data_error:
                            break

                if flag_data_error:
                    self.logger.error(
                        f'Некорректные данные в файле Anubis {match[0]}.xtr.')
                    bar.next()
                    print('')
                    continue

                try:
                    data2df = {'total_time': meta_data['total_time'],
                               'ExptObs': meta_data['ExptObs'],
                               'ExisObs': meta_data['ExisObs'],
                               '%Ratio': meta_data['%Ratio'],
                               'ExptObs>10': meta_data['ExptObs>10'],
                               'ExisObs>10': meta_data['ExisObs>10'],
                               '%Ratio>10': meta_data["%Ratio>10"],
                               'missEpoch': meta_data['missEpoch'],
                               'CodeMulti': meta_data['CodeMulti'],
                               'SAT_healthy': meta_data['SAT_healthy'],
                               'nSlip': meta_data['nSlip'],
                               'Sig2Noise': meta_data['Sig2Noise']
                               }

                except KeyError as e:
                    self.logger.error(
                        f'Что то случилось с формированием новой записи. {e}')
                    bar.next()
                    print('')
                    continue

                try:
                    os.remove(match[0]+'.xtr')
                except Exception as e:
                    self.logger.error(
                        f'Что то случилось с удалением файла {match[0]}.xtr. {e}')

                if marker_name in output_list:
                    output_list[marker_name][date] = data2df
                else:
                    output_list[marker_name] = {}
                    output_list[marker_name][date] = data2df

                bar.next()
                print('')
        bar.finish()
        print('')
        self.match_list = list()
        return output_list
