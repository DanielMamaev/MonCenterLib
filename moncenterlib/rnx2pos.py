import argparse
from typing import List
from pprint import pprint
import os
import sys


class Rnx2Pos:
    '''
    Rnx2Pos inputs the standard RINEX observation data and navigation message
    files (GPS, GLONASS, Galileo, QZSS,
    BeiDou and SBAS) and can computers the positioning solutions by various 
    positioning modes including
    Single‐point, DGPS/DGNSS, Kinematic, Static, PPP‐Kinematic and PPP‐Static.
    The module can accept one or more files. 
    Thanks to this functionality, it becomes possible to process a large 
    number of files with the same settings.

    '''

    def __init__(self) -> None:
        self.__kol_inputs = 0

    def read_dirs(self, input_rover: str, input_base: str = '',
                  input_nav: str = '', input_sp3: str = '',
                  input_clk: str = '', input_ionex: str = '') -> dict:
        '''
        This method reads files from the specified folders and creates
        dictionary. The dictionary in which the files were filtered by dates
        is returned.
        Input SBAS and FCB are in development.

        Args:
            input_rover: The path to the folder with the files of the
                rover station.
            input_base (optional): The path to the folder with the files
                of the base station. Defaults to ''
            input_nav (optional): The path to the folder with ephemeris files.
                Defaults to ''
            input_sp3 (optional): The path to the folder with the Precise
                ephemeris or Clock files. Defaults to ''
            input_clk (optional): The path to the folder with the
                Clock files. Defaults to ''
            input_ionex (optional): The path to the folder with the
                IONEX files. Defaults to ''

        Returns:
            The dictionary in which the files were filtered by dates is returned.

        Raises:
            TypeError: Occurs if an incorrect data type was passed in the argument.

        Examples:
            >>> rnx2pos = Rnx2Pos()
            >>> print(rnx2pos.read_dirs('/home_dir/NOVM/', input_nav='/home_dir/eph/'))
            {
            '2022/1/11': ['/home_dir/NOVM/novm0110.22o', '/home_dir/eph/nsk10110.22n'],
            '2022/1/12': ['/home_dir/NOVM/novm0120.22o', '/home_dir/eph/nsk10120.22n']
            }
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
        elif not type(input_sp3) is str:
            raise TypeError(
                "The type of the 'input_sp3' variable should be 'str'")
        elif not type(input_clk) is str:
            raise TypeError(
                "The type of the 'input_clk' variable should be 'str'")
        elif not type(input_ionex) is str:
            raise TypeError(
                "The type of the 'input_ionex' variable should be 'str'")

        rover_files = list(
            map(lambda x: os.path.join(input_rover, x),
                os.listdir(input_rover))) if input_rover != '' else []

        base_files = list(
            map(lambda x: os.path.join(input_base, x),
                os.listdir(input_base))) if input_base != '' else []

        nav_files = list(map(lambda x: os.path.join(input_nav, x), os.listdir(
            input_nav))) if input_nav != '' else []

        sp3_files = list(
            map(lambda x: os.path.join(input_sp3, x),
                os.listdir(input_sp3))) if input_sp3 != '' else []

        clk_files = list(
            map(lambda x: os.path.join(input_clk, x),
                os.listdir(input_clk))) if input_clk != '' else []

        ionex_files = list(
            map(lambda x: os.path.join(input_ionex, x),
                os.listdir(input_ionex))) if input_ionex != '' else []

        return self.read_list(rover_files, base_files, nav_files,
                              sp3_files, clk_files, ionex_files)

    def read_list(self, input_rover: List[str], input_base: List[str] = [],
                  input_nav: List[str] = [], input_sp3: List[str] = [],
                  input_clk: List[str] = [],
                  input_ionex: List[str] = []) -> dict:
        """
        This method reads lists containing paths to files and forms
        a match_list dictionary from them. Input SBAS and FCB are
        in development.

        Args:
            input_rover: A list containing the paths to the files
                rover station.
            input_base (optional): A list containing the paths to the files.
                base station. Defaults to [].
            input_nav (optional): A list containing the paths to the
                files ephemeris. Defaults to [].
            input_sp3 (optional): A list containing the paths to the files
                precise ephemeris. Defaults to [].
            input_clk (optional): A list containing the paths to the files
                Clock. Defaults to [].
            input_sbas_ionex_fcb (optional): A list containing the paths
                to the IONEX files. Defaults to [].

        Raises:
            TypeError: Occurs if an incorrect data type was passed in the argument.

        Returns:
            The dictionary in which the files were filtered by dates is returned.

        Examples:
            >>> rnx2pos = Rnx2Pos()
            >>> rover_list = ['/home_dir/NOVM/novm0110.22o', '/home_dir/NOVM/novm0120.22o']
            >>> nav_list = ['/home_dir/eph/nsk10110.22n', '/home_dir/eph/nsk10120.22n']
            >>> print(rnx2pos.read_list(rover_list, input_nav=nav_list))
            {
            '2022/1/11': ['/home_dir/NOVM/novm0110.22o', '/home_dir/eph/nsk10110.22n'],
            '2022/1/12': ['/home_dir/NOVM/novm0120.22o', '/home_dir/eph/nsk10120.22n']
            }
        """

        if not type(input_rover) is list:
            raise TypeError(
                "The type of the 'input_rover' variable should be 'list'")
        elif not type(input_base) is list:
            raise TypeError(
                "The type of the 'input_base' variable should be 'list'")
        elif not type(input_nav) is list:
            raise TypeError(
                "The type of the 'input_nav' variable should be 'list'")
        elif not type(input_sp3) is list:
            raise TypeError(
                "The type of the 'input_sp3' variable should be 'list'")
        elif not type(input_clk) is list:
            raise TypeError(
                "The type of the 'input_sp3' variable should be 'list'")
        elif not type(input_ionex) is list:
            raise TypeError(
                "The type of the 'input_ionex' variable should be 'list'")

        # узнаем кол-во списков
        self.__kol_inputs = 0
        if not input_rover == []:
            self.__kol_inputs += 1
        if not input_base == []:
            self.__kol_inputs += 1
        if not input_nav == []:
            self.__kol_inputs += 1
        if not input_sp3 == []:
            self.__kol_inputs += 1
        if not input_clk == []:
            self.__kol_inputs += 1
        if not input_ionex == []:
            self.__kol_inputs += 1

        match_list = dict()

        for file in input_rover + input_base:
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'TIME OF FIRST OBS' in line:
                        date = line.split()[:3]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date = '/'.join(date)
                        if date in match_list:
                            match_list[date] += [file]
                        else:
                            match_list[date] = [file]
                        break
                    elif 'END OF HEADER' in line:
                        break

        for file in input_nav:
            flag_end = False
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'END OF HEADER' in line:
                        flag_end = True
                    elif flag_end:
                        date = line.split()[1:4]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date[0] = '20' + \
                            date[0] if not len(date[0]) == 4 else date[0]
                        date = '/'.join(date)
                        if date in match_list:
                            match_list[date] += [file]
                        else:
                            match_list[date] = [file]
                        break

        for file in input_sp3:
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if line[0] == "*":
                        date = line.split()[1:4]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date[0] = '20' + \
                            date[0] if not len(date[0]) == 4 else date[0]
                        date = '/'.join(date)
                        if date in match_list:
                            match_list[date] += [file]
                        else:
                            match_list[date] = [file]
                        break
        
        for file in input_clk:
            flag_end = False
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'END OF HEADER' in line:
                        flag_end = True
                    elif flag_end:
                        date = line.split()[2:5]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date[0] = '20' + \
                            date[0] if not len(date[0]) == 4 else date[0]
                        date = '/'.join(date)
                        if date in match_list:
                            match_list[date] += [file]
                        else:
                            match_list[date] = [file]
                        break
        # sbas_fcb

        return match_list

    def start(self, match_list: dict, path_rnx2rtkp: str, rnx2rtkp_conf: str,
              output_dir: str, timeint: int = 0):
        """
        This method starts the post-processing process.
        The output generates a list with paths to the generated .pos files.

        Args:
            match_list: The dictionary is formed from the read_dirs or read_list method.
            path_rnx2rtkp: The path to the rnx2rtkp executable.
            rnx2rtkp_conf: The path to rnx2rtkp config.
            output_dir: The path to the output folder.
            timeint:  Time interval (seconds). Defaults to ''.

        Raises:
            TypeError: Occurs if an incorrect data type was passed in the argument.

        Returns:
            The tuple returns. The first element contains a list that
            specifies the paths to .pos files. The second element contains
            a dictionary in which errors are displayed.

        Examples:
            >>> rnx2pos = Rnx2Pos()
            >>> match_list = rnx2pos.read_dirs('/home_dir/NOVM/', input_base='/home_dir/NSK1/', input_nav='/home_dir/eph/'))
            >>> print(rnx2pos.start(match_list, '/home_dir/rnx2rtkp', '/home_dir/rnx2rtkp.conf', '/home_dir/output/', timeint=30))
            (
                ['home_dir/output/novm0040.22o.pos', 'home_dir/output/novm0090.22o.pos'],
                {
                '2022/1/1': [['/home_dir/NOVM/novm0010.22o'], 'Not enough files'],
                '2022/1/10': [['/home_dir/NOVM/novm0100.22o'], 'Not enough files']
                }
            )
        """

        if not type(path_rnx2rtkp) is str:
            raise TypeError(
                "The type of the 'path_rnx2rtkp' variable should be 'str'")
        elif not type(rnx2rtkp_conf) is str:
            raise TypeError(
                "The type of the 'rnx2rtkp_conf' variable should be 'str'")
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
                command = f"'{path_rnx2rtkp}' "
                command += f'-ti {timeint} ' if timeint != '' else ''
                command += f"-k '{rnx2rtkp_conf}' "
                for path_file in value:
                    command += f"'{path_file}'" + ' '
                command += f"-o '{os.path.join(output_dir, os.path.basename(value[0]))}.pos'"
                pos_paths.append(
                    f"{os.path.join(output_dir, os.path.basename(value[0]))}.pos")
                #print(command)
                os.system(command)
            else:
                error_list[key] = [value, "Not enough files"]
        return pos_paths, error_list


if __name__ == "__main__":
    des = '''
    Rnx2Pos inputs the standard RINEX observation data and navigation message
    files (GPS, GLONASS, Galileo, QZSS, BeiDou and SBAS) and can computers the
    positioning solutions by various positioning modes including Single‐point,
    DGPS/DGNSS, Kinematic, Static, PPP‐Kinematic and PPP‐Static.
    The module can accept one or more files.The module can accept one
    or more files.
    Thanks to this functionality, it becomes possible to process a large
    number of files with the same settings.
    Input SBAS and FCB are in development.
    '''
    parser = argparse.ArgumentParser(description=des)
    parser.add_argument('-e', '--rnx2rtkp', type=str,
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
    parser.add_argument('-pp', '--psp3', type=str,
                        help='Specify the path to the folder with the Precise ephemeris. Types: .sp3')
    parser.add_argument('-pc', '--pclk', type=str,
                        help='Specify the path to the folder with the Clock files. Types: .clk*')
    parser.add_argument('-pi', '--pionex', type=str,
                        help='Specify the path to the folder with the IONEX files. Types: .*i, .ionex')
    parser.add_argument('-t', '--timeint', type=str, help='Interval (s)')
    parser.add_argument('-ml', '--matchlist',
                        action='store_true', help='Show match list')
    parser.add_argument('-p', '--poslist', action='store_true',
                        help='Show paths to generated .pos files')
    arg = parser.parse_args()

    if arg.rnx2rtkp is None:
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
    input_rover = arg.prover if arg.prover is not None else ''
    input_base = arg.pbase if arg.pbase is not None else ''
    input_nav = arg.pnav if arg.pnav is not None else ''
    input_sp3 = arg.psp3 if arg.psp3 is not None else ''
    input_clk = arg.pclk if arg.pclk is not None else ''
    input_ionex = arg.pionex if arg.pionex is not None else ''

    match_list = rnx2pos.read_dirs(
        input_rover,
        input_base,
        input_nav,
        input_sp3,
        input_clk,
        input_ionex)

    if arg.matchlist:
        pprint('# Match list start #')
        pprint(match_list)
        pprint('# Match list end #')

    timeint = int(arg.timeint) if arg.timeint is not None else 0
    pos_paths = rnx2pos.start(match_list, arg.rnx2rtkp,
                              arg.conf, arg.output, timeint)
    if arg.poslist:
        pprint('# Pos list start #')
        pprint(pos_paths)
        pprint('# Pos list end #')
