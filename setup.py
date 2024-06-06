from pathlib import Path
from setuptools import setup, find_packages


PATH_BASE = Path(__file__).resolve().parent


def readme():
    with open('README.md', 'r') as f:
        return f.read()


def read_requirements() -> list:
    with open(PATH_BASE.joinpath("requirements.txt"), "r", encoding="utf-8") as f:
        list_req = list(map(lambda x: x.replace("\n", ""), f.readlines()))
        return list_req


if __name__ == '__main__':
    setup(
        name='moncenterlib',
        version='1.0.3',
        author='Daniel Mamaev',
        author_email='moncenter@moncenter.ru',
        description=('MonCenterLib is a python library for geodetic monitoring. The library contains programs,'
                     'designed to collect, process, analyze and visualize data for geodetic time series.'),
        long_description=readme(),
        long_description_content_type='text/markdown',
        url='https://github.com/DanielMamaev/MonCenterLib',
        packages=find_packages(),
        install_requires=read_requirements(),
        include_package_data=True,
        package_data={'moncenterlib.gnss': [str(PATH_BASE.joinpath("moncenterlib", "gnss", "bin", "aarch64", "*")),
                                            str(PATH_BASE.joinpath("moncenterlib", "gnss", "bin", "x86_64", "*")),
                                            str(PATH_BASE.joinpath("moncenterlib", "gnss", "conf", "*"))]},
        classifiers=[
            'Programming Language :: Python :: 3.10',
            'Operating System :: POSIX :: Linux'
        ],
        keywords='python',
        project_urls={
            'Documentation': 'https://moncenterlib.readthedocs.io/',
            'Source': 'https://github.com/DanielMamaev/MonCenterLib',
        },
        python_requires='>=3.10'
    )
