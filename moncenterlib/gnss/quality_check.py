import logging
import os
import json
import datetime as dt
import xml.etree.ElementTree as ET
import string
import random
import subprocess
from pathlib import Path
from collections import defaultdict
from shutil import copy2
from progress.bar import IncrementalBar
from moncenterlib.gnss.different_tools import type_check, disable_progress_bar


class Anubis:
    def __init__(self, input_logger: logging = None) -> None:
        self.logger = input_logger
        if not input_logger:
            self.logger = logging.getLogger('Anubis')
            self.logger.handlers.clear()
            self.logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        self.path_conf4del = ""
        self.path_xtr4del = ""

    @type_check((str, 'path_obs'), (str, 'path_nav'), (bool, 'recursion'), (bool, 'show_progress'))
    def scan_dirs(self, path_obs: str, path_nav: str, recursion: bool = False, show_progress: bool = True) -> dict:
        match_list = defaultdict(list)
        if ' ' in path_obs or ' ' in path_nav:
            self.logger.error("Please, remove spaces in path.")
            raise ValueError("Please, remove spaces in path.")

        self.logger.info("Finding files obs")
        files_obs = []
        if os.path.isdir(path_obs):
            if recursion:
                for root, _, files in os.walk(path_obs):
                    for file in files:
                        path = os.path.join(root, file)
                        files_obs.append(path)
            else:
                temp_lst = []
                for file in os.listdir(path_obs):
                    if os.path.isfile(os.path.join(path_obs, file)):
                        temp_lst.append(os.path.join(path_obs, file))
                files_obs = temp_lst
        else:
            raise ValueError("Path to dir is strange.")

        self.logger.info("Finding files nav")
        files_nav = []
        if os.path.isdir(path_nav):
            if recursion:
                for root, _, files in os.walk(path_nav):
                    for file in files:
                        path = os.path.join(root, file)
                        files_nav.append(path)
            else:
                temp_lst = []
                for file in os.listdir(path_nav):
                    if os.path.isfile(os.path.join(path_nav, file)):
                        temp_lst.append(os.path.join(path_nav, file))
                files_nav = temp_lst
        else:
            raise ValueError("Path to dir is strange.")

        inc_bar = IncrementalBar('Filter nav - Progress', max=len(files_nav),
                                 suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
        if not show_progress:
            inc_bar = disable_progress_bar(inc_bar)

        inc_bar.start()
        filter_files_nav = dict()
        for file_nav in files_nav:
            date_nav = ''
            flag_end = False
            try:
                with open(file_nav, 'r', encoding="utf-8") as f_nav:
                    for line_nav in f_nav:
                        if 'END OF HEADER' in line_nav:
                            flag_end = True
                        elif flag_end:
                            date_nav = line_nav.split()[1:4]
                            date_nav[1] = date_nav[1].zfill(2)
                            date_nav[2] = date_nav[2].zfill(2)
                            if len(date_nav[0]) == 4:
                                date_nav = dt.datetime.strptime(
                                    f'{date_nav[0]}-{date_nav[1]}-{date_nav[2]}', '%Y-%m-%d')
                            else:
                                date_nav = dt.datetime.strptime(
                                    f'{date_nav[0]}-{date_nav[1]}-{date_nav[2]}', '%y-%m-%d')

                            date_nav = date_nav.strftime('%Y-%m-%d')
                            filter_files_nav[date_nav] = file_nav
                            break
            except Exception:
                self.logger.error("File reading error %s", file_nav, exc_info=True)
                continue
            inc_bar.next()
        inc_bar.finish()

        inc_bar = IncrementalBar('Match files - Progress', max=len(files_obs),
                                 suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
        if not show_progress:
            inc_bar = disable_progress_bar(inc_bar)

        inc_bar.start()
        for file_obs in files_obs:
            date_obs = ''
            marker_name = ''
            try:
                with open(file_obs, 'r', encoding="utf-8") as f_obs:
                    for line_obs in f_obs:
                        if 'TIME OF FIRST OBS' in line_obs:
                            date_obs = line_obs.split()[:3]
                            date_obs[1] = date_obs[1].zfill(2)
                            date_obs[2] = date_obs[2].zfill(2)
                            date_obs = '-'.join(date_obs)
                        if 'MARKER NAME' in line_obs:
                            marker_name = line_obs.split()[0]
                            if marker_name == "MARKER":
                                marker_name = Path(file_obs).name
                        elif 'END OF HEADER' in line_obs:
                            break
            except Exception:
                self.logger.error("File reading error %s", file_obs, exc_info=True)
                continue

            if date_obs in filter_files_nav:
                inc_bar.next()
                match_list[marker_name].append([file_obs, filter_files_nav[date_obs]])

        inc_bar.finish()

        return dict(match_list)

    @type_check((object, "input_data"), (bool, "recursion"), (bool, "show_progress"), (str, "output_files_xtr"))
    def start(self, input_data: dict | tuple, recursion: bool = False, show_progress: bool = True,
              output_files_xtr: str = None) -> dict:

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
                match_list = self.scan_dirs(input_data[0], input_data[1], recursion, show_progress)
            else:
                raise ValueError("Path to file or dir is strange.")
        else:
            raise TypeError("The type of the 'input_data' variable should be 'tuple' or 'dict'.")

        for marker_name, matchs in match_list.items():
            inc_bar = IncrementalBar(f'Anubis - {marker_name} - progress',
                                     max=len(matchs),
                                     suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
            if not show_progress:
                inc_bar = disable_progress_bar(inc_bar)

            inc_bar.start()
            for match in matchs:
                date = ''
                if len(match) != 2:
                    self.logger.error("Some file is missing %s", match)
                    inc_bar.next()
                    continue

                cmd = []

                anubis_path = str(Path(__file__).resolve().parent.parent.parent)
                anubis_path = anubis_path + '/bin/Anubis/app/anubis'
                cmd += [anubis_path]

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
                xtr.text = f'{match[0]}.xtr'

                # создание временного файла конфига
                path_conf = ''
                while True:
                    folder_conf = os.path.join(
                        Path(__file__).resolve().parent.parent.parent, 'conf')
                    alphabet = string.ascii_letters + string.digits
                    name_conf = ''.join(random.choice(alphabet) for i in range(6))
                    path_conf = os.path.join(folder_conf, name_conf) + '.xml'
                    direct = Path(path_conf)
                    if not direct.exists():
                        break
                tree = ET.ElementTree(conf)
                tree.write(path_conf)
                self.path_conf4del = path_conf
                self.path_xtr4del = f'{match[0]}.xtr'

                cmd += ["-x", path_conf]

                self.logger.info('Start Anubis')
                subprocess.run(cmd, stderr=subprocess.DEVNULL, check=False)

                try:
                    with open(f'{match[0]}.xtr', 'r', encoding="utf-8") as f:
                        data = f.readlines()
                except Exception:
                    self.logger.error("Something happened to the opening of the Anubis file %s.xtr.", match[0],
                                      exc_info=True)
                    inc_bar.next()
                    continue

                self.logger.info("Start parsing file Anubis %s.xtr", match[0])
                meta_data = {}
                flag_gnssum = False
                flag_data_error = False
                for indx, row in enumerate(data):
                    if '=TOTSUM' in row:
                        row_split = row.split(' ')
                        row_split = list(filter(lambda i: i != '', row_split))
                        date = row_split[1] + " " + row_split[2]
                        try:
                            meta_data["total_time"] = float(row_split[5])
                            meta_data["expt_obs"] = int(row_split[8])
                            meta_data["exis_obs"] = int(row_split[9])
                            meta_data["ratio"] = float(row_split[10])
                            meta_data["expt_obs10"] = int(row_split[13])
                            meta_data["exis_obs10"] = int(row_split[14])
                            meta_data["ratio10"] = float(row_split[15])
                        except Exception:
                            self.logger.warning("Parameter =TOTSUM. Skip %s.", match[0], exc_info=True)
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
                            row_split = list(
                                filter(lambda i: i != '', row_data))
                            name_sys = row_split[0].replace(
                                "=", "").replace("SUM", "")
                            try:
                                meta_data["miss_epoch"][name_sys] = int(row_split[11])
                                meta_data["n_slip"][name_sys] = int(row_split[14])
                            except Exception:
                                self.logger.warning("Parameter =TOTSUM. Skip %s.", match[0], exc_info=True)
                                flag_data_error = True
                                break

                            try:
                                meta_data["code_multi"][name_sys + "MP1"] = float(row_split[18])
                            except ValueError:
                                # self.logger.warning(f'Попался дефис. {e}')
                                meta_data["code_multi"][name_sys + "MP1"] = row_split[18]

                            try:
                                meta_data["code_multi"][name_sys + "MP2"] = float(row_split[19])
                            except ValueError:
                                # self.logger.warning(f'Попался дефис. {e}')
                                meta_data["code_multi"][name_sys + "MP2"] = row_split[19]
                            count += 1

                        meta_data["miss_epoch"] = json.dumps(meta_data["miss_epoch"])
                        meta_data["code_multi"] = json.dumps(meta_data["code_multi"])
                        meta_data["n_slip"] = json.dumps(meta_data["n_slip"])
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
                                self.logger.warning("Parameter =GNSSYS. Skip %s.", match[0], exc_info=True)
                                flag_data_error = True
                                break
                        meta_data["sat_healthy"] = json.dumps(meta_data["sat_healthy"])

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
                        meta_data["sig2noise"] = json.dumps(meta_data["sig2noise"])

                if flag_data_error:
                    self.logger.error("Incorrect data in file %s.xtr.", match[0], exc_info=True)
                    inc_bar.next()
                    continue

                try:
                    data_metric = {'total_time': meta_data['total_time'],
                                   'expt_obs': meta_data['expt_obs'],
                                   'exis_obs': meta_data['exis_obs'],
                                   'ratio': meta_data['ratio'],
                                   'expt_obs10': meta_data['expt_obs10'],
                                   'exis_obs10': meta_data['exis_obs10'],
                                   'ratio10': meta_data["ratio10"],
                                   'miss_epoch': meta_data['miss_epoch'],
                                   'code_multi': meta_data['code_multi'],
                                   'sat_healthy': meta_data['sat_healthy'],
                                   'n_slip': meta_data['n_slip'],
                                   'sig2noise': meta_data['sig2noise']
                                   }

                except KeyError:
                    self.logger.error("Something happened to the output metrics formation", exc_info=True)
                    inc_bar.next()
                    continue

                if isinstance(output_files_xtr, str) and os.path.isdir(output_files_xtr):
                    copy2(f"{match[0]}.xtr", output_files_xtr)

                try:
                    os.remove(match[0]+'.xtr')
                except Exception:
                    self.logger.error("Something happened to remove file %s", match[0], exc_info=True)

                try:
                    os.remove(path_conf)
                except Exception:
                    self.logger.error("Something happened to remove file %s", path_conf, exc_info=True)

                output_list[marker_name][date] = data_metric
                inc_bar.next()
            inc_bar.finish()

        return dict(output_list)

    def __del__(self):
        try:
            os.remove(self.path_conf4del)
        except FileNotFoundError:
            pass

        try:
            os.remove(self.path_xtr4del)
        except FileNotFoundError:
            pass
