"""
A module for manipulating RINEX files.
- Converting raw satellite receiver data into a universal RINEX format;
- Soon (e.g. merge, cut rinex files).

The module has the following classes:
- RtkLibConvbin;
- Soon.

Learn more about the specific class.
"""

import datetime
import os
import subprocess
from pathlib import Path
from progress.bar import IncrementalBar
from pydantic import validate_call
from moncenterlib.gnss.tools import files_check, get_system_info


class RtkLibConvbin:
    """
    This class is based on the RTKLib software package.
    See more about RTKLIB here: https://rtklib.com/
    See code usage examples in the examples folder
    """

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

    def get_default_config(self) -> dict:
        """
        Return variable __default_config. Default config isn't editable.
        In the future, you will manually configure this config and send it to the start method.
        See documentation RTKLIB, how to configuration.

        Returns:
            dict: default config for convbin of RTKLib
        """
        return self.__default_config.copy()

    @validate_call
    def scan_dir(self, input_dir: str, recursion: bool = False) -> list[str]:
        """This method scans the directory and makes a list of files for further work of the class.
        The method can also recursively search for files.

        Args:
            input_dir (str): Path to the directory.
            recursion (bool, optional): Recursively search for files. Defaults to False.

        Raises:
            ValueError: Path to dir is strange.

        Returns:
            list[str]: List of files.

        Examples:
            >>> t4r = RtkLibConvib()
            >>> res = t4r.scan_dir("/some_path_to_dir", True)
            >>> res
            ["file_1", "file_2"]
        """
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

    def __check_config(self, config: dict):
        format_raw = ["rtcm2", "rtcm3", "nov", "oem3", "ubx", "ss2",
                      "hemis", "stq", "javad", "nvs", "binex", "rt17", "sbf", "rinex"]
        rinex_v = ["3.04", "3.03", "3.02", "3.01", "3.00", "2.12", "2.11", "2.10"]
        output_type = ["o", "n", "g", "h", "q", "l", "b", "i", "s"]
        other_type = ['od', 'os', 'oi', 'ot', 'ol', 'halfc']
        full_sys = ['G', 'R', 'E', 'J', 'S', 'C', 'I']

        if len(config) == 0:
            raise ValueError("Config is empty.")

        for key, val in config.items():
            if not isinstance(key, str):
                raise TypeError(f"Config. Key '{key}' must be str.")

            if not isinstance(val, str):
                raise TypeError(f"Config. Value '{val}' of key '{key}' must be str.")

        for key in self.__default_config.keys():
            if key not in config:
                raise Exception(f"Config. Not found key '{key}'.")

        if config['format'] not in format_raw:
            raise ValueError(f"Config. Key: format. Unknown format '{config['format']}'.")

        if config['rinex_v'] not in rinex_v:
            raise ValueError(f"Config. Key: rinex_v. Unknown rinex version '{config['rinex_v']}'.")

        if config['start_time'] != '':
            try:
                datetime.datetime.strptime(config['start_time'], "%Y/%m/%d %H:%M:%S")
            except ValueError:
                raise ValueError(
                    f"Config. Key: start_time. Incorrect data format {config['start_time']}, should be YYYY/MM/DD HH:MM:SS.")
        if config['end_time'] != '':
            try:
                datetime.datetime.strptime(config['end_time'], "%Y/%m/%d %H:%M:%S")
            except ValueError:
                raise ValueError(
                    f"Config. Key: end_time. Incorrect data format {config['end_time']}, should be YYYY/MM/DD HH:MM:SS.")

        if float(config['interval']) < 0:
            raise ValueError(f"Config. Key: interval. Interval {config['interval']} must be >= 0.")

        if not (0 <= int(config['freq']) <= 127):
            raise ValueError(f"Config. Key: freq. Freq {config['freq']} must be 0 <= freq <= 127.")

        systems = config['system'].split(",")
        for s in systems:
            if s not in full_sys:
                raise ValueError(f"Config. Key: system. Unknown system '{s}'.")

        for t in output_type:
            if config[f'output_{t}'] not in ["0", "1"]:
                raise ValueError(f"Config. Key: {f'output_{t}'}. Unknown value '{config[f'output_{t}']}'.")

        for t in other_type:
            if config[f'other_{t}'] not in ["0", "1"]:
                raise ValueError(f"Config. Key: {f'other_{t}'}. Unknown value '{config[f'other_{t}']}'.")

    @validate_call
    def start(self, input_raw: str | list, output: str, config: dict,
              recursion: bool = False, show_progress: bool = True) -> dict:
        """The method starts the process of preserving files in the RINEX format.

        Args:
            input_raw (str | list): The input method can accept a path of up to one file.
                                    The path to the directory where several files are stored.
                                    As well as a list of files generated by the scan_dirs method.

            output (str): The path to the directory where the files will be saved.

            config (dict): Dictionary with configuration.
                           You can get the configuration by calling the get_default_config() method.

            recursion (bool, optional): When you put path to directory, you can use recursively search for files.
                                        Defaults to False.

            show_progress (bool, optional): The progress bar is displayed. Defaults to True.

        Raises:
            ValueError: Path to file or dir is strange.
            TypeError: The type of the 'input_raw' variable should be 'str' or 'list'.
            ValueError: Path to output dir is strange.

        Returns:
            dict: The dictionary contains 2 keys. Done and error.
            The done key stores a list of files that have been successfully created.
            The error key stores a list of files that have not been created.

        Examples:
            >>> t4r = RtkLibConvib()
            >>> list_files = t4r.scan_dir("/some_path_to_dir", True)
            >>> config = t4r.get_default_config()
            >>> config["format"] = "ubx"
            >>> res = t4r.start(list_files, "/some_output_dir", config, False, True)
            >>> res
            {
                'done': ["file_1", "file_2"],
                'error': ["file_3"]
            }
        """
        self.__check_config(config)

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
            raise TypeError("The type of the 'input_raw' variable should be 'str' or 'list'.")

        if not os.path.isdir(output):
            raise ValueError("Path to output dir is strange.")

        # запуск конвертации
        inc_bar = IncrementalBar('Progress convbin', max=len(input_files),
                                 suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
        if not show_progress:
            def nothing():
                pass
            inc_bar.start = nothing
            inc_bar.next = nothing
            inc_bar.finish = nothing

        inc_bar.start()
        output_files = []
        for file in input_files:
            cmd = []
            path_convbin = ""

            if get_system_info()[1] == "x86_64":
                path_convbin = Path(__file__).resolve().parent.joinpath(
                    "bin", "x86_64", "convbin_2.4.3-34_x86_64_linux")
            elif get_system_info()[1] == "aarch64":
                path_convbin = Path(__file__).resolve().parent.joinpath(
                    "bin", "aarch64", "convbin_2.4.3-34_aarch64_linux")
            else:
                raise OSError(f"{get_system_info()} doesn't support")

            cmd += [str(path_convbin)]

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
            final_sys = list(full_sys - sys)
            final_sys.sort()
            for i in final_sys:
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
            cmd += ["-hr", f"{config['receiver_number']}/{config['receiver_type']}/{config['receiver_version']}"]
            cmd += ["-ha", f"{config['antenna_number']}/{config['antenna_type']}"]
            cmd += ["-hp", f"{config['approx_position_x']}/{config['approx_position_y']}/{config['approx_position_z']}"]
            cmd += ["-hd", f"{config['antenna_delta_h']}/{config['antenna_delta_e']}/{config['antenna_delta_n']}"]

            cmd += [file]

            subprocess.run(cmd, stderr=subprocess.DEVNULL, check=False)

            inc_bar.next()

        inc_bar.finish()
        return files_check(output_files)
