"""

"""


from logging import Logger
import os
import tempfile
import xml.etree.ElementTree as ET
import subprocess
from collections import defaultdict
from typeguard import typechecked
import moncenterlib.gnss.tools as mcl_tools
from pathlib import Path


class Anubis:
    """_summary_

    """
    @typechecked
    def __init__(self, logger: bool | Logger | None = None) -> None:

        self.logger = logger

        if self.logger in [None, False]:
            self.logger = mcl_tools.create_simple_logger("Anubis", logger)

    @typechecked
    def scan_dirs(self, input_dir_obs: str, input_dir_nav: str, recursion: bool = False) -> dict:
        match_list = defaultdict(list)
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
                date_nav = mcl_tools.get_start_date_from_nav(file_nav)
            except Exception:
                self.logger.error("Something happened to get date from nav file %s.", file_nav, exc_info=True)
                continue
            filter_files_nav[date_nav] = file_nav

        for file_obs in files_obs:
            date_obs = ''
            marker_name = ''
            try:
                date_obs = mcl_tools.get_start_date_from_obs(file_obs)
            except Exception:
                self.logger.error("Something happened to get date from obs file %s.", file_obs, exc_info=True)
                continue

            try:
                marker_name = mcl_tools.get_marker_name(file_obs)
            except Exception:
                self.logger.error("Something happened to get marker name from obs file %s.", file_obs, exc_info=True)
                continue

            if date_obs in filter_files_nav:
                match_list[marker_name].append([file_obs, filter_files_nav[date_obs]])

        return dict(match_list)

    @typechecked
    def start(self, input_data: dict | tuple, recursion: bool = False, output_dir_xtr: str | None = None) -> dict:

        match_list = {}
        output_list = defaultdict(dict)

        if isinstance(input_data, dict):
            match_list = input_data
        elif isinstance(input_data, tuple):
            if os.path.isfile(input_data[0]) and os.path.isfile(input_data[1]):
                if ' ' in input_data[0] or ' ' in input_data[1]:
                    self.logger.error("Please, remove spaces in path.")
                    raise ValueError("Please, remove spaces in path.")
                match_list = {'point': [[input_data[0], input_data[1]]]}

            elif os.path.isdir(input_data[0]) and os.path.isdir(input_data[1]):
                match_list = self.scan_dirs(input_data[0], input_data[1], recursion)
            else:
                raise ValueError("Path to file or dir is strange.")

        for marker_name, matchs in match_list.items():
            for match in matchs:
                if len(match) != 2:
                    self.logger.error("Some file is missing %s.", match)
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

                self.logger.info("Start parsing file Anubis %s.xtr", output_file_xtr)
                data_metric = self._parsing_xtr(output_file_xtr)

                output_list[marker_name][data_metric["date"]] = data_metric

        return dict(output_list)

    @typechecked
    def _create_config(self, match: list, temp_file: str, output_files_xtr: str | None) -> None:
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
