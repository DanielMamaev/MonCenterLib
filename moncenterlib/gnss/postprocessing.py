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
import subprocess
import tempfile
from typeguard import typechecked
from gps_time import GPSTime
import moncenterlib.tools as mcl_tools
import moncenterlib.gnss.tools as mcl_gnss_tools


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
    def scan_dirs(self, input_rnx: dict[str, str], recursion: bool = False) -> dict[str, list[str]]:
        """This method scans the directories and makes a list of files for further work of the class.
        The method can also recursively search for files.

        Args:
            input_rnx (dict[str, str]): input_rnx must be a dictionary.
                Key is the type of file. Value is the path to the directory.
                This is a list of keys that you can use. ['rover', 'base', 'nav', 'sp3', 'clk', 'erp', 'dcb', 'ionex'].
            recursion (bool, optional): Recursively search for files. Defaults to False.

        Raises:
            ValueError: Unidentified key.

        Returns:
            dict[str, list[str]]: Return a dict of files.

        Examples:
            >>> from moncenterlib.gnss.postprocessing import RtkLibPost
            >>> rtk_post = RtkLibPost()
            >>> paths = {'rover': '/path/to/rover', 'base': '/path/to/base', 'nav': '/path/to/nav'}
            >>> rtk_post.scan_dirs(paths, True)
            {
                'rover': ['file1.rnx', 'file2.rnx'],
                'base': ['file1.rnx', 'file2.rnx'],
                'nav': ['file1.rnx', 'file2.rnx']
            }
        """

        self.logger.info("Scanning directories...")
        type_files = ['rover', 'base', 'nav', 'sp3', 'clk', 'erp', 'dcb', 'ionex']
        for k in input_rnx.keys():
            if k not in type_files:
                raise ValueError(f"Unidentified key {k}")

        scan_dirs = dict()
        for key, directory in input_rnx.items():
            list_files = mcl_tools.get_files_from_dir(directory, recursion)
            scan_dirs[key] = list_files
        return scan_dirs

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
    def confing2dict(self, path2conf: str) -> dict:
        """This method is used to convert file configuration to dictionary.

        Args:
            path2conf (str): The path to the file configuration

        Raises:
            ValueError: Path to path2conf is strange.

        Returns:
            dict: Return dictionary of configuration.
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
    def start(self, input_rnx: dict[str, str | list[str]], output: str, config: dict[str, str],
              timeint: int = 0, recursion: bool = False,
              show_info_rtklib: bool = True) -> dict[str, list]:
        """The method starts the postprocessing.

        Args:
            input_rnx (dict[str, str  |  list[str]]): The dictionary where keys are a type of file and
                values are a list of path to the files or path to directory or path to one file.
            output (str): The path to the directory where the files will be saved.
            config (dict[str, str]): Dictionary with configuration.
                You can get the configuration by calling the get_default_config() method.
            timeint (int, optional): Time interval. Defaults to 0.
            recursion (bool, optional): If you put a path to dir in arg input_rnx, recursively search for files.
                Defaults to False.
            show_info_rtklib (bool, optional): This flag indicates whether to display the output of the rnx2rtkp program.
                True to display. False is not displayed. Defaults to True.

        Raises:
            ValueError: Output directory does not exist.
            ValueError: Config file does not exist.

        Returns:
            dict[str, list]: The dictionary contains 3 keys. done, no_exists, no_match.
            The done key stores a list of files that have been successfully created.
            The no_exists key stores a list of files that have not been created.
            The no_match key stores a list of no match files.

        Examples:
            >>> from moncenterlib.gnss.postprocessing import RtkLibPost
            >>> rtk_post = RtkLibPost()
            >>> paths = {'rover': '/path/to/rover', 'base': '/path/to/base', 'nav': '/path/to/nav'}
            >>> config = rtk_post.get_default_config()
            >>> rtk_post.start(paths, '/path/to/output', config, erp_from_config=False, timeint=1, recursion=False, show_info_rtklib=True)
            {
                "done": ["path2pos1", "path2pos2"],
                "error": ["path2pos3", "path2pos4"],
                "no_match": [{"base": "path2file1"}, {"erp": "path2file2"}]
            }
        """

        # - fcb - в rtklib это не робит
        # - sbas - пока забываем про это

        if not os.path.isdir(output):
            self.logger.error("Output directory does not exist")
            raise ValueError("Output directory does not exist")

        inputs = dict()
        for k, v in input_rnx.items():
            if isinstance(v, str) and os.path.isfile(v):
                inputs[k] = [v]
            elif isinstance(v, str) and os.path.isdir(v):
                inputs = self.scan_dirs(input_rnx, recursion)
            elif isinstance(v, list):
                inputs = input_rnx

        self.logger.info("Starting match files")
        match_list = defaultdict(dict)
        for file in inputs.get('rover', []):
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

        for file in inputs.get('base', []):
            try:
                date = mcl_gnss_tools.get_start_date_from_obs(file)
            except Exception as e:
                self.logger.error("Can't get date from base file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["base"] = file

        for file in inputs.get('nav', []):
            try:
                date = mcl_gnss_tools.get_start_date_from_nav(file)
            except Exception as e:
                self.logger.error("Can't get date from nav file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["nav"] = file

        for file in inputs.get('sp3', []):
            try:
                date = self._get_start_date_from_sp3(file)
            except Exception as e:
                self.logger.error("Can't get date from sp3 file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["sp3"] = file

        for file in inputs.get('clk', []):
            try:
                date = self._get_start_date_from_clk(file)
            except Exception as e:
                self.logger.error("Can't get date from clk file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["clk"] = file

        for file in inputs.get('erp', []):
            try:
                dates = self._get_dates_from_erp(file)
            except Exception as e:
                self.logger.error("Can't get dates from erp file %s", file)
                self.logger.error(e)
                continue
            for date in dates:
                match_list[date]["erp"] = file

        for file in inputs.get('dcb', []):
            try:
                date = self._get_start_date_from_dcb(file)
            except Exception as e:
                self.logger.error("Can't get date from dcb file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["dcb"] = file

        for file in inputs.get('ionex', []):
            try:
                date = self._get_start_date_from_ionex(file)
            except Exception as e:
                self.logger.error("Can't get date from ionex file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["ionex"] = file

        pos_paths = []
        no_match = []
        with tempfile.NamedTemporaryFile() as temp_file:
            for path_files in match_list.values():
                if len(path_files) != len(input_rnx):
                    no_match.append(path_files)
                    continue

                # make configuration
                self.logger.info("Starting make configuration")
                with open(temp_file.name, 'w', encoding="utf-8") as config_temp_file:

                    config["file-eopfile"] = path_files.get("erp", "")
                    config["file-dcbfile"] = path_files.get("dcb", "")

                    for key, val in config.items():
                        config_temp_file.write(key + '=' + val + '\n')

                # make command
                for rvr in path_files.get("rovers", []):
                    cmd = [mcl_tools.get_path2bin("rnx2rtkp")]

                    cmd += ["-ti", str(timeint)]
                    cmd += ["-k", temp_file.name]

                    cmd += [rvr]
                    cmd += [path_files.get("base", "")]
                    cmd += [path_files.get("nav", "")]
                    cmd += [path_files.get("sp3", "")]
                    cmd += [path_files.get("clk", "")]
                    cmd += [path_files.get("ionex", "")]

                    cmd = [i for i in cmd if i != ""]

                    path_end = os.path.join(output, os.path.basename(rvr)) + ".pos"
                    cmd += ["-o", path_end]

                    pos_paths.append(path_end)

                    self.logger.info("Run postprocessing %s", rvr)
                    if show_info_rtklib:
                        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL)
                    else:
                        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        output_dict = mcl_tools.files_check(pos_paths)
        output_dict["no_match"] = no_match
        return output_dict
