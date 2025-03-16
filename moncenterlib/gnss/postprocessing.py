"""
The module for standard and precise positioning with GNSS (global navigation satellite system).

- Post‐Processing Analysis;
- Soon.

The module has the following classes:
- RtkLibPost;
- Soon.

Learn more about the specific class.
"""


from collections import defaultdict
from datetime import datetime, timedelta
import os
from logging import Logger
from pprint import pprint
import queue
import subprocess
import tempfile
import threading
from typeguard import typechecked
from gps_time import GPSTime
import moncenterlib.tools as mcl_tools
import moncenterlib.gnss.tools as mcl_gnss_tools
import moncenterlib.tools as mcl_tools


class RtkLibPost:
    """
    This class is based on the RTKLib software package.
    RTKLIB contains a post processing analysis AP RTKPOST. RTKPOST inputs the standard RINEX 2.10, 2.11,
    2.12, 3.00, 3.01, 3.02 (draft) observation data and navigation message files (GPS, GLONASS, Galileo, QZSS,
    BeiDou and SBAS) and can computes the positioning solutions by various positioning modes including
    Single‐point, DGPS/DGNSS, Kinematic, Static, PPP‐Kinematic and PPP‐Static.
    See more about RTKLIB here: https://rtklib.com/
    This class can postprocessing one or more files.
    See code usage examples in the examples folder.

    Available file types:
    {
        "rover": "",
        "base": "",
        "nav": "",
        "sp3": "",
        "clk": "",
        "ionex": "",
        "erp": "",
        "dcb": "",
        "fcb": "",
        "sbas": "",
        "otl": "",
        "satant": "",
        "rcvant": ""
    }
    """
    @typechecked
    def __init__(self, logger: bool | Logger | None = None):
        """
        Args:
            logger (bool | Logger, optional): if the logger is None, a logger will be created inside the default class.
                If the logger is False, then no information will be output.
                If you pass an instance of your logger, the information output will be implemented according to your logger.
                Defaults to None.
        """

        self.logger = logger

        if self.logger in [None, False]:
            self.logger = mcl_tools.create_simple_logger("RtkLibPost", logger)

        self.__default_config = {
            'pos1-posmode': '0',
            'pos1-frequency':  '2',
            'pos1-soltype':  '0',
            'pos1-elmask':  '15',
            'pos1-snrmask_r':  'off',
            'pos1-snrmask_b':  'off',
            'pos1-snrmask_l1':  '0,0,0,0,0,0,0,0,0',
            'pos1-snrmask_l2':  '0,0,0,0,0,0,0,0,0',
            'pos1-snrmask_l5':  '0,0,0,0,0,0,0,0,0',
            'pos1-dynamics':  '0',
            'pos1-tidecorr':  '0',
            'pos1-ionoopt':  '1',
            'pos1-tropopt':  '1',
            'pos1-sateph':  '0',
            'pos1-posopt1':  '0',
            'pos1-posopt2':  '0',
            'pos1-posopt3':  '0',
            'pos1-posopt4':  '0',
            'pos1-posopt5':  '0',
            'pos1-posopt6':  '0',
            'pos1-exclsats':  '',
            'pos1-navsys':  '1',

            'pos2-armode':  '1',
            'pos2-gloarmode':  '1',
            'pos2-bdsarmode':  '1',
            'pos2-arthres':  '3',
            'pos2-arthres1':  '0.9999',
            'pos2-arthres2':  '0.25',
            'pos2-arthres3':  '0.1',
            'pos2-arthres4':  '0.05',
            'pos2-arlockcnt':  '0',
            'pos2-arelmask':  '0',
            'pos2-arminfix':  '10',
            'pos2-armaxiter':  '1',
            'pos2-elmaskhold':  '0',
            'pos2-aroutcnt':  '5',
            'pos2-maxage':  '30',
            'pos2-syncsol':  'off',
            'pos2-slipthres':  '0.05',
            'pos2-rejionno':  '30',
            'pos2-rejgdop':  '30',
            'pos2-niter':  '1',
            'pos2-baselen':  '0',
            'pos2-basesig':  '0',

            'out-solformat':  '0',
            'out-outhead':  '1',
            'out-outopt':  '1',
            'out-outvel':  '0',
            'out-timesys':  '0',
            'out-timeform':  '1',
            'out-timendec':  '3',
            'out-degform':  '0',
            'out-fieldsep':  '',
            'out-outsingle':  '0',
            'out-maxsolstd':  '0',
            'out-height':  '0',
            'out-geoid':  '0',
            'out-solstatic':  '0',
            'out-nmeaintv1':  '0',
            'out-nmeaintv2':  '0',
            'out-outstat':  '0',

            'stats-eratio1':  '100',
            'stats-eratio2':  '100',
            'stats-errphase':  '0.003',
            'stats-errphaseel':  '0.003',
            'stats-errphasebl':  '0',
            'stats-errdoppler':  '1',
            'stats-stdbias':  '30',
            'stats-stdiono':  '0.03',
            'stats-stdtrop':  '0.3',
            'stats-prnaccelh':  '10',
            'stats-prnaccelv':  '10',
            'stats-prnbias':  '0.0001',
            'stats-prniono':  '0.001',
            'stats-prntrop':  '0.0001',
            'stats-prnpos':  '0',
            'stats-clkstab':  '5E-12',

            'ant1-postype':  '0',
            'ant1-pos1':  '90',
            'ant1-pos2':  '0',
            'ant1-pos3':  '-6335367.62849036',
            'ant1-anttype':  '',
            'ant1-antdele':  '0',
            'ant1-antdeln':  '0',
            'ant1-antdelu':  '0',

            'ant2-postype':  '0',
            'ant2-pos1':  '90',
            'ant2-pos2':  '0',
            'ant2-pos3':  '-6335367.62849036',
            'ant2-anttype':  '',
            'ant2-antdele':  '0',
            'ant2-antdeln':  '0',
            'ant2-antdelu':  '0',
            'ant2-maxaveep':  '0',
            'ant2-initrst':  'off',

            'misc-timeinterp':  'off',
            'misc-sbasatsel':  '0',
            'misc-rnxopt1':  '',
            'misc-rnxopt2':  '',
            'misc-pppopt':  '',
            'file-satantfile':  '',
            'file-rcvantfile':  '',
            'file-staposfile':  '',
            'file-geoidfile':  '',
            'file-ionofile':  '',
            'file-dcbfile':  '',
            'file-eopfile':  '',
            'file-blqfile':  '',
            'file-tempdir':  '',
            'file-geexefile':  '',
            'file-solstatfile':  '',
            'file-tracefile':  ''
        }

        self.__create_vars()

    def __create_vars(self):
        self.__process = defaultdict(None)

        def def_dict(): return {
            'stdout': [],
            'stderr': []
        }
        self.std_log = defaultdict(def_dict)
        self.output_files = defaultdict(list)

    @typechecked
    def _get_start_date_from_sp3(self, file: str) -> str:
        date = ""
        with open(file, 'r', encoding="utf-8") as f:
            line = f.readline()
            sp3_version = line[:2]
            if sp3_version != '#c':
                raise Exception(f'Invalid sp3 version {sp3_version}')

            date = line[3:].split()[:3]
            date[1] = date[1].zfill(2)
            date[2] = date[2].zfill(2)
            date = '-'.join(date)
        return date

    @typechecked
    def _get_start_date_from_clk(self, file: str) -> str:
        date = ""
        with open(file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if 'RINEX VERSION' in line:
                    rinex_v = line.split()[0]
                    if not (rinex_v.startswith("2") or rinex_v.startswith("3")):
                        raise Exception(f"Unknown version rinex {rinex_v}")

                if 'GPS week' in line:
                    line = line.split()
                    gps_week = int(line[2])
                    day = int(line[4])
                    gps_time = GPSTime(gps_week, day * 24 * 60 * 60)
                    date = gps_time.to_datetime().strftime("%Y-%m-%d")
                    break
        return date

    @typechecked
    def _get_dates_from_erp(self, file: str) -> list:
        dates = []
        with open(file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            erp_version = lines[0].split()[1]
            if erp_version != "2":
                raise Exception(f"Unknown version erp {lines[0].split()[1]}")

            for line in lines[4:]:
                mjd = float(line.split()[0])
                # Offset between MJD 0 and Unix epoch (January 1, 1970)
                mjd_epoch_offset = 40587
                days_since_epoch = int(mjd) - mjd_epoch_offset
                date = datetime(1970, 1, 1) + timedelta(days=days_since_epoch)
                date = date.strftime("%Y-%m-%d")
                dates.append(date)
        return dates

    @typechecked
    def _get_start_date_from_ionex(self, file: str) -> str:
        date = ""
        ionex_ver_list = ["1.0"]
        with open(file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if 'IONEX VERSION' in line:
                    rinex_v = line.split()[0]
                    if rinex_v not in ionex_ver_list:
                        raise Exception(f"Unknown version ionex {rinex_v}")

                if "EPOCH OF FIRST MAP" in line:
                    date = line.split()[:3]
                    date[1] = date[1].zfill(2)
                    date[2] = date[2].zfill(2)
                    date = '-'.join(date)
        return date

    @typechecked
    def _get_start_date_from_dcb(self, file: str) -> str:
        date = ""
        dcb_ver_list = ["0.01", "1.00"]
        with open(file, 'r', encoding="utf-8") as f:
            line = f.readline()
            dcb_version = line.split()[1]
            if dcb_version not in dcb_ver_list:
                raise Exception(f'Unknown version dcb {dcb_version}')

            date = line.split()[5].split(":")[:2]
            date[0] = "20" + date[0] if len(date[0]) == 2 else date[0]
            date = datetime.strptime("-".join(date), "%Y-%j")
            date = date.strftime("%Y-%m-%d")
        return date

    @typechecked
    def __make_cmd(self, input_rnx: dict[str, str], output_dir: str, timeint: int, temp_file) -> list[str]:
        cmd = [mcl_tools.get_path2bin("rnx2rtkp")]

        cmd += ["-ti", str(timeint)]
        cmd += ["-k", temp_file.name]

        cmd += [input_rnx.get("rover", "")]
        cmd += [input_rnx.get("base", "")]
        cmd += [input_rnx.get("nav", "")]
        cmd += [input_rnx.get("sp3", "")]
        cmd += [input_rnx.get("clk", "")]
        cmd += [input_rnx.get("ionex", "")]

        cmd = [i for i in cmd if i != ""]

        path_end = os.path.join(output_dir, os.path.basename(input_rnx.get("rover", ""))) + ".pos"
        cmd += ["-o", path_end]

        return cmd

    @typechecked
    def __start_process(self, cmd: list[str], wait_process: bool = False):
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

    def get_default_config(self) -> dict:
        """
        Return variable __default_config. __default_config isn't editable.
        In the future, you will manually configure this config and send it to the start method.
        See documentation RTKLIB (manual_2.4.2, page 34-49), how to configuration.
        Also you can see in example code how to configure.

        Returns:
            dict: default config for rnx2rtkp of RTKLib

        Examples:
            >>> from moncenterlib.gnss.postprocessing import RtkLibPost
            >>> rtk_post = RtkLibPost()
            >>> rtk_post.get_default_config()
            {
                'pos1-posmode': '0',
                'pos1-frequency':  '2',
                'pos1-soltype':  '0',
                'pos1-elmask':  '15',
                'pos1-snrmask_r':  'off',
                'pos1-snrmask_b':  'off',
                ...
            }
        """
        return self.__default_config.copy()

    @typechecked
    def config2dict(self, path2conf: str) -> dict[str, str]:
        """This method is used to convert file configuration to dictionary.

        Args:
            path2conf (str): The path to the file configuration

        Raises:
            ValueError: Path to path2conf is strange.

        Returns:
            dict: Return dictionary of configuration.

        Examples:
            >>> from moncenterlib.gnss.postprocessing import RtkLibPost
            >>> rtk_post = RtkLibPost()
            >>> config = rtk_post.config2dict('/path/to/config.conf')
            {
                "param1": "val1",
                "param2": "val2"
            }
        """

        if not os.path.isfile(path2conf):
            raise ValueError("Path to path2conf is strange.")

        config_dict = {}
        with open(path2conf, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    value = value.split('#', 1)[0]  # remove comment
                    config_dict[key.strip()] = value.strip()

        return config_dict

    @typechecked
    def dict2config(self,
                    config: dict[str, str],
                    path_file: str | tempfile._TemporaryFileWrapper,
                    input_rnx: dict[str, str | list] = {}):
        """Saves the dictionary with the RtkLibPost configuration to a file.
        The file can be used in rnx2rtkp CLI or rtkpost GUI.

        Args:
            config (dict[str, str]): Config for rnx2rtkp of RTKLibPost.
            path_file (str | tempfile._TemporaryFileWrapper): The path where the configuration file will be created.
                You can use it in rnx2rtkp CLI or rtkpost GUI.
            input_rnx (dict[str, str  |  list], optional): The dictionary where keys are a type of file and
                values are a path to one file. Defaults to {}.

        Exaples:
            >>> from moncenterlib.gnss.postprocessing import RtkLibPost
            >>> rtk_post = RtkLibPost()
            >>> paths = {"rover": "path/to/rover_file", "satant": "path/to/satant_file"}
            >>> config = rtk_post.get_default_config()
            >>> rtk_post.dict2config(config, "path/to/config.conf", input_rnx=paths)
        """
        self.logger.info("Starting make configuration")

        path_config_file = None

        # This type of variable is used in start_multi_processing and start_single_processing
        if isinstance(path_file, tempfile._TemporaryFileWrapper):
            path_config_file = path_file.name
        elif isinstance(path_file, str):
            path_config_file = path_file

        with open(path_config_file, 'w', encoding="utf-8") as config_file:
            config["file-eopfile"] = input_rnx.get("erp", "")
            config["file-dcbfile"] = input_rnx.get("dcb", "")
            config['file-blqfile'] = input_rnx.get("otl", "")
            config['file-satantfile'] = input_rnx.get("satant", "")
            config['file-rcvantfile'] = input_rnx.get("rcvant", "")

            for key, val in config.items():
                config_file.write(key + '=' + val + '\n')

    @typechecked
    def match_files(self,
                    input_rnx: dict[str, str],
                    recursion: bool = True) -> tuple[dict, dict]:
        """This method allows you to automatically match the input files. The input is provided with data types and
            paths to the directory where these files are stored.
            Each file is scanned and the measurement start date is read.
            By this date, the files are being compared.
            This allows you to automate further post-processing of a large number of files.

        Args:
            input_rnx (dict[str, str]): The dictionary where keys are a type of file and values are
                a path to the directory where files are stored.
            recursion (bool, optional): Recursively search for files. Defaults to True.

        Raises:
            ValueError: Does not support a type of file
            ValueError: Invalid file path

        Returns:
            tuple[dict, dict]: A tuple has two elements.
                The first is the matched files, the second is the files for which the files could not be matched.

        Examples:
            >>> from moncenterlib.gnss.postprocessing import RtkLibPost
            >>> rtk_post = RtkLibPost()
            >>> paths = {"rover": "path/to/rover_directory", "nav": "path/to/nav_directory", "satant": "path/to/satant_directory"}
            >>> match_files, no_match = rtk_post.match_files(paths, True)
        """

        # check correct input
        for type_file, path_file in input_rnx.items():
            if type_file == "fcb" or type_file == "sbas":
                self.logger.error("Does not support %s", type_file)
                raise ValueError(f"Does not support {type_file}")

            if type_file == "otl" or type_file == "satant" or type_file == "rcvant":
                if os.path.isfile(path_file) is False:
                    self.logger.error("Invalid file path: %s", path_file)
                    raise ValueError(f"Invalid file path: {path_file}")
                else:
                    continue

            if isinstance(path_file, str) is False or os.path.isdir(path_file) is False:
                self.logger.error("Invalid file path: %s", path_file)
                raise ValueError(f"Invalid file path: {path_file}")

        input_files = defaultdict(list)
        for type_file, dir in input_rnx.items():
            if type_file == "otl" or type_file == "satant" or type_file == "rcvant":
                continue
            input_files[type_file] = mcl_tools.get_files_from_dir(dir, recursion)

        self.logger.info("Starting match files")
        match_list = defaultdict(dict)
        for file in input_files.get('rover', []):
            try:
                date = mcl_gnss_tools.get_start_date_from_obs(file)
            except Exception as e:
                self.logger.error("Can't get date from rover file %s", file)
                self.logger.error(e)
                continue
            if "rovers" in match_list[date]:
                match_list[date]["rovers"] += [file]
            else:
                match_list[date]["rovers"] = [file]

        for file in input_files.get('base', []):
            try:
                date = mcl_gnss_tools.get_start_date_from_obs(file)
            except Exception as e:
                self.logger.error("Can't get date from base file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["base"] = file

        for file in input_files.get('nav', []):
            try:
                date = mcl_gnss_tools.get_start_date_from_nav(file)
            except Exception as e:
                self.logger.error("Can't get date from nav file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["nav"] = file

        for file in input_files.get('sp3', []):
            try:
                date = self._get_start_date_from_sp3(file)
            except Exception as e:
                self.logger.error("Can't get date from sp3 file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["sp3"] = file

        for file in input_files.get('clk', []):
            try:
                date = self._get_start_date_from_clk(file)
            except Exception as e:
                self.logger.error("Can't get date from clk file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["clk"] = file

        for file in input_files.get('ionex', []):
            try:
                date = self._get_start_date_from_ionex(file)
            except Exception as e:
                self.logger.error("Can't get date from ionex file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["ionex"] = file

        for file in input_files.get('erp', []):
            try:
                dates = self._get_dates_from_erp(file)
            except Exception as e:
                self.logger.error("Can't get dates from erp file %s", file)
                self.logger.error(e)
                continue
            for date in dates:
                match_list[date]["erp"] = file

        for file in input_files.get('dcb', []):
            try:
                date = self._get_start_date_from_dcb(file)
            except Exception as e:
                self.logger.error("Can't get date from dcb file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["dcb"] = file

        # add additional files
        for date, match in match_list.items():
            if input_rnx.get("otl", "") != "":
                match["otl"] = input_rnx.get("otl", "")
            if input_rnx.get("satant", "") != "":
                match["satant"] = input_rnx.get("satant", "")
            if input_rnx.get("rcvant", "") != "":
                match["rcvant"] = input_rnx.get("rcvant", "")

        # clearing incomplete lists
        no_match = dict()
        finally_match = dict()
        for date, match in match_list.items():
            if len(match) != len(input_rnx):
                no_match[date] = match
                continue
            finally_match[date] = match

        return finally_match, no_match

    def start_multi_processing(self,
                               match_list: dict[str, dict[str, str | list]],
                               output_dir: str,
                               config: dict[str, str],
                               timeint: int = 0,
                               workers: int = 1):
        """The method starts the postprocessing. The method allows you to postprocess a large number of files.
        The generated dictionary with the matched files is taken from the 'match_files' method.
        This method is non-blocking. You can use an endless loop to wait for the process to complete.
        See the usage example.

        Args:
            match_list (dict[str, dict[str, str  |  list]]): Match files from the 'match_files' method.
            output_dir (str): The path to the directory where the files will be saved.
            config (dict[str, str]): Config for rnx2rtkp of RTKLibPost.
            timeint (int, optional): Time interval. Defaults to 0.
            workers (int, optional): The number of parallel processes.
                It reduces the processing time for multiple files. Defaults to 1.

        Examples:
            >>> from moncenterlib.gnss.postprocessing import RtkLibPost
            >>> rtk_post = RtkLibPost()
            >>> paths = {"rover": "path/to/rover_directory", "nav": "path/to/nav_directory", "satant": "path/to/satant_file"}
            >>> match_files, no_match = rtk_post.match_files(paths, True)
            >>> config = rtk_post.get_default_config()
            >>> rtk_post.start_multi_processing(match_files, "path/to/output_directory", config, timeint=1, workers=2)
            >>> # wait process and get status
            >>> while True:
            ...     time.sleep(1)
            ...     status = rtk_post.get_last_status()
            ...     print(status)
            ...     states = [s['isStop'] for s in status.values()]
            ...     if all(states):
            ...         break
            >>> print(rtk_post.output_files)
        """

        self.logger.info("Start MultiProcessing")
        if not os.path.isdir(output_dir):
            self.logger.error("Output directory does not exist")
            raise ValueError("Output directory does not exist")

        self.__create_vars()

        semaphore = threading.Semaphore(workers)
        q = queue.Queue()

        for match in match_list.values():
            for rover in match.get('rovers', []):
                match_temp = match.copy()
                match_temp.pop("rovers")
                match_temp["rover"] = rover
                q.put(match_temp)

        def worker(q: queue.Queue):
            while not q.empty():
                input_rnx: dict = q.get()

                with (tempfile.NamedTemporaryFile() as temp_file,
                      semaphore):
                    # make configuration
                    self.dict2config(config, temp_file, input_rnx)

                    # make command
                    cmd = self.__make_cmd(input_rnx, output_dir, timeint, temp_file)

                    self.logger.info("Run postprocessing %s", input_rnx.get("rover", ""))
                    self.__start_process(cmd, True)

                q.task_done()

        for _ in range(workers):
            thread = threading.Thread(target=worker, args=(q,))
            thread.start()

    @typechecked
    def start_single_processing(self,
                                input_rnx: dict[str, str],
                                output_dir: str,
                                config: dict[str, str],
                                timeint: int = 0,
                                wait_process: bool = True
                                ):
        """The method starts the postprocessing. This method can process single files. This method is non-blocking.
        You can use an endless loop to wait for the process to complete. See the usage example.

        Args:
            input_rnx (dict[str, str]): The dictionary where keys are a type of file and values are
                a path to the file.
            output_dir (str): The path to the directory where the files will be saved.
            config (dict[str, str]): Config for rnx2rtkp of RTKLibPost.
            timeint (int, optional): Time interval. Defaults to 0.
            wait_process (bool, optional): Wait for the method to be rejected. Or run it as a parallel process.
                Defaults to False.

        Raises:
            ValueError: Output directory does not exist.
            ValueError: Rover path is not set.
            ValueError: Path to file 'path/to/file' does not exist.

        Examples:
            >>> from moncenterlib.gnss.postprocessing import RtkLibPost
            >>> rtk_post = RtkLibPost()
            >>> paths = {"rover": "path/to/rover_file", "nav": "path/to/nav_file", "satant": "path/to/satant_file"}
            >>> config = rtk_post.get_default_config()
            >>> rtk_post.start_single_processing(paths, "path/to/output_directory", config, timeint=1, wait_process=True)
            >>> print(rtk_post.output_files)
        """

        # - fcb - в rtklib это не робит
        # - sbas - пока забываем про это

        if input_rnx.get("rover", "") == "":
            self.logger.error("Rover path is not set")
            raise ValueError("Rover path is not set")

        if not os.path.isdir(output_dir):
            self.logger.error("Output directory does not exist")
            raise ValueError("Output directory does not exist")

        for path_file in input_rnx.values():
            if not os.path.isfile(path_file):
                self.logger.error("Path to file %s does not exist", path_file)
                raise ValueError(f"Path to file '{path_file}' does not exist")

        self.__create_vars()

        with tempfile.NamedTemporaryFile() as temp_file:
            # make configuration
            self.dict2config(config, temp_file, input_rnx)

            # make command
            cmd = self.__make_cmd(input_rnx, output_dir, timeint, temp_file)

            self.logger.info("Run postprocessing %s", input_rnx.get("rover", ""))
            self.__start_process(cmd, wait_process)

    @typechecked
    def get_last_status(self) -> dict[str, dict]:
        """Returns the last line of processing status information.

        Returns:
            dict[str, str | bool]: The dictionary contains 3 keys. stderr, stdout, isStop.
            The stderr key stores the last line of error information.
            The stdout key stores the last line of information.
            The isStop key stores a boolean value. True if the process has stopped, False otherwise.

        Examples:
            >>> post = RtkLibPost()
            >>> post.start_single_processing(...)
            >>> While True:
            >>>     status = post.get_last_status()
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
                stdout = std["stdout"][-2]
            if std["stderr"] != []:
                stderr = std["stderr"][-2]

            output_status[file] = {"stdout": stdout,
                                   "stderr": stderr,
                                   "isStop": isStop
                                   }

        return output_status

    @typechecked
    def get_full_status(self) -> dict[str, dict[str, list]]:
        """Returns the full lines of processing status information.

        Returns:
            dict[str, dict[str, list]]: The dictionary contains 2 keys. stderr, stdout.
            The stderr key stores the list lines of error information.
            The stdout key stores the list lines of information.

        Examples:
            >>> post = RtkLibConvib()
            >>> post.start_single_processing(...)
            >>> print(post.get_full_status())
            {
                "/home/file1": {
                    "stdout": ["Status: Running", "bla bla"],
                    "stderr": ["Error: File not found", "bum bum"]
                }
                "/home/file2": {
                    "stdout": ["ok"],
                    "stderr": []
                }
            }

        """
        return self.std_log
