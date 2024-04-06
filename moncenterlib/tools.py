import logging
from logging import Logger
import os
from pathlib import Path
import platform


def get_path2bin(name_bin) -> str:
    system = platform.system()
    bit_info = platform.machine()

    if system == "Linux":
        if bit_info not in ['x86_64', 'aarch64']:
            raise OSError(f"{bit_info} doesn't support")
    else:
        raise OSError(f"{system} doesn't support")
    
    path_base = Path(__file__).resolve().parent

    paths = {
        "x86_64": {
            "anubis": str(path_base.joinpath("gnss/bin/x86_64/anubis_2.3_x86_64_linux")),
            "str2str": str(path_base.joinpath("gnss/bin/x86_64/str2str_2.4.3-34_x86_64_linux")),
            "convbin": str(path_base.joinpath("gnss/bin/x86_64/convbin_2.4.3-34_x86_64_linux")),
            "rnx2rtkp": str(path_base.joinpath("gnss/bin/x86_64/rnx2rtkp_2.4.3-34_x86_64_linux"))
        },
        "aarch64": {
            "anubis": str(path_base.joinpath("gnss/bin/aarch64/anubis_2.3_aarch64_linux")),
            "str2str": str(path_base.joinpath("gnss/bin/aarch64/str2str_2.4.3-34_aarch64_linux")),
            "convbin": str(path_base.joinpath("gnss/bin/aarch64/convbin_2.4.3-34_aarch64_linux")),
            "rnx2rtkp": str(path_base.joinpath("gnss/bin/aarch64/rnx2rtkp_2.4.3-34_aarch64_linux"))
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


def get_files_from_dir(input_dir: str, recursion: bool) -> list:
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
        raise ValueError(f"Path '{input_dir}' to dir is strange.")

    return output_files


def files_check(files: list) -> dict:
    output_check = {
        'done': [],
        'no_exists': []
    }

    for file in files:
        direct = Path(file)
        if direct.exists():
            output_check['done'].append(file)
        else:
            output_check['no_exists'].append(file)

    return output_check
