"""
This module allows you to download various GNSS files from the service https://rgs-centre.ru
This module can.
1) Download different files from different stations.
2) Get information about one or all stations.
3) Get information about files.

Learn more about the specific class.

See example code in example folder.
"""
import gzip
import json
import os
import logging
from logging import Logger
import requests
from typeguard import typechecked
from moncenterlib.gnss.tools import files_check


class RGSClient:
    """
    """

    def __init__(self, api_token: str, ssl: bool = True, logger: bool | Logger = None) -> None:
        """
        Args:
            api_token (str): API token from personal account of rgs-centre.
            ssl (bool, optional): It may be that the rgs-centre will not have a security certificate.
                Then access to this service will be unavailable.
                To restore access, you must set the value to False.
                But be careful. It's not safe.. Defaults to True.
            logger (bool | Logger, optional): if the logger is None, a logger will be created inside the default class.
                If the logger is False, then no information will be output.
                If you pass an instance of your logger, the information output will be implemented according to your logger.
                Defaults to None.
        """

        self.ssl = ssl

        self.path = 'https://rgs-centre.ru/api'
        self.api_token = api_token

        self.logger = logger

        if self.logger in [None, False]:
            self.logger = logging.getLogger('RGSCLient')
            if logger is False:
                self.logger.setLevel(logging.NOTSET)
            else:
                self.logger.setLevel(logging.INFO)

            handlers = logging.StreamHandler()
            handlers.setLevel(logging.INFO)

            formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
            handlers.setFormatter(formatter)
            self.logger.addHandler(handlers)

    def _download_file(self, filename: str, output_dir: str, unpack: bool) -> str:
        output_path_file: str = os.path.join(output_dir, filename)
        if unpack:
            data = gzip.decompress(self._request(f'file/{filename}', {}, json_mode=False)).decode()
            output_path_file = output_path_file.replace('.gz', '')
            with open(output_path_file, 'w', encoding="utf-8") as out:
                out.write(data)
        else:
            data = self._request(f'file/{filename}', {}, json_mode=False)
            with open(output_path_file, 'wb') as out:
                out.write(data)

        return output_path_file

    @typechecked
    def _request(self, method: str, filter_param: dict, json_mode: bool = True):
        filter_param['api_token'] = self.api_token

        request = method + '?' + '&'.join([f'{key}={value}' for key, value in filter_param.items()])

        request = '/'.join((self.path, request))

        with requests.Session() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
            }

            try:
                response = session.get(request, headers=headers, verify=self.ssl)
            except Exception as e:
                self.logger.error("Something happened to request %s. %s", request, e)

            if json_mode:
                try:
                    response = json.loads(response.content.decode())
                except Exception:
                    self.logger.error("Something happened to decode json. Check the request.")
                    raise
            else:
                response = response.content

            return response

    @typechecked
    def get_info_list_of_files(self, filter_param: dict) -> list[dict]:
        """Get information about files.

        Args:
            filter_param (dict): filter. See exaples code or https://rgs-centre.ru/rest-api

        Returns:
            list[dict]: A list with information of files.

        Examples:
            >>> rgs_cli = RGSClient("your_api")
            >>> param = {"working_center": "NSK1", "date": "2022-01-01", "type": "O"}
            >>> res = rgs_cli.get_info_list_of_files(param)
            >>> res
            [{
                'id': 450675, 'type': 'O',
                'name': 'NSK100RUS_R_20220010000_01D_30S_MO.rnx.gz',
                'original_name': 'NSK100RUS_R_20220010000_01D_30S_MO.rnx',
                'date': '2022-01-01', 'year': 2022, 'day': 1, 'gps_week': 2190, 'gps_week_day': 6,
                'rinex_version': 3.04
            }]
        """
        return self._request('files', filter_param)

    @typechecked
    def station_info(self, fags_name: str) -> dict:
        """Get information of station.
        See name of stations here: https://rgs-centre.ru/fags-map or https://rgs-centre.ru/fags-coords

        Args:
            fags_name (str): Station name.

        Returns:
            dict: A dictionary with station information is returned.

        Examples:
            >>> rgs_cli = RGSClient("your_api")
            >>> res = rgs_cli.fags_info("NSK1")
            >>> res
            {
                'name': 'NSK1', 'iers_number': None,
                'x': 447670.3, 'y': 3638117.39, 'z': 5202281.56,
                'vx': -0.027, 'vy': 0.003, 'vz': -0.004,
                'b': 55.01225551, 'l': 82.98501852, 'h': 141.68742225,
                'vb': -0.00077, 'vl': 0.0003, 'vh': 0.01248,
                'vn': -0.00203, 've': 0.02716, 'vu': -0.00346,
                'receiver': 'LEICA GR50', 'antenna': 'LEIAR20         LEIM'
            }
        """
        return self._request(f'fags/{fags_name.upper()}', {})

    def get_all_stations_info(self) -> list[dict]:
        """Get all informations of stations.

        Returns:
            list[dict]: A list with information of stations.

        Examples:
            >>> rgs_cli = RGSClient("your_api")
            >>> res = rgs_cli.get_all_stations_info()
            >>> res
            [{some_info1}, {some_info2}]
        """
        return self._request('fags', {})

    @typechecked
    def download_files(self, output_dir: str, filter_param: dict, unpack=True) -> dict:
        """Downloading files according to the specified request

        Args:
            output_dir (str): The path where the files should be saved.
            filter_param (dict): filter. See exaples code or https://rgs-centre.ru/rest-api
            unpack (bool, optional): Unpack archive. Defaults to True.

        Raises:
            Exception: List information about files is empty.

        Returns:
            dict: The dictionary contains 2 keys. Done and error.
            The done key stores a list of files that have been successfully created.
            The error key stores a list of files that have not been created.
        """
        files_list = []
        output_path_list = []
        self.logger.info('Start get information about files.')
        try:
            files_list = self.get_info_list_of_files(filter_param)
        except Exception as e:
            self.logger.error('Something happened to get information about files %s.', e)
            raise

        if files_list == [] or files_list is None:
            self.logger.error('List information about files is empty.')
            raise Exception('List information about files is empty.')

        self.logger.info('Start download files.')
        for file in files_list:
            self.logger.info("File %s downloading.", file['name'])

            try:
                output_path_list.append(self._download_file(file['name'], output_dir, unpack))
            except Exception as e:
                self.logger.error("Something happened to download file %s. %s.", file['name'], e)

        return files_check(output_path_list)
