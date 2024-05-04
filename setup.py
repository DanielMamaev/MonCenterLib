from pathlib import Path
from setuptools import setup, find_packages


PATH_BASE = Path(__file__).resolve().parent


def read_requirements() -> list:
    with open(PATH_BASE.joinpath("requirements.txt"), "r", encoding="utf-8") as f:
        list_req = list(map(lambda x: x.replace("\n", ""), f.readlines()))
        return list_req


if __name__ == '__main__':
    setup(
        name='moncenterlib',
        version='1.0.0',
        packages=find_packages(),
        install_requires=read_requirements(),
        include_package_data=True,
        package_data={'moncenterlib.gnss': [str(PATH_BASE.joinpath("moncenterlib", "gnss", "bin", "aarch64", "*")),
                                            str(PATH_BASE.joinpath("moncenterlib", "gnss", "bin", "x86_64", "*")),
                                            str(PATH_BASE.joinpath("moncenterlib", "gnss", "conf", "*"))]},
    )
