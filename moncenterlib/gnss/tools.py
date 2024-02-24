import os
from pathlib import Path
import platform
import logging
from logging import Logger
from datetime import datetime

PATH_BASE = Path(__file__).resolve().parent


def files_check(files: list) -> dict:
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


def get_path2bin(name_bin) -> str:
    system = platform.system()
    bit_info = platform.machine()

    if system == "Linux":
        if bit_info not in ['x86_64', 'aarch64']:
            raise OSError(f"{bit_info} doesn't support")
    else:
        raise OSError(f"{system} doesn't support")

    paths = {
        "x86_64": {
            "anubis": str(Path(__file__).resolve().parent.joinpath("bin/x86_64/anubis_2.3_x86_64_linux")),
            "str2str": str(Path(__file__).resolve().parent.joinpath("bin/x86_64/str2str_2.4.3-34_x86_64_linux")),
            "convbin": str(Path(__file__).resolve().parent.joinpath("bin/x86_64/convbin_2.4.3-34_x86_64_linux")),
            "rnx2rtkp": str(Path(__file__).resolve().parent.joinpath("bin/x86_64/rnx2rtkp_2.4.3-34_x86_64_linux"))
        },
        "aarch64": {
            "anubis": str(Path(__file__).resolve().parent.joinpath("bin/aarch64/anubis_2.3_aarch64_linux")),
            "str2str": str(Path(__file__).resolve().parent.joinpath("bin/aarch64/str2str_2.4.3-34_aarch64_linux")),
            "convbin": str(Path(__file__).resolve().parent.joinpath("bin/aarch64/convbin_2.4.3-34_aarch64_linux")),
            "rnx2rtkp": str(Path(__file__).resolve().parent.joinpath("bin/aarch64/rnx2rtkp_2.4.3-34_aarch64_linux"))
        }
    }

    path2bin = paths[bit_info][name_bin]
    return path2bin


class NoLoggingFilter(logging.Filter):
    def __init__(self, flag: bool = True) -> None:
        self.flag = flag
        super().__init__()

    def filter(self, record):
        return self.flag


def create_simple_logger(name: str, disable_output: bool) -> Logger:
    logger = logging.getLogger(name)
    if disable_output is False:
        logger.filters = [NoLoggingFilter(False)]
    else:
        logger.setLevel(logging.INFO)
        logger.filters = [NoLoggingFilter(True)]

    if not logger.handlers:
        handlers = logging.StreamHandler()
        handlers.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        handlers.setFormatter(formatter)
        logger.addHandler(handlers)

    return logger


def get_files_from_dir(input_dir: str, recursion: bool) -> list[str]:
    output_files = []
    if os.path.isdir(input_dir):
        if recursion:
            for root, _, files in os.walk(input_dir):
                for file in files:
                    path = os.path.join(root, file)
                    output_files.append(path)
        else:
            temp_lst = []
            for file in os.listdir(input_dir):
                if os.path.isfile(os.path.join(input_dir, file)):
                    temp_lst.append(os.path.join(input_dir, file))
            output_files = temp_lst
    else:
        raise ValueError("Path to dir is strange.")

    return output_files


def get_start_date_from_nav(file_nav: str) -> str:
    date_nav: list[str] = []
    with open(file_nav, 'r', encoding="utf-8") as f_nav:
        data = f_nav.readlines()
        for i, line in enumerate(data):
            if 'END OF HEADER' in line:
                date_nav = data[i + 1].split()[1:4]
                # for rinex v1,2
                if len(date_nav[0]) == 2:
                    if 80 <= int(date_nav[0]) <= 99:
                        date_nav[0] = "19" + date_nav[0]
                    elif 0 <= int(date_nav[0]) <= 79:
                        date_nav[0] = "20" + date_nav[0]

                date_nav[1] = date_nav[1].zfill(2)
                date_nav[2] = date_nav[2].zfill(2)
                break
    return "-".join(date_nav)


def get_start_date_from_obs(file_obs: str) -> str:
    date_obs = ""
    with open(file_obs, 'r', encoding="utf-8") as f_obs:
        for line_obs in f_obs:
            if 'TIME OF FIRST OBS' in line_obs:
                date_obs = line_obs.split()[:3]
                date_obs[1] = date_obs[1].zfill(2)
                date_obs[2] = date_obs[2].zfill(2)
                date_obs = '-'.join(date_obs)
    return date_obs


def get_marker_name(file: str) -> str:
    marker_name = ""
    with open(file, 'r', encoding="utf-8") as f:
        for line_obs in f:
            if 'MARKER NAME' in line_obs:
                marker_name = line_obs.split()[0]
                if marker_name == "MARKER":
                    marker_name = Path(file).name
    return marker_name
