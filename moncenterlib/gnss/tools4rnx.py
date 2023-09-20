import os
from typing import Any
from progress.bar import IncrementalBar
from pathlib import Path


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
        if not type(arg) is type_check:
            raise TypeError(f"The type of the '{name}' variable should be {type_check}")

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

    def scan_dir(self, input: str, recursion: bool = False) -> list:
        self.__check_type(recursion, bool, 'recursion')
        self.__check_type(input, str, 'input')
        
        input_files = []
        if os.path.isdir(input):
            # составляем список файлов из папки
            if recursion:
                for root, _, files in os.walk(input):
                    for file in files:
                        path = os.path.join(root, file)
                        input_files.append(path)
            else:
                temp_lst = []
                for file in os.listdir(input):
                    if os.path.isfile(os.path.join(input, file)):
                        temp_lst.append(os.path.join(input, file))
                input_files = temp_lst
        else:
            raise Exception("Path to dir is strange.")
        
        return input_files

    def start(self, input: Any, output: str, config: dict) -> dict:

        # check type
        #self.__check_type(input, str, 'input')
        self.__check_type(output, str, 'output')
        self.__check_type(config, dict, 'config')
        
        for k, v in config.items():
            self.__check_type(v, str, k)

        input_files = []
        if type(input) == list:
            input_files = input
        elif type(input) == str:
            if os.path.isfile(input):
                input_files = [input]
            else:
                raise Exception("Path to file is strange.")
        else:
            raise TypeError(f"The type of the 'input' variable should be 'str' or 'list'.")

        # запуск конвертации
        output_files = []
        bar = IncrementalBar('Progress',
                             max=len(input_files),
                             suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
        bar.start()
        for file in input_files:

            command = ''

            command += f"-r {config['format']} "
            command += f"-v {config['rinex_v']} "

            if not config['start_time'] == '':
                command += f"-ts {config['start_time']} "

            if not config['end_time'] == '':
                command += f"-te {config['end_time']} "

            command += f"-ti {config['interval']} "

            command += f"-f {config['freq']} "

            full_sys = {'G', 'R', 'E', 'J', 'S', 'C', 'I'}
            sys = set(config['system'].split(','))
            for i in full_sys - sys:
                command += f"-y {i} "

            namef = os.path.basename(file)
            if not Path(namef).suffix == '':
                namef = namef.rsplit(Path(namef).suffix, 1)[0]

            type_files = ['o', 'n', 'g', 'h', 'q', 'l', 'b', 'i', 's']
            for t in type_files:
                if config[f'output_{t}'] == '1':
                    temp_path = os.path.join(output, f"{namef}.{t}")
                    command += f"-{t} '{temp_path}' "
                    output_files.append(os.path.join(output, f"{namef}.{t}"))

            other_type = ['od', 'os', 'oi', 'ot', 'ol', 'halfc']
            for t in other_type:
                if config[f'other_{t}'] == '1':
                    command += f"-{t} "

            command += f"-hc '{config['comment']}' "

            command += f"-hm '{config['marker_name']}' "
            command += f"-hn '{config['marker_number']}' "
            command += f"-ht '{config['marker_type']}' "

            command += f"-ho '{config['about_name']}/{config['about_agency']}' "
            command += f"-hr '{config['receiver_number']}/{config['receiver_type']}/{config['receiver_version']}' "
            command += f"-ha '{config['antenna_number']}/{config['antenna_type']}' "
            command += f"-hp '{config['approx_position_x']}/{config['approx_position_y']}/{config['approx_position_z']}' "
            command += f"-hd '{config['antenna_delta_h']}/{config['antenna_delta_e']}/{config['antenna_delta_n']}' "

            command += f"'{file}'"

            cmd = str(Path(__file__).resolve().parent.parent.parent)
            cmd += "/bin/RTKLIB-2.4.3-b34/app/consapp/convbin/gcc/convbin "
            cmd += command
            #print(cmd)
            os.system(cmd)

            bar.next()
            # переименование файлов по стандарту ринекса, впланах

        bar.finish()
        return self.__check_files(output_files)
