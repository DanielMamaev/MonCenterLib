"""
A module for manipulating RINEX files.
- Converting raw satellite receiver data into a universal RINEX format;
- Soon (e.g. merge, cut rinex files).

The module has the following classes:
- RtkLibConvbin;
- Soon.

Learn more about the specific class.
"""

from collections import defaultdict
import datetime
from logging import Logger
import os
import queue
import subprocess
from pathlib import Path
import threading
from typeguard import typechecked
from moncenterlib.tools import create_simple_logger, get_files_from_dir, get_path2bin


class RtkLibConvbin:
    """
    This class is based on the RTKLib software package.
    Convert RTCM, receiver raw data log and RINEX file to RINEX and SBAS/LEX
    message file. SBAS message file complies with RTKLIB SBAS/LEX message
    format.
    See more about RTKLIB here: https://rtklib.com/
    This class can convert one or more files.
    See code usage examples in the examples folder.
    """
    @typechecked
    def __init__(self, workers: int = 1, logger: bool | Logger | None = None):
        """
        Args:
            workers (int): The number of parallel processes. It reduces the processing time for multiple files.
                Defaults to 1.
            logger (bool | Logger, optional): if the logger is None, a logger will be created inside the default class.
                If the logger is False, then no information will be output.
                If you pass an instance of your logger, the information output will be implemented according to your logger.
                Defaults to None.
        """
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

        self.logger = logger

        if self.logger in [None, False]:
            self.logger = create_simple_logger("RtkLibConvbin", logger)

        self.workers = workers
        self.semaphore = threading.Semaphore(self.workers)

        self.__create_vars()

    def __create_vars(self):
        self.__process = defaultdict(None)

        def def_dict(): return {
            'stdout': [],
            'stderr': []
        }
        self.std_log = defaultdict(def_dict)
        self.output_files = defaultdict(list)

    def __check_config(self, config: dict):
        format_raw = ["rtcm2", "rtcm3", "nov", "oem3", "ubx", "ss2",
                      "hemis", "stq", "javad", "nvs", "binex", "rt17", "sbf", "rinex"]
        rinex_v = ["3.04", "3.03", "3.02", "3.01", "3.00", "2.12", "2.11", "2.10"]
        output_type = ["o", "n", "g", "h", "q", "l", "b", "i", "s"]
        other_type = ['od', 'os', 'oi', 'ot', 'ol', 'halfc']
        full_sys = ['G', 'R', 'E', 'J', 'S', 'C', 'I']

        if len(config) == 0:
            self.logger.error("Config is empty.")
            raise ValueError("Config is empty.")

        for key, val in config.items():
            if not isinstance(key, str):
                self.logger.error("Config. Key '%s' must be str.", key)
                raise TypeError(f"Config. Key '{key}' must be str.")

            if not isinstance(val, str):
                self.logger.error("Config. Value '%s' of key '%s' must be str.", val, key)
                raise TypeError(f"Config. Value '{val}' of key '{key}' must be str.")

        for key in self.__default_config.keys():
            if key not in config:
                self.logger.error("Config. Not found key '%s'.", key)
                raise Exception(f"Config. Not found key '{key}'.")

        if config['format'] not in format_raw:
            self.logger.error("Config. Key: format. Unknown format '%s'.", config['format'])
            raise ValueError(f"Config. Key: format. Unknown format '{config['format']}'.")

        if config['rinex_v'] not in rinex_v:
            self.logger.error("Config. Key: rinex_v. Unknown rinex version '%s'.", config['rinex_v'])
            raise ValueError(f"Config. Key: rinex_v. Unknown rinex version '{config['rinex_v']}'.")

        if config['start_time'] != '':
            try:
                datetime.datetime.strptime(config['start_time'], "%Y/%m/%d %H:%M:%S")
            except ValueError:
                self.logger.error(
                    "Config. Key: start_time. Incorrect data format %s, should be YYYY/MM/DD HH:MM:SS.", config['start_time'])
                raise ValueError(
                    f"Config. Key: start_time. Incorrect data format {config['start_time']}, should be YYYY/MM/DD HH:MM:SS.")
        if config['end_time'] != '':
            try:
                datetime.datetime.strptime(config['end_time'], "%Y/%m/%d %H:%M:%S")
            except ValueError:
                self.logger.error(
                    "Config. Key: end_time. Incorrect data format %s, should be YYYY/MM/DD HH:MM:SS.", config['end_time'])
                raise ValueError(
                    f"Config. Key: end_time. Incorrect data format {config['end_time']}, should be YYYY/MM/DD HH:MM:SS.")

        if float(config['interval']) < 0:
            self.logger.error("Config. Key: interval. Interval %s must be >= 0.", config['interval'])
            raise ValueError(f"Config. Key: interval. Interval {config['interval']} must be >= 0.")

        if not (0 <= int(config['freq']) <= 127):
            self.logger.error("Config. Key: freq. Freq %s must be 0 <= freq <= 127.", config['freq'])
            raise ValueError(f"Config. Key: freq. Freq {config['freq']} must be 0 <= freq <= 127.")

        systems = config['system'].split(",")
        for s in systems:
            if s not in full_sys:
                self.logger.error("Config. Key: system. Unknown system '%s'.", s)
                raise ValueError(f"Config. Key: system. Unknown system '{s}'.")

        for t in output_type:
            if config[f'output_{t}'] not in ["0", "1"]:
                self.logger.error("Config. Key: {f'output_%s'}. Unknown value '%s'.", t, config[f'output_{t}'])
                raise ValueError(f"Config. Key: {f'output_{t}'}. Unknown value '{config[f'output_{t}']}'.")

        for t in other_type:
            if config[f'other_{t}'] not in ["0", "1"]:
                self.logger.error("Config. Key: {f'other_%s'}. Unknown value '%s'.", t, config[f'other_{t}'])
                raise ValueError(f"Config. Key: {f'other_{t}'}. Unknown value '{config[f'other_{t}']}'.")

    def __make_config4convbin(self, filename: str, output_dir: str, config: dict, output_filename=""):
        output_files = dict()
        cmd = []

        cmd += [get_path2bin("convbin")]

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

        namef = os.path.basename(filename)
        if Path(namef).suffix != '':
            namef = namef.rsplit(Path(namef).suffix, 1)[0]

        type_files = ['o', 'n', 'g', 'h', 'q', 'l', 'b', 'i', 's']
        for t in type_files:
            if config[f'output_{t}'] == '1':
                if output_filename == "":
                    temp_path = os.path.join(output_dir, f"{namef}.{t}")
                    output_files[t] = os.path.join(output_dir, f"{namef}.{t}")
                else:
                    temp_path = os.path.join(output_dir, output_filename + f".{t}")
                    output_files[t] = os.path.join(output_dir, output_filename + f"{namef.replace('*', '')}.{t}")
                cmd += [f"-{t}", temp_path]

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

        cmd += [filename]

        return cmd, output_files

    def __start_converting(self, cmd: list, wait_process=False):
        filename = cmd[-1]
        self.__process[filename] = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        def read_output(stream, filename):
            for line in stream:
                self.std_log[filename]['stdout'] += [line.strip()]

        def read_error(stream, filename):
            for line in stream:
                self.std_log[filename]['stderr'] += [line.strip()]

        stdout_thread = threading.Thread(target=read_output, args=(self.__process[filename].stdout, filename))
        stderr_thread = threading.Thread(target=read_error, args=(self.__process[filename].stderr, filename))

        stdout_thread.start()
        stderr_thread.start()

        if wait_process:
            self.__process[filename].wait()

        # self.logger.info("Finish converting file %s", cmd[-1])

    def get_default_config(self) -> dict:
        """
        Return variable __default_config. Default config isn't editable.
        In the future, you will manually configure this config and send it to the start method.
        See documentation RTKLIB, how to configuration.

        Returns:
            dict: default config for convbin of RTKLib
        """
        return self.__default_config.copy()

    @typechecked
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
        input_files = get_files_from_dir(input_dir, recursion)

        return input_files

    @typechecked
    def merge_rinex(self,
                    input_dir: str,
                    output_dir: str,
                    output_filename: str,
                    config: dict,
                    wait_process: bool = True):
        """Allows you to combine several RINEX files into one common file.

        Args:
            input_dir (str): Path to the directory. There should definitely be an asterisk at the end of the path.
                For example /input_dir/*
            output_dir (str): Path to the output directory.
            output_filename (str): Name of the output file.
            config (dict): Dictionary with configuration.
                You can get the configuration by calling the get_default_config() method.
            wait_process (bool): If wait_process is set to False, the file merging process is performed in a separate thread.
                The method becomes non-blocking. If wait_process is True, then the process becomes blocking.
                The file merging process is waiting to be completed.

        Examples:
            >>> t4r = RtkLibConvib()
            >>> config = t4r.get_default_config()
            >>> t4r.merge_rinex("/input_dir/*", "/output_dir", "name_file", config, True)
            >>> print(t4r.output_files)
        """

        self.logger.info("Start merging files")

        self.__check_config(config)
        self.__create_vars()

        cmd, output_files = self.__make_config4convbin(input_dir, output_dir, config, output_filename)
        for type_file, filename in output_files.items():
            self.output_files[type_file].append(filename)

        self.__start_converting(cmd, wait_process)

    @typechecked
    def start(self,
              input_raw: str | list,
              output: str,
              config: dict,
              recursion: bool = False):
        """The method starts the process of preserving files in the RINEX format.This method is non-blocking.
        You can use an endless loop to wait for the process to complete. See the usage example.

        Args:
            input_raw (str | list): The input method can accept a path of up to one file.
                                    The path to the directory where several files are stored.
                                    As well as a list of files generated by the scan_dirs method.

            output (str): The path to the directory where the files will be saved.

            config (dict): Dictionary with configuration.
                           You can get the configuration by calling the get_default_config() method.

            recursion (bool, optional): When you put path to directory, you can use recursively search for files.
                                        Defaults to False.

        Raises:
            ValueError: Path to file or dir is strange.
            TypeError: The type of the 'input_raw' variable should be 'str' or 'list'.
            ValueError: Path to output dir is strange.

        Examples:
            >>> t4r = RtkLibConvib()
            >>> list_files = t4r.scan_dir("/some_path_to_dir", True)
            >>> config = t4r.get_default_config()
            >>> t4r.start(list_files, "/some_output_dir", config, True)
            >>> while True:
            ...     time.sleep(1)
            ...     status = t4r.get_last_status()
            ...     print(status)
            ...     states = [s['isStop'] for s in status.values()]
            ...     if all(states):
            ...         break
            >>> print(t4r.output_files)
            >>> # check output files
            >>> from moncenterlib.tools import files_check
            >>> return_files = {}
            >>> for type_file, files in t4r.output_files.items():
            ...     return_files[type_file] = files_check(files)
            >>> print(return_files)

        """
        self.logger.info("Start converting")
        self.logger.info("Checking config")
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
                self.logger.error("Path to file or dir is strange.")
                raise ValueError("Path to file or dir is strange.")

        if not os.path.isdir(output):
            self.logger.error("Path to output dir is strange.")
            raise ValueError("Path to output dir is strange.")

        self.__create_vars()

        q = queue.Queue()

        for file in input_files:
            self.logger.info("Set config for %s", file)
            cmd, output_files = self.__make_config4convbin(file, output, config)

            for type_file, filename in output_files.items():
                self.output_files[type_file].append(filename)

            q.put(cmd)

        def worker(q: queue.Queue):
            while not q.empty():
                cmd = q.get()

                with self.semaphore:
                    self.logger.info("Start converting file %s", cmd[-1])
                    self.__start_converting(cmd, True)

                q.task_done()

        for _ in range(self.workers):
            thread = threading.Thread(target=worker, args=(q,))
            thread.start()

    @typechecked
    def get_last_status(self) -> dict[str, dict]:
        """Returns the last line of processing status information.

        Returns:
            dict[str, str | bool]: The dictionary contains 3 keys. stderr, stdout, isStop.
            The stderr key stores the last line of error information.
            The stdout key stores the last line of information.
            The isStop key stores a boolean value. True if the process has stopped, False otherwise.

        Examples:
            >>> t4r = RtkLibConvib()
            >>> t4r.start(list_files, "/some_output_dir", config, True)
            >>> While True:
            >>>     status = t4r.get_last_status()
            >>>     if status["isStop"]:
            >>>         break
            >>>     time.sleep(1)
            >>>     print(status)
            {
                "isStop": True,
                "stdout": "some info",
                "stderr": ""
            }

        """

        output_status = defaultdict(dict)

        for file, std in self.std_log.items():
            stdout = ''
            stderr = ''

            isStop = False
            if self.__process[file] is not None and self.__process[file].poll() is not None:
                isStop = True

            if std["stdout"] != []:
                stdout = std["stdout"][-1]
            if std["stderr"] != []:
                stderr = std["stderr"][-1]

            output_status[file] = {"stdout": stdout,
                                   "stderr": stderr,
                                   "isStop": isStop
                                   }

        return output_status

    @typechecked
    def get_full_status(self) -> dict[str, list[str]]:
        """Returns the full lines of processing status information.

        Returns:
            dict[str, list[str]]: The dictionary contains 2 keys. stderr, stdout.
            The stderr key stores the list lines of error information.
            The stdout key stores the list lines of information.

        Examples:
            >>> t4r = RtkLibConvib()
            >>> t4r.start(list_files, "/some_output_dir", config, True)
            >>> print(t4r.get_full_status())
            {
                "stdout": ["some info", "blabla"]
                "stderr": []
            }

        """
        return self.std_log
