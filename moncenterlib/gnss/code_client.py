

import datetime
import gzip
from logging import Logger
import os
from pathlib import Path
import shutil

from typeguard import typechecked
from gps_time import GPSTime
import requests
import unlzw3

from moncenterlib.tools import create_simple_logger


class CODEClient:
    """
    Client for downloading precise CODE (Center for Orbit Determination in Europe) products for GNSS processing.

    The class downloads files from the AIUB/CODE archive:
    ``http://ftp.aiub.unibe.ch/CODE``.
    Supported product types are ``ION``, ``ERP``, ``SP3``, ``CLK``,
    ``CLK_05S``, ``DCB_P1C1``, and ``DCB_P1P2``.
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
            self.logger = create_simple_logger("CODEClient", logger)

    @typechecked
    def _make_rnx2_name(self, date: datetime.datetime, type_file: str) -> str:
        start_name = "COD"
        types_file_rnxv2 = {
            "ION": ".ION.Z",
            "ERP": ".ERP.Z",
            "SP3": ".EPH.Z",
            "CLK": ".CLK.Z",
            "CLK_05S": ".CLK_05S.Z"
        }
        gps_week = GPSTime.from_datetime(date).week_number
        gps_day = int(GPSTime.from_datetime(date).time_of_week / (24 * 60 * 60))

        if type_file == "ERP":
            file_name = f"{start_name}{gps_week}7{types_file_rnxv2[type_file]}"
            return file_name
        file_name = f"{start_name}{gps_week}{gps_day}{types_file_rnxv2[type_file]}"
        return file_name

    @typechecked
    def _make_rnx3_name(self, date: datetime.datetime, type_file: str) -> str:
        start_name = "COD0OPSFIN"
        types_file_rnxv3 = {
            "ION": "01D_01H_GIM.ION.gz",
            "ERP": "01D_01D_ERP.ERP.gz",
            "SP3": "01D_05M_ORB.SP3.gz",
            "CLK": "01D_30S_CLK.CLK.gz",
            "CLK_05S": "01D_05S_CLK.CLK.gz"
        }

        file_date_str = date.strftime("%Y%j%H%M")
        file_name = f"{start_name}_{file_date_str}_{types_file_rnxv3[type_file]}"

        return file_name

    @typechecked
    def _make_dbc_name(self, date: datetime.datetime, type_file: str) -> str:
        year_short = date.strftime("%y")
        month_str = date.strftime("%m")
        file_name = f"{type_file[4:]}{year_short}{month_str}.DCB.Z"
        return file_name

    @typechecked
    def _is_file_exists(self, url: str) -> bool:
        try:
            with requests.head(url, allow_redirects=True, timeout=10) as response:
                if response.status_code == 200:
                    return True
                if response.status_code == 404:
                    return False

            # Some servers do not support HEAD correctly, so fall back to GET.
            with requests.get(url, stream=True, timeout=60) as response:
                return response.status_code == 200
        except requests.RequestException as e:
            self.logger.error("Error checking file existence %s. Error. %s", url, e)
            return False

    @typechecked
    def _download_file(self, url: str, output_path: str) -> bool:
        self.logger.info("Downloading %s", url)
        try:
            with requests.get(url, stream=True, timeout=60) as response:
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        shutil.copyfileobj(response.raw, f)
                    self.logger.info("Completed %s", output_path)
                    return True
            self.logger.error(
                "Failed to download file %s. HTTP status code: %s",
                url,
                response.status_code
            )
            return False
        except (OSError, requests.RequestException) as e:
            self.logger.error("Error downloading file %s. Error. %s", url, e)
            return False

    @typechecked
    def _unzip_gz(self, file_path) -> bool:
        self.logger.info("Unpacking file %s", file_path)
        unzipped_path = file_path[:-3]
        try:
            with gzip.open(file_path, "rb") as f_in:
                with open(unzipped_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            self.logger.info("File unpacked %s", unzipped_path)
            return True
        except Exception as e:
            self.logger.error("Error unpacking file %s. Error. %s", file_path, e)
            return False

    @typechecked
    def _unzip_z(self, file_path) -> bool:
        self.logger.info("Unpacking file %s", file_path)
        path = Path(file_path)
        try:
            data = path.read_bytes()
            decoded = unlzw3.unlzw(data)
            path.with_suffix("").write_bytes(decoded)
            self.logger.info("File unpacked %s", path.with_suffix(""))
            return True
        except Exception as e:
            self.logger.error("Error unpacking file %s. Error. %s", file_path, e)
            return False

    @typechecked
    def download(
        self,
        dates: dict | list,
        type_file: str,
        output_dir: str,
        remove_archive: bool = True
    ) -> None:
        """Download CODE products for the requested dates.

        Available product types: ION, ERP, SP3, CLK, CLK_05S, DCB_P1C1, DCB_P1P2

        Args:
            dates (dict | list): Either a dictionary with ``start`` and ``end``
                keys in ``YYYY-MM-DD`` format, or a list of date strings in the
                same format.
            type_file (str): Product type to download.
            output_dir (str): Directory where downloaded files will be saved.
            remove_archive (bool, optional): Remove the original archive after
                successful unpacking. Defaults to ``True``.

        Raises:
            ValueError: If ``type_file`` is unknown or ``output_dir`` does not exist.
            TypeError: If ``dates`` is not a dict with ``start``/``end`` keys or
                a list of date strings.

        Examples:
            >>> code_client = CODEClient()
            >>> code_client.download(
            ...     dates={"start": "2024-01-01", "end": "2024-01-03"},
            ...     type_file="SP3",
            ...     output_dir="/tmp/code_products"
            ... )
            >>> code_client.download(
            ...     dates=["2024-01-01", "2024-01-15"],
            ...     type_file="DCB_P1C1",
            ...     output_dir="/tmp/code_products",
            ...     remove_archive=False
            ... )
        """
        base_url = "http://ftp.aiub.unibe.ch/CODE"

        date_list = []

        types_file = ["ION", "ERP", "SP3", "CLK", "CLK_05S", "DCB_P1C1", "DCB_P1P2"]
        if type_file not in types_file:
            self.logger.error("Unknown file type %s", type_file)
            raise ValueError(f"Unknown file type {type_file}")

        if not os.path.isdir(output_dir):
            self.logger.error("Output directory does not exist")
            raise ValueError("Output directory does not exist")

        if isinstance(dates, dict):
            start_date = datetime.datetime.strptime(dates["start"], "%Y-%m-%d")
            end_date = datetime.datetime.strptime(dates["end"], "%Y-%m-%d")

            current_date = start_date
            while current_date <= end_date:
                date_list.append(current_date)
                current_date += datetime.timedelta(days=1)
        elif isinstance(dates, list):
            date_list = [datetime.datetime.strptime(d, "%Y-%m-%d") for d in dates]
        else:
            raise TypeError("dates must be dict with 'start'/'end' or list of dates.")

        if "DCB" in type_file:
            unique_months = set()
            unique_date_list = []

            for current_date in date_list:
                year_month = (current_date.year, current_date.month)
                if year_month not in unique_months:
                    unique_months.add(year_month)
                    unique_date_list.append(current_date)

            date_list = unique_date_list

        for current_date in date_list:

            if "DCB" in type_file:
                file_name = self._make_dbc_name(current_date, type_file)
                url = f'{base_url}/{current_date.strftime("%Y")}/{file_name}'
                self.logger.info("Searching for file %s", url)
                if not self._is_file_exists(url):
                    self.logger.error("File %s was not found", url)
                    continue
            else:
                file_name = self._make_rnx3_name(current_date, type_file)
                url = f'{base_url}/{current_date.strftime("%Y")}/{file_name}'
                self.logger.info("Searching for file %s", url)
                if not self._is_file_exists(url):
                    file_name = self._make_rnx2_name(current_date, type_file)
                    url = f'{base_url}/{current_date.strftime("%Y")}/{file_name}'
                    self.logger.info("Searching for file %s", url)
                    if not self._is_file_exists(url):
                        self.logger.error("File %s was not found", url)
                        continue

            output_path = os.path.join(output_dir, file_name)
            if not self._download_file(url, output_path):
                continue

            suffix = Path(output_path).suffix
            if suffix == ".gz":
                if self._unzip_gz(output_path) and remove_archive:
                    os.remove(output_path)
            elif suffix == ".Z":
                if self._unzip_z(output_path) and remove_archive:
                    os.remove(output_path)
