"""
This module is designed for monitoring the quality and quantity of multi—GNSS data.
The module has the following classes:
- Anubis;
- Soon.

Learn more about the specific class.
"""


from logging import Logger
import os
import tempfile
import xml.etree.ElementTree as ET
import subprocess
from collections import defaultdict
from typeguard import typechecked
import moncenterlib.tools as mcl_tools
import moncenterlib.gnss.tools as mcl_gnss_tools
from pathlib import Path


class Anubis:
    """
    G-Nut/Anubis is an open source tool designed to monitor the quality and quantity of multi—GNSS data stored in
    RINEX 2.xx and 3.0x formats.
    It is capable of processing new signals from all global navigation satellite systems and their add-ons
    (GPS, GLONASS, Galileo, BeiDou, SBAS and QZSS).
    G-Nut/Anubis supports GPS, GLONASS and Galileo and performs single-point positioning,
    as well as provides GNSS data characteristics based on altitude and azimuth.
    See more about G-Nut/Anubis here: https://gnutsoftware.com/software/anubis
    This class can processing one or more files.
    See code usage examples in the examples folder.
    """
    @typechecked
    def __init__(self, logger: bool | Logger | None = None) -> None:
        """
        Args:
            logger (bool | Logger, optional): if the logger is None, a logger will be created inside the default class.
                If the logger is False, then no information will be output.
                If you pass an instance of your logger, the information output will be implemented according to your logger.
                Defaults to None.
        """
        self.logger = logger

        if self.logger in [None, False]:
            self.logger = mcl_tools.create_simple_logger("Anubis", logger)

    @typechecked
    def scan_dirs(self, input_dir_obs: str, input_dir_nav: str, recursion: bool = False) -> tuple[dict[str, list[list[str]]], dict[str, list[str]]]:
        """
        This method scans the directory and makes a match list of files for further work of the class.
        The method can also recursively search for files.

        Args:
            input_dir_obs (str): Path to the observation directory.
            input_dir_nav (str): Path to the navigation directory.
            recursion (bool, optional): Recursively search for files. Defaults to False.

        Raises:
            ValueError: Please, remove spaces in path.

        Returns:
            tuple[dict[str, list[list[str]]], dict[str, list[str]]]: First element of the tuple is a dictionary of matching.
            Key is name of station. Value is list of matches. The list of matches contains observation and navigation files matched by date.
            Second element of the tuple is a dictionary of non-matching.
            The list of matches contains observation files for which no navigation files were found.

        Examples:
            >>> anubis = Anubis()
            >>> res = anubis.scan_dir("/path_to_dir_obs", "/path_to_dir_nav", True)
            >>> res
            {"station1": [["/obs1.txt", "/nav1.txt"], ["/obs2.txt", "/nav2.txt"]],
            "station2": [["/obs3.txt", "/nav1.txt"], ["/obs4.txt", "/nav4.txt"]]}
        """
        match_list = defaultdict(list)
        no_match_list = defaultdict(list)

        if ' ' in input_dir_obs or ' ' in input_dir_nav:
            self.logger.error("Please, remove spaces in path.")
            raise ValueError("Please, remove spaces in path.")

        self.logger.info("Finding files obs.")
        files_obs = mcl_tools.get_files_from_dir(input_dir_obs, recursion)

        self.logger.info("Finding files nav.")
        files_nav = mcl_tools.get_files_from_dir(input_dir_nav, recursion)

        self.logger.info("Start matching files.")
        filter_files_nav = dict()
        for file_nav in files_nav:
            try:
                date_nav = mcl_gnss_tools.get_start_date_from_nav(file_nav)
            except Exception as e:
                self.logger.error("Can't get date from nav file %s", file_nav)
                self.logger.error(e)
                continue
            filter_files_nav[date_nav] = file_nav

        for file_obs in files_obs:
            date_obs = ''
            marker_name = ''
            try:
                date_obs = mcl_gnss_tools.get_start_date_from_obs(file_obs)
            except Exception as e:
                self.logger.error("Can't get date from obs file %s", date_obs)
                self.logger.error(e)
                continue

            try:
                marker_name = mcl_gnss_tools.get_marker_name(file_obs)
            except Exception as e:
                self.logger.error("Can't get marker name from obs file %s", date_obs)
                self.logger.error(e)
                continue

            if date_obs in filter_files_nav:
                match_list[marker_name].append([file_obs, filter_files_nav[date_obs]])
            else:
                no_match_list[marker_name] += [file_obs]

        return dict(match_list), dict(no_match_list)

    @typechecked
    def start(self, input_data: dict | tuple,
              recursion: bool = False,
              output_dir_xtr: str | None = None) -> tuple[dict[str, dict[str, float | int | str | dict]], dict[str, list[str]]]:
        """
        This method starts the process of calculating the quality and quantity of multi-GNSS data.
        The method allows you to upload one or more files for calculation.

        Args:
            input_data (dict | tuple): There are several possible input options.
                Tuple which contains the path to the observations and navigation file("/obs.txt", "/nav.txt").
                Tuple which contains the path to the directory of observation and navigation files, respectively("/dir_obs", "/dir_nav"). 
                As well as the dictionary obtained from the scan_dirs method.
            recursion (bool, optional): Recursively search for files. Defaults to False.
            output_dir_xtr (str | None, optional): The directory where the anubis xtr output files will be saved. Defaults to None.

        Raises:
            ValueError: Please, remove spaces in path.
            ValueError: Path to file or dir is strange.

        Returns:
            tuple[dict[str, dict[str, float | int | str | dict]], dict[str, list[str]]]: First element of the tuple is a dictionary of metrics for each date found for each station.
            Second element of the tuple is a dictionary of observation files for which no navigation files were found.

        Examples:
            >>> anubis = Anubis()
            >>> result = anubis.start(("/path_to_dir_obs", "/path_to_dir_nav"), False, "/path2output_xtr")
            >>> res
            {"station1": {"date1": {"some_metrics": "123"},
                          "date2": {"some_metrics": "123"}
                          },
             "station2": {"date1": {"some_metrics": "123"},
                          "date2": {"some_metrics": "123"}
                          }
            }
        """
        match_list = {}
        no_match_list = {}
        output_list = defaultdict(dict)

        if isinstance(input_data, dict):
            match_list = input_data
        elif isinstance(input_data, tuple):
            if os.path.isfile(input_data[0]) and os.path.isfile(input_data[1]):
                if ' ' in input_data[0] or ' ' in input_data[1]:
                    self.logger.error("Please, remove spaces in path.")
                    raise ValueError("Please, remove spaces in path.")
                marker_name = mcl_gnss_tools.get_marker_name(input_data[0])
                match_list = {marker_name: [[input_data[0], input_data[1]]]}

            elif os.path.isdir(input_data[0]) and os.path.isdir(input_data[1]):
                match_list, no_match_list = self.scan_dirs(input_data[0], input_data[1], recursion)
            else:
                raise ValueError("Path to file or dir is strange.")

        for marker_name, matchs in match_list.items():
            for match in matchs:

                if len(match) != 2:
                    self.logger.error("Some file is missing %s.", match)
                    continue

                if ' ' in match[0]:
                    self.logger.error("Please, remove spaces in path %s.", match[0])
                    continue
                if ' ' in match[1]:
                    self.logger.error("Please, remove spaces in path %s.", match[1])
                    continue

                cmd = [mcl_tools.get_path2bin("anubis")]

                # создание временного файла конфига
                with tempfile.NamedTemporaryFile() as temp_file:
                    self.logger.info('Create config')
                    self._create_config(match, temp_file.name, output_dir_xtr)

                    cmd += ["-x", temp_file.name]

                    self.logger.info('Start Anubis')
                    subprocess.run(cmd, stderr=subprocess.DEVNULL, check=False)

                # parsing file
                output_file_xtr = ""
                if output_dir_xtr is None:
                    output_file_xtr = f'{match[0]}.xtr'
                else:
                    output_file_xtr = str(Path(output_dir_xtr).joinpath(Path(match[0]).name + ".xtr"))

                self.logger.info("Start parsing file Anubis %s", output_file_xtr)
                data_metric = self._parsing_xtr(output_file_xtr)

                if data_metric is not None:
                    output_list[marker_name][data_metric["date"]] = data_metric

        return dict(output_list), no_match_list

    @typechecked
    def _create_config(self, match: list, temp_file: str, output_files_xtr: str | None) -> None:
        """A method for creating a configuration file for Anubis.

        Args:
            match (list): The list must contain the path to the observation file and the path to the navigation file.
            temp_file (str): Path to existing temp file of config.
            output_files_xtr (str | None): The directory where the output files of anubis xtr will be saved.
        """
        conf = ET.Element('config')
        param = {
            'sec_sum': "1",
            'sec_hdr': "0",
            'sec_obs': "1",
            'sec_gap': "1",
            'sec_bnd': "1",
            'sec_pre': "1",
            'sec_mpx': "1",
            'sec_snr': "1",
            'sec_est': "0",
            'sec_ele': "0",
            'sec_sat': "0"
        }
        ET.SubElement(conf, 'qc', param)

        inp = ET.SubElement(conf, 'inputs')
        inp_o = ET.SubElement(inp, 'rinexo')
        inp_o.text = match[0]
        inp_n = ET.SubElement(inp, 'rinexn')
        inp_n.text = match[1]

        o = ET.SubElement(conf, 'outputs')
        xtr = ET.SubElement(o, 'xtr')
        if output_files_xtr is None:
            xtr.text = f'{match[0]}.xtr'
        else:
            xtr.text = str(Path(output_files_xtr).joinpath(Path(match[0]).name + ".xtr"))
        tree = ET.ElementTree(conf)
        tree.write(temp_file)

    @typechecked
    def _parsing_xtr(self, path2file: str) -> dict[str, float | int | str | dict] | None:
        """A method for creating a reading of a xtr file and forming a dictionary with metrics.

        Args:
            path2file (str): Path to xtr file.

        Returns:
            dict[str, float | int | str | dict] | None: Returns a dictionary of metrics.
        """
        try:
            with open(path2file, 'r', encoding="utf-8") as f:
                data = f.readlines()
        except Exception:
            self.logger.error("Something happened to the opening of the Anubis file %s.", path2file, exc_info=True)
            return None

        meta_data = {}
        flag_gnssum = False
        flag_data_error = False
        for indx, row in enumerate(data):
            if '=TOTSUM' in row:
                row_split = row.split(' ')
                row_split = list(filter(lambda i: i != '', row_split))
                date = row_split[1] + " " + row_split[2]
                try:
                    meta_data["date"] = date
                    meta_data["total_time"] = float(row_split[5])
                    meta_data["expt_obs"] = int(row_split[8])
                    meta_data["exis_obs"] = int(row_split[9])
                    meta_data["ratio"] = float(row_split[10])
                    meta_data["expt_obs10"] = int(row_split[13])
                    meta_data["exis_obs10"] = int(row_split[14])
                    meta_data["ratio10"] = float(row_split[15])
                except Exception:
                    self.logger.warning("Parameter =TOTSUM. Skip %s.", path2file, exc_info=True)
                    flag_data_error = True
                    break

            elif '#GNSSUM' in row:
                if flag_gnssum:
                    continue
                flag_gnssum = True

                meta_data["miss_epoch"] = dict()
                meta_data["code_multi"] = dict()
                meta_data["n_slip"] = dict()
                count = 0
                while True:
                    row_data = data[indx+2+count]
                    if row_data == '\n':
                        break
                    row_data = row_data.split(' ')
                    row_split = list(filter(lambda i: i != '', row_data))
                    name_sys = row_split[0].replace("=", "").replace("SUM", "")
                    try:
                        meta_data["miss_epoch"][name_sys] = int(row_split[11])
                        meta_data["n_slip"][name_sys] = int(row_split[14])
                    except Exception:
                        self.logger.warning("Parameter =TOTSUM. Skip %s.", path2file, exc_info=True)
                        flag_data_error = True
                        break

                    try:
                        meta_data["code_multi"][name_sys + "MP1"] = float(row_split[18])
                    except ValueError:
                        meta_data["code_multi"][name_sys + "MP1"] = row_split[18]

                    try:
                        meta_data["code_multi"][name_sys + "MP2"] = float(row_split[19])
                    except ValueError:
                        meta_data["code_multi"][name_sys + "MP2"] = row_split[19]
                    count += 1

                if flag_data_error:
                    break

            elif '=GNSSYS' in row:
                meta_data["sat_healthy"] = dict()
                row_data = row
                row_split = row_data.split(' ')
                row_split = list(filter(lambda i: i != '', row_split))
                num_sys = int(row_split[3])
                for i in range(num_sys):
                    row_data = data[indx+2+i]
                    row_split = row_data.split(' ')
                    row_split = list(filter(lambda i: i != '', row_split))
                    name_sys = row_split[0].replace("=", "").replace("SAT", "")
                    try:
                        meta_data["sat_healthy"][name_sys] = int(row_split[3])
                    except Exception:
                        self.logger.warning("Parameter =GNSSYS. Skip %s.", path2file, exc_info=True)
                        flag_data_error = True
                        break

                if flag_data_error:
                    break

            elif '#GNSSxx' in row:
                meta_data["sig2noise"] = dict()
                count = 0
                while True:
                    try:
                        row_data = data[indx+1+count]
                    except Exception:
                        break

                    if row_data == '\n':
                        break
                    row_data = row_data.split(' ')
                    row_split = list(filter(lambda i: i != '', row_data))
                    name_sys = row_split[0].replace("=", "")
                    try:
                        meta_data["sig2noise"][name_sys] = float(row_split[3])
                    except Exception:
                        pass
                    count += 1

        if flag_data_error:
            self.logger.error("Incorrect data in file %s.", path2file)
            return None

        return meta_data
