"""
This module is designed to download one or more GNSS files from the CDDIS archive.
This simplifies the process of searching and downloading various types of files. This automates your process.
See more here: https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/GNSS_data_and_product_archive.html

Learn more about the specific class.

"""

import logging
import logging.config
from ftplib import FTP_TLS
import os
import gzip
import shutil
import subprocess
from datetime import datetime, timedelta
import charset_normalizer
from typeguard import typechecked
from moncenterlib.gnss.tools import files_check


class CDDISClient:
    def __init__(self, logger=None):
        self.logger = logger

        if not self.logger:
            conf_log = {
                "version": 1,
                "formatters": {
                    "default": {
                        "format": "{asctime} {name} {levelname} {message}",
                        "style": "{",
                    },
                },
                "handlers": {
                    "stream_handler": {
                        "level": "INFO",
                        "class": "logging.StreamHandler",
                        "formatter": "default",
                        "filters": [],
                    },
                },
                "loggers": {
                    "CDDISCLient": {
                        "level": "INFO",
                        "handlers": ["stream_handler"],
                    },
                }
            }
            logging.config.dictConfig(conf_log)
            self.logger = logging.getLogger('CDDISCLient')

    @typechecked
    def get_daily_multi_gnss_brd_eph(self, output_dir: str, query: dict, delete_gz: bool = True) -> dict:
        """This method allows you to download Daily RINEX V3 GNSS Broadcast Ephemeris Files or Daily Multi-GNSS Broadcast Ephemeris Files.
        These are the format files BRDC00IGS_R_YYYYDDDHHMM_01D_MN.rnx.gz and BRDM00DLR_S_YYYYDDDHHMM_01D_MN.rnx.gz accordingly.
        Daily RINEX V3 GNSS Broadcast Ephemeris Files are downloaded as a priority.
        If no such file was found, then the Daily Multi-GNSS Broadcast Ephemeris Files are downloaded.
        See more here: https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/broadcast_ephemeris_data.html

        Args:
            output_dir (str): The path where the files should be saved.
            query (dict): A request containing a start date and an end date.
                Example: {"start": "2020-12-30", "end": "2021-12-30"}. Format date = YYYY-MM-DD
            delete_gz (bool, optional): Deleting an archive after unpacking. Defaults to True.

        Raises:
            ValueError: Path to output_dir is strange.
            KeyError: The query must have the start and end keys.
            ValueError: Start day must be less than or equal to end day.

        Returns:
            dict: The dictionary contains 2 keys. Done and error.
            The done key stores a list of files that have been successfully created.
            The error key stores a list of files that have not been created.

        Examples:
            >>> cddiscli = CDDISClient()
            >>> query = {"start": "2020-12-30", "end": "2021-01-02"}
            >>> res = cddiscli.get_daily_multi_gnss_brd_eph("/output_dir", query)
            >>> res
            {
                "done": ["file_1", "file_2"],
                "error": []
            }
        """

        if not os.path.isdir(output_dir):
            raise ValueError("Path to output_dir is strange.")
        if not query.get("start", None) or not query.get("start", None):
            raise KeyError("The query must have the start and end keys.")

        output_file_list = []

        start_day = datetime.strptime(query["start"], "%Y-%m-%d")
        end_day = datetime.strptime(query["end"], "%Y-%m-%d")
        if start_day > end_day:
            raise ValueError("Start day must be less than or equal to end day.")

        self.logger.info('Connect to CDDIS FTP.')
        with FTP_TLS('gdc.cddis.eosdis.nasa.gov') as ftps:
            ftps.login(user='anonymous', passwd='anonymous')
            ftps.prot_p()
            ftps.set_pasv(True)

            # generate list dates
            temp_day = start_day
            list_days: list[datetime] = []
            for _ in range((end_day - start_day).days + 1):
                list_days.append(temp_day)
                temp_day += timedelta(1)

            for day in list_days:
                year = day.strftime("%Y")
                num_day = day.strftime("%j")

                nav_gzip = ''
                dir_on_ftp = f"gnss/data/daily/{year}/brdc/"

                name_file = f"BRDC00IGS_R_{year}{num_day}0000_01D_MN.rnx.gz"
                self.logger.info('Searching file %s', name_file)
                try:
                    ftps.size(dir_on_ftp + name_file)
                except Exception:
                    self.logger.warning('File %s not found.', name_file)
                else:
                    nav_gzip = name_file

                if nav_gzip == "":
                    name_file = f"BRDM00DLR_S_{year}{num_day}0000_01D_MN.rnx.gz"
                    self.logger.info('Searching file %s', name_file)
                    try:
                        ftps.size(dir_on_ftp + name_file)
                    except Exception:
                        self.logger.error('File %s not found.', name_file)
                        continue
                    else:
                        nav_gzip = name_file

                self.logger.info('File %s downloading', nav_gzip)
                output_file_gz = os.path.join(output_dir, nav_gzip)
                output_file_rnx = os.path.join(output_dir, nav_gzip[:-3])
                try:
                    ftps.retrbinary(f"RETR {dir_on_ftp}{nav_gzip}", open(output_file_gz, 'wb').write)
                except Exception as e:
                    self.logger.error('Something happened to download %s. %s', nav_gzip, e)
                    continue

                self.logger.info('Start unpack %s', output_file_gz)
                try:
                    with gzip.open(output_file_gz, 'rb') as f_in:
                        with open(output_file_rnx, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                except Exception as e:
                    self.logger.error('Something happened to unpack %s. %s', output_file_gz, e)
                    continue

                output_file_list.append(output_file_rnx)
                if delete_gz:
                    try:
                        os.remove(output_file_gz)
                    except Exception as e:
                        self.logger.error('Something happened to delete %s. %s', output_file_gz, e)
                        continue

        return files_check(output_file_list)

    @typechecked
    def get_daily_30s_data(self, output_dir: str, query: dict, delete_gz=True) -> dict:
        """This method allows you to download Daily 30-second data. It is possible to select a range of days.
        Also select the station, file type and RINEX version.
        So far, linux version 2 is supported.
        See more here: https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/daily_30second_data.html

        Args:
            output_dir (str): The path where the files should be saved.
            query (dict): The dictionary should contain the following keys. "start" - start date,
                "end"- end date, "station" - station name, "type" - file type, "rinex_v" - RINEX version.
            delete_gz (bool, optional): Deleting an archive after unpacking. Defaults to True.

        Raises:
            ValueError: Path to output_dir is strange.
            KeyError: Invalid query.
            ValueError: Start day must be less than or equal to end day.
            ValueError: Rinex version 3 doesn't support.

        Returns:
            dict: The dictionary contains 2 keys. Done and error.
            The done key stores a list of files that have been successfully created.
            The error key stores a list of files that have not been created.

        Examples:
            >>> cddiscli = CDDISClient()
            >>> query = {"start": "2020-12-30", "end": "2021-01-02", "station": "NOVM", "type": "o", "rinex_v": "2"}
            >>> res = cddiscli.get_daily_30s_data("/output_path", query))
            >>> res
            {
                "done": ["file_1", "file_2"],
                "error": []
            }
        """

        if not os.path.isdir(output_dir):
            raise ValueError("Path to output_dir is strange.")

        if (not query.get("start", None) or
            not query.get("end", None) or
            not query.get("station", None) or
            not query.get("rinex_v", None) or
                not query.get("type", None)):
            raise KeyError("Invalid query.")

        output_file_list = []

        start_day = datetime.strptime(query["start"], "%Y-%m-%d")
        end_day = datetime.strptime(query["end"], "%Y-%m-%d")
        if start_day > end_day:
            raise ValueError("Start day must be less than or equal to end day.")

        self.logger.info('Connect to CDDIS FTP.')
        with FTP_TLS('gdc.cddis.eosdis.nasa.gov') as ftps:
            ftps.login(user='anonymous', passwd='anonymous')
            ftps.prot_p()
            ftps.set_pasv(True)

            # generate list dates
            temp_day = start_day
            list_dates: list[datetime] = []
            for _ in range((end_day - start_day).days + 1):
                list_dates.append(temp_day)
                temp_day += timedelta(1)

            for date in list_dates:
                year = date.strftime("%Y")
                year_short = date.strftime("%y")
                num_day = date.strftime("%j")

                dir_on_ftp = f"gnss/data/daily/{year}/{num_day}/{year_short}{query['type'].lower()}/"
                name_file = ""
                temp_name_file = ""
                if query["rinex_v"] == "2":
                    temp_name_file = f"{query['station'].lower()}{num_day}0.{year_short}{query['type'].lower()}.gz"
                    self.logger.info('Searching file %s', temp_name_file)
                    try:
                        ftps.size(dir_on_ftp + temp_name_file)
                    except Exception:
                        self.logger.warning('File %s not found.', temp_name_file)
                    else:
                        name_file = temp_name_file

                    if name_file == "":
                        temp_name_file = f"{query['station'].lower()}{num_day}0.{year_short}{query['type'].lower()}.Z"
                        self.logger.info('Searching file %s', temp_name_file)
                        try:
                            ftps.size(dir_on_ftp + temp_name_file)
                        except Exception:
                            self.logger.error('File %s not found.', temp_name_file)
                            continue
                        else:
                            name_file = temp_name_file
                elif query["rinex_v"] == "3":
                    raise ValueError("Rinex version 3 doesn't support.")

                self.logger.info('File %s downloading', name_file)
                output_file_zip = os.path.join(output_dir, name_file)
                try:
                    ftps.retrbinary(f"RETR {dir_on_ftp}{name_file}", open(output_file_zip, 'wb').write)
                except Exception as e:
                    self.logger.error('Something happened to download %s. %s', output_file_zip, e)
                    continue

                self.logger.info('Start unpack %s', output_file_zip)
                output_file_rnx = ""
                if name_file.endswith(".gz"):
                    output_file_rnx = os.path.join(output_dir, name_file[:-3])
                    try:
                        with gzip.open(output_file_zip, 'rb') as f_in:
                            with open(output_file_rnx, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                    except Exception as e:
                        self.logger.error('Something happened to unpack %s. %s', output_file_zip, e)
                        continue
                elif name_file.endswith(".Z"):
                    output_file_rnx = os.path.join(output_dir, name_file[:-2])
                    try:
                        with open(output_file_rnx, 'wb') as f_out:
                            subprocess.run(['gunzip', '-c', output_file_zip], stdout=f_out, check=True)

                        with open(output_file_rnx, 'rb') as file:
                            raw_data = file.read(5000)
                        detected_encoding = charset_normalizer.detect(raw_data)['encoding']

                        if detected_encoding.lower() != 'utf-8':
                            with open(output_file_rnx, 'r', encoding=detected_encoding) as file:
                                file_content = file.read()

                            with open(output_file_rnx, 'w', encoding='utf-8') as file:
                                file.write(file_content)
                    except Exception as e:
                        self.logger.error('Something happened to unpack %s. %s', output_file_zip, e)

                output_file_list.append(output_file_rnx)
                if delete_gz:
                    try:
                        os.remove(output_file_zip)
                    except Exception as e:
                        self.logger.error('Something happened to delete %s. %s', output_file_zip, e)
                        continue

        return files_check(output_file_list)
