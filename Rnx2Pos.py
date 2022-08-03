from typing import List
from pprint import pprint


class Rnx2Pos:
    def __init__(self) -> None:
        self.match_list = dict()
        self.errors_match_list = dict()
        self.pos_paths = dict()

    def read_dirs(self, input_rover: str, input_base: str = '', input_nav: str = '', input_sp3_clk: str = '', input_sbas_ionex_fcb: str = '') -> dict:
        if not isinstance(input_rover, str):
            raise TypeError(
                "The type of the 'input_rover' variable should be 'str'")
        elif not isinstance(input_base, str):
            raise TypeError(
                "The type of the 'input_base' variable should be 'str'")
        elif not isinstance(input_nav, str):
            raise TypeError(
                "The type of the 'input_nav' variable should be 'str'")
        elif not isinstance(input_sp3_clk, str):
            raise TypeError(
                "The type of the 'input_sp3_clk' variable should be 'str'")
        elif not isinstance(input_sbas_ionex_fcb, str):
            raise TypeError(
                "The type of the 'input_sbas_ionex_fcb' variable should be 'str'")

    def read_list(self, input_rover: List[str], input_base: List[str] = [], input_nav: List[str] = [], input_sp3_clk: List[str] = [], input_sbas_ionex_fcb: List[str] = []) -> dict:
        if not isinstance(input_rover, list):
            raise TypeError(
                "The type of the 'input_rover' variable should be 'list'")
        elif not isinstance(input_base, list):
            raise TypeError(
                "The type of the 'input_base' variable should be 'list'")
        elif not isinstance(input_nav, list):
            raise TypeError(
                "The type of the 'input_nav' variable should be 'list'")
        elif not isinstance(input_sp3_clk, list):
            raise TypeError(
                "The type of the 'input_sp3_clk' variable should be 'list'")
        elif not isinstance(input_sbas_ionex_fcb, list):
            raise TypeError(
                "The type of the 'input_sbas_ionex_fcb' variable should be 'list'")

        for file in input_rover + input_base:
            flag_notFound = True
            with open(file, 'r') as f:
                text = f.readlines()[0:30]
                for item in text:
                    if 'TIME OF FIRST OBS' in item:
                        date = '/'.join(item.split()[:3])
                        if not self.pos_paths.get(date) == None:
                            self.pos_paths[date] += [file]
                        else:
                            self.pos_paths[date] = [file]
                        flag_notFound = False
                        break

            if flag_notFound:
                self.errors_match_list[file] = 'Not found row "TIME OF FIRST OBS"'

        return self.pos_paths, self.errors_match_list

    def start(self, path_rtklib, rtklib_conf, output_path, start_time='', end_time='', timeint=''):
        pass


if __name__ == "__main__":
    input_rover = ['/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0010.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0020.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0030.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0040.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0050.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0060.22o',
                   '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0070.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0080.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0090.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0100.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0110.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/novm0120.22o']
    input_base = ['/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10020.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10030.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10040.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10050.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10060.22o',
                  '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10070.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10080.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10090.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10110.22o', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10120.22o']
    input_nav = ['/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10020.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10030.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10040.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10050.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10060.22n',
                 '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10070.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10080.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10090.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10110.22n', '/home/danisimo/Desktop/MonCenterWeb/FilesUsers/danisimo/postprocessing/nsk10120.22n']
    a = Rnx2Pos()
    pprint(a.read_list(input_rover, input_base, input_nav))
    a.read_dirs()
