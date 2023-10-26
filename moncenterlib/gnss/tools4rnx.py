import os
import subprocess
# from typing import Any
from pathlib import Path
from progress.bar import IncrementalBar


class RtkLibConvbin:
    def __init__(self):
        self.__default_config = {
            'format': 'rtcm2',
            'rinex_v': '3.04',
            'start_time': '',
            'end_time': '',
            'interval': '0',
            'freq': '3',
            'system': 'G,R,E,J,S,C,I',
            'output_o': '1',
            'output_n': '1',
            'output_g': '0',
            'output_h': '0',
            'output_q': '0',
            'output_l': '0',
            'output_b': '0',
            'output_i': '0',
            'output_s': '0',
            'other_od': '1',
            'other_os': '1',
            'other_oi': '0',
            'other_ot': '0',
            'other_ol': '0',
            'other_halfc': '0',
            'comment': '',
            'marker_name': '',
            'marker_number': '',
            'marker_type': '',
            'about_name': '',
            'about_agency': '',
            'receiver_number': '',
            'receiver_type': '',
            'receiver_version': '',
            'antenna_number': '',
            'antenna_type': '',
            'approx_position_x': '',
            'approx_position_y': '',
            'approx_position_z': '',
            'antenna_delta_h': '',
            'antenna_delta_e': '',
            'antenna_delta_n': ''
        }

    @property
    def DEFAULT_CONFIG(self):
        return self.__default_config.copy()

    def __check_type(self, arg: object, type_check: object, name: str) -> None:
        if not isinstance(arg, type_check):
            raise TypeError(
                f"The type of the '{name}' variable should be {type_check}")

    def __check_files(self, files: list) -> dict:
        output_check = {
            'done': [],
            'error': []
        }

        for file in files:
            direct = Path(file)
            if direct.exists():
                output_check['done'].append(file)
            else:
                output_check['error'].append(file)

        return output_check

    def scan_dir(self, input_dir: str, recursion: bool = False) -> list:
        self.__check_type(recursion, bool, 'recursion')
        self.__check_type(input_dir, str, 'input')

        input_files = []
        if os.path.isdir(input_dir):
            if recursion:
                for root, _, files in os.walk(input_dir):
                    for file in files:
                        path = os.path.join(root, file)
                        input_files.append(path)
            else:
                temp_lst = []
                for file in os.listdir(input_dir):
                    if os.path.isfile(os.path.join(input_dir, file)):
                        temp_lst.append(os.path.join(input_dir, file))
                input_files = temp_lst
        else:
            raise ValueError("Path to dir is strange.")

        return input_files

    def start(self, input_raw: str | list, output: str, config: dict,
              recursion: bool = False, show_progress: bool = True) -> dict:

        # check type
        self.__check_type(output, str, 'output')
        self.__check_type(config, dict, 'config')

        for k, v in config.items():
            self.__check_type(v, str, k)

        input_files = []
        if isinstance(input_raw, list):
            input_files = input_raw
        elif isinstance(input_raw, str):
            if os.path.isfile(input_raw):
                input_files = [input_raw]
            elif os.path.isdir(input_raw):
                input_files = self.scan_dir(input_raw, recursion)
            else:
                raise ValueError("Path to file or dir is strange.")
        else:
            raise TypeError(
                "The type of the 'input_raw' variable should be 'str' or 'list'.")

        # запуск конвертации
        inc_bar = IncrementalBar('Progress convbin',
                                 max=len(input_files),
                                 suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
        if not show_progress:
            def nothing():
                pass
            inc_bar.start = nothing
            inc_bar.next = nothing
            inc_bar.finish = nothing

        inc_bar.start()
        output_files = []
        cmd = []
        for file in input_files:
            path_convbin = str(Path(__file__).resolve().parent.parent.parent)
            path_convbin += "/bin/RTKLIB-2.4.3-b34/app/consapp/convbin/gcc/convbin"
            cmd += [path_convbin]

            cmd += ["-r", config['format']]
            cmd += ["-v", config['rinex_v']]

            if not config['start_time'] == '':
                cmd += ["-ts", config['start_time']]

            if not config['end_time'] == '':
                cmd += ["-te", config['end_time']]

            cmd += ["-ti", config['interval']]
            cmd += ["-f", config['freq']]

            full_sys = {'G', 'R', 'E', 'J', 'S', 'C', 'I'}
            sys = set(config['system'].split(','))
            for i in full_sys - sys:
                cmd += ["-y", i]

            namef = os.path.basename(file)
            if Path(namef).suffix != '':
                namef = namef.rsplit(Path(namef).suffix, 1)[0]

            type_files = ['o', 'n', 'g', 'h', 'q', 'l', 'b', 'i', 's']
            for t in type_files:
                if config[f'output_{t}'] == '1':
                    temp_path = os.path.join(output, f"{namef}.{t}")
                    cmd += [f"-{t}", temp_path]
                    output_files.append(os.path.join(output, f"{namef}.{t}"))

            other_type = ['od', 'os', 'oi', 'ot', 'ol', 'halfc']
            for t in other_type:
                if config[f'other_{t}'] == '1':
                    cmd += [f"-{t}"]

            cmd += ["-hc", config['comment']]

            cmd += ["-hm", config['marker_name']]
            cmd += ["-hn", config['marker_number']]
            cmd += ["-ht", config['marker_type']]

            cmd += ["-ho", f"{config['about_name']}/{config['about_agency']}"]
            cmd += ["-hr",
                    f"{config['receiver_number']}/{config['receiver_type']}/{config['receiver_version']}"]
            cmd += ["-ha",
                    f"{config['antenna_number']}/{config['antenna_type']}"]
            cmd += ["-hp", f"{config['approx_position_x']}/{config['approx_position_y']}/{config['approx_position_z']}"]
            cmd += ["-hd",
                    f"{config['antenna_delta_h']}/{config['antenna_delta_e']}/{config['antenna_delta_n']}"]

            cmd += [file]

            subprocess.run(cmd, stderr=subprocess.DEVNULL, check=False)

            inc_bar.next()

        inc_bar.finish()
        return self.__check_files(output_files)
