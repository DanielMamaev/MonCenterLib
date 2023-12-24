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
    def get_daily_multi_gnss_brd_eph(self, output_dir: str, query: dict, delete_gz: bool = True) -> list[str]:
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
            list[str]: The list of downloaded files is returned.

        Examples:
            >>> cddiscli = CDDISClient()
            >>> query = {"start": "2020-12-30", "end": "2021-01-02"}
            >>> res = cddiscli.get_daily_multi_gnss_brd_eph("/output_dir", query)
            >>> res
            ["file_1", "file_2"]
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
        try:
            ftps = FTP_TLS(host='gdc.cddis.eosdis.nasa.gov')
            ftps.login(user='anonymous', passwd='anonymous')
            ftps.prot_p()
        except Exception as e:
            self.logger.error("Something happened to the CDDIS connection. %s", e)
            raise

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

            self.logger.info('Start unpack %s', nav_gzip)
            try:
                with gzip.open(output_file_gz, 'rb') as f_in:
                    with open(output_file_rnx, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            except Exception as e:
                self.logger.error('Something happened to unpack %s. %s', nav_gzip, e)
                continue

            output_file_list.append(output_file_rnx)
            if delete_gz:
                try:
                    os.remove(output_file_gz)
                except Exception as e:
                    self.logger.error('Something happened to delete %s. %s', output_file_gz, e)
                    continue
        try:
            ftps.quit()
        except Exception as e:
            self.logger.error("Something happened to close FTP connection. %s", e)

        return output_file_list

    # @typechecked
    # def get_daily_30s_data(self, path_dir, point, year, day, delete_gz=True):
    #     """
    #     TODO
    #     Доделать поиск ринекс 3 версии, пока только 2
    #     Добавить возможность выбора не только файлов измерений но и эфемерид
    #     """

    #     year = str(year)
    #     day = str(day).zfill(3)

    #     self.logger.info(f'Ищем измерения в архиве CDDIS')
    #     try:
    #         ftps = FTP_TLS(host='gdc.cddis.eosdis.nasa.gov')
    #         ftps.login(user='anonymous', passwd='anonymous')
    #         ftps.prot_p()
    #         ftps.cwd(f'gnss/data/daily/{year}/{day}/{year[2:]}o/')
    #         file_lst = ftps.nlst()
    #     except Exception as e:
    #         self.logger.error(f'Что то с доступом к архиву CDDIS. {e}')
    #         raise Exception(f'Что то с доступом к архиву CDDIS. {e}')

    #     obs_gzip = ''
    #     for i in file_lst:
    #         if point+day in i:
    #             obs_gzip = i
    #     if obs_gzip == '':
    #         self.logger.error(f'Не нашел измерения в архиве CDDIS {point}-{year}-{day}.')
    #         raise Exception(f'Не нашел измерения в архиве CDDIS {point}-{year}-{day}.')

    #     self.logger.info(f'Начинаем скачивать файл с архива CDDIS {obs_gzip}')
    #     try:
    #         ftps.retrbinary("RETR " + obs_gzip, open(os.path.join(path_dir, obs_gzip), 'wb').write)
    #     except Exception as e:
    #         self.logger.error(f'Что то случилось со скачиванием файла {obs_gzip} с CDDIS. {e}')
    #         raise Exception(f'Что то случилось со скачиванием файла {obs_gzip} с CDDIS. {e}')

    #     try:
    #         ftps.quit()
    #     except Exception as e:
    #         self.logger.error(e)

    #     self.logger.info(f'Начинаем разархивировать файл {obs_gzip} с архива CDDIS')
    #     try:
    #         with gzip.open(os.path.join(path_dir, obs_gzip), 'rb') as f_in:
    #             with open(os.path.join(path_dir, obs_gzip[:obs_gzip.rfind('.')]), 'wb') as f_out:
    #                 shutil.copyfileobj(f_in, f_out)
    #     except Exception as e:
    #         self.logger.warning(f'Что то случилось с разархвивацией файла {obs_gzip} CDDIS. {e}')
    #         self.logger.info(f'Пробуем другой метод разархивации {obs_gzip} CDDIS.')

    #         zip_path = os.path.join(path_dir, obs_gzip)
    #         decompressed_file_path = os.path.join(path_dir, obs_gzip[:obs_gzip.rfind('.')])
    #         try:
    #             with open(decompressed_file_path, 'wb') as f_out:
    #                 subprocess.run(['gunzip', '-c', zip_path], stdout=f_out, check=True)

    #             # Detecting the encoding of the decompressed file
    #             with open(decompressed_file_path, 'rb') as file:
    #                 raw_data = file.read(5000)
    #             detected_encoding = charset_normalizer.detect(raw_data)['encoding']

    #             if detected_encoding.lower() != 'utf-8':
    #                 with open(decompressed_file_path, 'r', encoding=detected_encoding) as file:
    #                     file_content = file.read()

    #                 with open(decompressed_file_path, 'w', encoding='utf-8') as file:
    #                     file.write(file_content)

    #         except Exception as e:
    #             raise Exception(f'Что то случилось с разархвивацией файла {obs_gzip} CDDIS. {e}')

    #     if delete_gz:
    #         try:
    #             os.remove(os.path.join(path_dir, obs_gzip))
    #         except Exception as e:
    #             self.logger.error(
    #                 f'Что то случилось с удалением файла nav.gzip {os.path.join(path_dir, obs_gzip)}. {e}')

    #     self.logger.handlers.clear()
    #     return os.path.join(path_dir, obs_gzip[:obs_gzip.rfind('.')])
