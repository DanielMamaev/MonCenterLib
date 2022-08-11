import argparse
from typing import List
from pprint import pprint
import os
import sys


class Rnx2Pos:
    '''
    Rnx2Pos inputs the standard RINEX observation data and navigation message files (GPS, GLONASS, Galileo, QZSS,
    BeiDou and SBAS) and can computers the positioning solutions by various positioning modes including
    Single‐point, DGPS/DGNSS, Kinematic, Static, PPP‐Kinematic and PPP‐Static.
    The module can accept one or more files.The module can accept one or more files. 
    Thanks to this functionality, it becomes possible to process a large number of files with the same settings.
    '''

    def __init__(self) -> None:
        self.__kol_inputs = 0

    def read_dirs(self, input_rover: str, input_base: str = '', input_nav: str = '', input_sp3_clk: str = '', input_sbas_ionex_fcb: str = '') -> dict:
        '''
        This method reads files from the specified directories and creates a match_list dictionary
        '''
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

        rover_files = list(map(lambda x: os.path.join(input_rover, x), os.listdir(
            input_rover))) if input_rover != '' else []
        base_files = list(map(lambda x: os.path.join(input_base, x), os.listdir(
            input_base))) if input_base != '' else []
        nav_files = list(map(lambda x: os.path.join(input_nav, x), os.listdir(
            input_nav))) if input_nav != '' else []
        sp3_clk_files = list(map(lambda x: os.path.join(input_sp3_clk, x), os.listdir(
            input_sp3_clk))) if input_sp3_clk != '' else []
        sbas_ionex_fcb_files = list(map(lambda x: os.path.join(input_sbas_ionex_fcb, x), os.listdir(
            input_sbas_ionex_fcb))) if input_sbas_ionex_fcb != '' else []

        return self.read_list(rover_files, base_files, nav_files, sp3_clk_files, sbas_ionex_fcb_files)

    def read_list(self, input_rover: List[str], input_base: List[str] = [], input_nav: List[str] = [], input_sp3_clk: List[str] = [], input_sbas_ionex_fcb: List[str] = []) -> dict:
        '''
        This method reads lists containing paths to files and forms a match_list dictionary from them.
        '''
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

        match_list = dict()

        for file in input_rover + input_base:
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'TIME OF FIRST OBS' in line:
                        date = '/'.join(line.split()[:3])
                        if date in match_list:
                            match_list[date] += [file]
                        else:
                            match_list[date] = [file]
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
                        if date in match_list:
                            match_list[date] += [file]
                        else:
                            match_list[date] = [file]
                        break
        # sbas
        #
        # sbas

        return match_list

    def start(self, match_list: dict, path_rtklib: str, rtklib_conf: str, output_dir: str, timeint: int = ''):
        '''
        This method starts the post-processing process. The output generates a list with paths to the generated .pos files.
        '''
        if not type(path_rtklib) is str:
            raise TypeError(
                "The type of the 'path_rtklib' variable should be 'str'")
        elif not type(rtklib_conf) is str:
            raise TypeError(
                "The type of the 'rtklib_conf' variable should be 'str'")
        elif not type(output_dir) is str:
            raise TypeError(
                "The type of the 'output_dir' variable should be 'str'")
        elif not type(timeint) is int:
            raise TypeError(
                "The type of the 'timeint' variable should be 'int'")
        elif not type(match_list) is dict:
            raise TypeError(
                "The type of the 'match_list' variable should be 'dict'")

        error_list = {}
        pos_paths = []
        for key, value in match_list.items():
            if len(value) == self.__kol_inputs:
                command = f'{path_rtklib} '
                command += f'-ti {timeint} ' if timeint != '' else ''
                command += f"-k {rtklib_conf} "
                for path_file in value:
                    command += f"'{path_file}'" + ' '
                command += f"-o '{os.path.join(output_dir, os.path.basename(value[0]))}.pos'"
                pos_paths.append(
                    f"{os.path.join(output_dir, os.path.basename(value[0]))}.pos")
                # print(command)
                os.system(command)
            else:
                error_list[key] = [value, "Not enough files"]
        return pos_paths, error_list


if __name__ == "__main__":
    des = '''
    Rnx2Pos inputs the standard RINEX observation data and navigation message files (GPS, GLONASS, Galileo, QZSS,
    BeiDou and SBAS) and can computers the positioning solutions by various positioning modes including
    Single‐point, DGPS/DGNSS, Kinematic, Static, PPP‐Kinematic and PPP‐Static.
    The module can accept one or more files.The module can accept one or more files. 
    Thanks to this functionality, it becomes possible to process a large number of files with the same settings.
    '''
    parser = argparse.ArgumentParser(description=des)
    parser.add_argument('-r', '--rtklib', type=str,
                        help='Specify the path to the rnx2rtkp executable.')
    parser.add_argument('-c', '--conf', type=str,
                        help='Specify the path to rnx2rtkp config.')
    parser.add_argument('-o', '--output', type=str,
                        help='Specify the path to the output folder.')
    parser.add_argument('-pr', '--prover', type=str,
                        help='Specify the path to the folder with the rover files. Types: .*obs, .*O, .*D')
    parser.add_argument('-pb', '--pbase', type=str,
                        help='Specify the path to the folder with the base files. Types: .*obs, .*O, .*D')
    parser.add_argument('-pn', '--pnav', type=str,
                        help='Specify the path to the folder with the ephemeris files. Types: .*nav, .*N, .*P, .*G, .*H, .*Q')
    parser.add_argument('-pa1', '--pa1', type=str,
                        help='Specify the path to the folder with the Precise ephemeris or Clock files. Types: .sp3, .clk*, .eph*')
    parser.add_argument('-pa2', '--pa2', type=str,
                        help='Specify the path to the folder with the FCB, IONEX or SBAS files. Types: .fcb, .*i, .ionex, .sbs, .ems')
    parser.add_argument('-t', '--timeint', type=str, help='Interval (s)')
    parser.add_argument('-ml', '--matchlist',
                        action='store_true', help='Show match list')
    parser.add_argument('-p', '--poslist', action='store_true',
                        help='Show paths to generated .pos files')
    arg = parser.parse_args()

    if arg.rtklib is None:
        print('Error. Specify the path to rnx2rtkp.')
        sys.exit()
    if arg.conf is None:
        print('Error. Specify the path to rnx2rtkp config.')
        sys.exit()
    if arg.output is None:
        print('Error. Specify the path to the output folder.')
        sys.exit()
    if arg.prover is None:
        print('Error. Specify the path to the folder with the rover files.')
        sys.exit()

    rnx2pos = Rnx2Pos()
    input_rover = arg.prover if not arg.prover is None else ''
    input_base = arg.pbase if not arg.pbase is None else ''
    input_nav = arg.pnav if not arg.pnav is None else ''
    input_sp3_clk = arg.pa1 if not arg.pa1 is None else ''
    input_sbas_ionex_fcb = arg.pa2 if not arg.pa2 is None else ''

    match_list = rnx2pos.read_dirs(
        input_rover, input_base, input_nav, input_sp3_clk, input_sbas_ionex_fcb)
    if arg.matchlist:
        pprint('# Match list start #')
        pprint(match_list)
        pprint('# Match list end #')

    timeint = int(arg.timeint) if not arg.timeint is None else 0
    pos_paths = rnx2pos.start(match_list, arg.rtklib,
                              arg.conf, arg.output, timeint)
    if arg.poslist:
        pprint('# Pos list start #')
        pprint(pos_paths)
        pprint('# Pos list end #')
