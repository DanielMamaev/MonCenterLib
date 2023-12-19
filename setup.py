import os
from pathlib import Path
import urllib.request
import zipfile
from shutil import copy2
from setuptools import setup, find_packages


PATH_BASE = Path(__file__).resolve().parent


def read_requirements() -> list:
    with open(PATH_BASE.joinpath("requirements.txt"), "r", encoding="utf-8") as f:
        list_req = list(map(lambda x: x.replace("\n", ""), f.readlines()))
        return list_req


def setup_rtklib():
    url2rtklib = "http://danisimo.ru:82/index.php/s/GfJ7br5wQwMuZfx/download"

    # download RTKLib zip file
    print("Download RTKLib zip file")
    path2rtklib_zip = PATH_BASE.joinpath("bin", "rtklib.zip")
    urllib.request.urlretrieve(url2rtklib, path2rtklib_zip)

    # unzip RTKLib zip file
    print("Unzip RTKLib zip file")
    with zipfile.ZipFile(path2rtklib_zip, 'r') as zip_file:
        zip_file.extractall(PATH_BASE.joinpath("bin"))

    # make RTKLib
    print("Make RTKLib")
    path2rtklib = PATH_BASE.joinpath("bin", "RTKLIB-2.4.3-b34")
    os.system(f"cd {path2rtklib.joinpath('lib', 'iers', 'gcc')} && make")
    os.system(f"cd {path2rtklib.joinpath('app', 'consapp', 'str2str', 'gcc')} && make")
    os.system(f"cd {path2rtklib.joinpath('app', 'consapp', 'convbin', 'gcc')} && make")
    os.system(f"cd {path2rtklib.joinpath('app', 'consapp', 'rnx2rtkp', 'gcc')} && make")

    copy2(path2rtklib.joinpath('app', 'consapp', 'str2str', 'gcc', 'str2str'),
          PATH_BASE.joinpath("moncenterlib", "gnss", "bin", "str2str"))
    copy2(path2rtklib.joinpath('app', 'consapp', 'convbin', 'gcc', 'convbin'),
          PATH_BASE.joinpath("moncenterlib", "gnss", "bin", "convbin"))
    copy2(path2rtklib.joinpath('app', 'consapp', 'rnx2rtkp', 'gcc', 'rnx2rtkp'),
          PATH_BASE.joinpath("moncenterlib", "gnss", "bin", "rnx2rtkp"))


def setup_anubis():
    url2rtklib = "http://danisimo.ru:82/index.php/s/pjKGC0Ank72rCkX/download"

    # download Anubis zip file
    print("Download Anubis tgz file")
    path2anubis_zip = PATH_BASE.joinpath("bin", "anubis.zip")
    urllib.request.urlretrieve(url2rtklib, path2anubis_zip)

    # unzip Anubis zip file
    print("Unzip Anubis zip file")
    with zipfile.ZipFile(path2anubis_zip, 'r') as zip_file:
        zip_file.extractall(PATH_BASE.joinpath("bin"))

    # make Anubis
    print('Make Anubis')
    os.system(f"chmod -R 755 {PATH_BASE.joinpath('bin', 'Anubis')}")
    os.system(f"cd {PATH_BASE.joinpath('bin', 'Anubis')} && ./autogen.sh")

    copy2(PATH_BASE.joinpath('bin', 'Anubis', "app", "anubis"),
          PATH_BASE.joinpath("moncenterlib", "gnss", "bin", "anubis"))


if __name__ == '__main__':
    setup_rtklib()
    setup_anubis()

    setup(
        name='moncenterlib',
        version='0.1',
        packages=find_packages(),
        install_requires=read_requirements(),
        include_package_data=True,
        package_data={'': [str(PATH_BASE.joinpath("moncenterlib", "gnss", "bin", "*"))]},
    )
