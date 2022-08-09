from typing import List
from pprint import pprint
import os
from pathlib import Path


class Rnx2Pos:
    def __init__(self) -> None:
        self.match_list = dict()
        self.pos_paths = []
        self.__kol_inputs = 0

    def read_dirs(self, input_rover: str, input_base: str = '', input_nav: str = '', input_sp3_clk: str = '', input_sbas_ionex_fcb: str = '') -> dict:
        if not type(input_rover) is str:
            raise TypeError(
                "The type of the 'input_rover' variable should be 'str'")
        elif not type(input_base) is str:
            raise TypeError(
                "The type of the 'input_base' variable should be 'str'")
        elif not type(input_nav) is str:
            raise TypeError(
                "The type of the 'input_nav' variable should be 'str'")
        elif not type(input_sp3_clk) is str:
            raise TypeError(
                "The type of the 'input_sp3_clk' variable should be 'str'")
        elif not type(input_sbas_ionex_fcb) is str:
            raise TypeError(
                "The type of the 'input_sbas_ionex_fcb' variable should be 'str'")
        
        rover_files = os.listdir(input_rover)
        rover_files = list(map(lambda x: os.path.join(input_rover, x) , rover_files))
        pprint(rover_files)

    def read_list(self, input_rover: List[str], input_base: List[str] = [], input_nav: List[str] = [], input_sp3_clk: List[str] = [], input_sbas_ionex_fcb: List[str] = []) -> dict:
        if not type(input_rover) is list:
            raise TypeError(
                "The type of the 'input_rover' variable should be 'list'")
        elif not type(input_base) is list:
            raise TypeError(
                "The type of the 'input_base' variable should be 'list'")
        elif not type(input_nav) is list:
            raise TypeError(
                "The type of the 'input_nav' variable should be 'list'")
        elif not type(input_sp3_clk) is list:
            raise TypeError(
                "The type of the 'input_sp3_clk' variable should be 'list'")
        elif not type(input_sbas_ionex_fcb) is list:
            raise TypeError(
                "The type of the 'input_sbas_ionex_fcb' variable should be 'list'")

        # узнаем кол-во списков
        self.__kol_inputs = 0
        if not input_rover == []:
            self.__kol_inputs += 1
        if not input_base == []:
            self.__kol_inputs += 1
        if not input_nav == []:
            self.__kol_inputs += 1
        if not input_sp3_clk == []:
            self.__kol_inputs += 1
        if not input_sbas_ionex_fcb == []:
            self.__kol_inputs += 1

        for file in input_rover + input_base:
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'TIME OF FIRST OBS' in line:
                        date = '/'.join(line.split()[:3])
                        if date in self.match_list:
                            self.match_list[date] += [file]
                        else:
                            self.match_list[date] = [file]
                        break
                    elif 'END OF HEADER' in line:
                        break

        for file in input_nav + input_sp3_clk:
            flag_end = False
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'END OF HEADER' in line:
                        flag_end = True
                    elif flag_end:
                        date = line.split()[1:4]
                        date[0] = '20' + \
                            date[0] if not len(date[0]) == 4 else date[0]
                        date = '/'.join(date)
                        if date in self.match_list:
                            self.match_list[date] += [file]
                        else:
                            self.match_list[date] = [file]
                        break
        # sbas
        #
        # sbas

        return self.match_list

    def start(self, path_rtklib: str, rtklib_conf: str, output_dir: str, start_time: str = '', end_time: str = '', timeint: str = ''):
        if not type(path_rtklib) is str:
            raise TypeError(
                "The type of the 'path_rtklib' variable should be 'str'")
        elif not type(rtklib_conf) is str:
            raise TypeError(
                "The type of the 'rtklib_conf' variable should be 'str'")
        elif not type(output_dir) is str:
            raise TypeError(
                "The type of the 'output_dir' variable should be 'str'")
        elif not type(start_time) is str:
            raise TypeError(
                "The type of the 'start_time' variable should be 'str'")
        elif not type(end_time) is str:
            raise TypeError(
                "The type of the 'end_time' variable should be 'str'")
        elif not type(timeint) is str:
            raise TypeError(
                "The type of the 'timeint' variable should be 'str'")

        error_list = {}
        for key, value in self.match_list.items():
            if len(value) == self.__kol_inputs:
                command = f'{path_rtklib} '
                command += f'-ts {start_time} ' if not start_time == '' else ''
                command += f'-te {end_time} ' if not end_time == '' else ''
                command += f'-ti {timeint} '
                command += f"-k {rtklib_conf} "
                for path_file in value:
                    command += path_file + ' '
                command += f"-o {output_dir}/{os.path.basename(value[0])}.pos"
                self.pos_paths.append(
                    f"{output_dir}/{os.path.basename(value[0])}.pos")
                # print(command)
                os.system(command)
            else:
                error_list[key] = [value, "Not enough files"]
        return self.pos_paths, error_list


if __name__ == "__main__":
    input_rover = ['/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0010.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0020.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0030.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0040.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0050.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0060.22o',
                   '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0070.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0080.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0090.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0100.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0110.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0120.22o']
    input_base = ['/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10020.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10030.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10040.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10050.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10060.22o',
                  '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10070.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10080.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10090.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10110.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10120.22o']
    input_nav = ['/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10020.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10030.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10040.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10050.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10060.22n',
                 '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10070.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10080.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10090.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10110.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10120.22n']
    a = Rnx2Pos()
    #a.read_list(input_rover, input_base, input_nav)
    a.read_dirs('/home/danisimo/Desktop/MonCenterWeb/MonCenterLib/test/NOVM')
    
    #pprint(a.start('/home/danisimo/Desktop/MonCenterWeb/RTKLIB_2.4.3_b34/app/consapp/rnx2rtkp/gcc/rnx2rtkp',
     #      '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/rnx2rtkp.conf', str(Path.cwd())))
