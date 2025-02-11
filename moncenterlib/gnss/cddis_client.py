"""
This module is designed to download one or more GNSS files from the CDDIS archive.
This simplifies the process of searching and downloading various types of files. This automates your process.
See more here: https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/GNSS_data_and_product_archive.html

Learn more about the specific class.

"""
from logging import Logger
from ftplib import FTP_TLS
import os
import gzip
import shutil
import subprocess
from datetime import datetime, timedelta
import charset_normalizer
from typeguard import typechecked
from gps_time import GPSTime
from moncenterlib.tools import create_simple_logger, files_check


class CDDISClient:
    """

    """
    @typechecked
    def __init__(self, logger: bool | Logger | None = None) -> None:
        """
        Args:
            logger (bool | Logger, optional): if the logger is None, a logger will be created inside the default class.
                If the logger is False, then no information will be output.
                If you pass an instance of your logger, the information output will be implemented according to your logger.
                Defaults to None.
        """
        self.logger = logger

        if self.logger in [None, False]:
            self.logger = create_simple_logger("CDDISCLient", logger)

    @typechecked
    def _generate_list_dates(self, start_day: datetime, end_day: datetime) -> list[datetime]:
        temp_day = start_day
        list_days: list[datetime] = []
        for _ in range((end_day - start_day).days + 1):
            list_days.append(temp_day)
            temp_day += timedelta(1)
        return list_days

    @typechecked
    def get_daily_multi_gnss_brd_eph(self, output_dir: str, query: dict | list, unpack: bool = True) -> dict:
        """This method allows you to download Daily RINEX V3 GNSS Broadcast Ephemeris Files or Daily Multi-GNSS Broadcast Ephemeris Files.
        These are the format files BRDC00IGS_R_YYYYDDDHHMM_01D_MN.rnx.gz and BRDM00DLR_S_YYYYDDDHHMM_01D_MN.rnx.gz accordingly.
        Daily RINEX V3 GNSS Broadcast Ephemeris Files are downloaded as a priority.
        If no such file was found, then the Daily Multi-GNSS Broadcast Ephemeris Files are downloaded.
        See more here: https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/broadcast_ephemeris_data.html

        Args:
            output_dir (str): The path where the files should be saved.
            query (dict | list): A request may containing a start date and an end date.
                Example: {"start": "2020-12-30", "end": "2021-12-30"}. Format date = YYYY-MM-DD.
                Also you can use list of dates. Example: ["2020-12-30", "2021-12-31"]
            unpack (bool, optional): Deleting an archive after unpacking. Defaults to True.

        Raises:
            ValueError: Path to output_dir is strange.
            KeyError: The query must have the start and end keys.
            ValueError: Start day must be less than or equal to end day.

        Returns:
            dict: The dictionary contains 3 keys. done, no_exists, no_found_dates.
            The done key stores a list of files that have been successfully created.
            The no_exists key stores a list of files that have not been created.
            The no_found_dates key stores a list of dates that have not been found.

        Examples:
            >>> cddiscli = CDDISClient()
            >>> query = {"start": "2020-12-30", "end": "2021-01-02"}
            >>> # or query = ["2020-12-30", "2024-05-05"]
            >>> res = cddiscli.get_daily_multi_gnss_brd_eph("/output_dir", query)
            >>> res
            {
                "done": ["file_1", "file_2"],
                "no_exists": [],
                "no_found_dates": []
            }
        """

        if not os.path.isdir(output_dir):
            raise ValueError("Path to output_dir is strange.")

        list_dates = []
        output_file_list = []
        no_found_dates = []

        if isinstance(query, dict):
            if not query.get("start", None) or not query.get("end", None):
                raise KeyError("The query must have the start and end keys.")

            start_day = datetime.strptime(query["start"], "%Y-%m-%d")
            end_day = datetime.strptime(query["end"], "%Y-%m-%d")
            if start_day > end_day:
                raise ValueError("Start day must be less than or equal to end day.")
            list_dates = self._generate_list_dates(start_day, end_day)
        elif isinstance(query, list):
            list_dates = [datetime.strptime(date, "%Y-%m-%d") for date in query]

        self.logger.info('Connect to CDDIS FTP.')
        with FTP_TLS('gdc.cddis.eosdis.nasa.gov', timeout=300) as ftps:
            ftps.login(user='anonymous', passwd='anonymous')
            ftps.prot_p()
            ftps.set_pasv(True)

            for date in list_dates:
                year = date.strftime("%Y")
                num_day = date.strftime("%j")

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
                        no_found_dates.append(date.strftime("%Y-%m-%d"))
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

                if unpack:
                    self.logger.info('Start unpack %s', output_file_gz)
                    try:
                        with gzip.open(output_file_gz, 'rb') as f_in:
                            with open(output_file_rnx, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                    except Exception as e:
                        self.logger.error('Something happened to unpack %s. %s', output_file_gz, e)
                        continue

                    output_file_list.append(output_file_rnx)

                    try:
                        os.remove(output_file_gz)
                    except Exception as e:
                        self.logger.error('Something happened to delete %s. %s', output_file_gz, e)
                        continue
                else:
                    output_file_list.append(output_file_gz)

        output_dict = files_check(output_file_list)
        output_dict["no_found_dates"] = no_found_dates
        return output_dict

    @typechecked
    def _search_daily_30s_data_v2(self, ftps: FTP_TLS, query: dict, num_day: str,
                                  year_short: str, dir_on_ftp: str) -> str:
        temp_name_file = ""
        name_file = ""
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
            else:
                name_file = temp_name_file
        return name_file

    @typechecked
    def _search_daily_30s_data_v3(self, ftps: FTP_TLS, query: dict, num_day: str, year: str, dir_on_ftp: str) -> str:
        self.logger.info('Searching station %s', query["station"])
        name_file = ""
        file_lst = []
        try:
            file_lst = ftps.nlst(dir_on_ftp)
        except Exception as e:
            self.logger.error('Something happened to get list file of date %s-%s. %s', year, num_day, e)
            return ""

        file_lst = [file.replace(dir_on_ftp, "") for file in file_lst]
        for file in file_lst:
            file_split = file.split("_")
            if (query["station"].upper() in file_split[0] and
                    year+num_day in file_split[2] and file_split[3] == "01D"):
                name_file = file
        if name_file == "":
            self.logger.error('Station %s not found in %s-%s.', query["station"], year, num_day)
        return name_file

    @typechecked
    def get_daily_30s_data(self, output_dir: str, query: dict, unpack=True) -> dict:
        """This method allows you to download Daily 30-second data. It is possible to select a range of days.
        Also select the station, file type and RINEX version.
        See more here: https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/daily_30second_data.html

        Args:
            output_dir (str): The path where the files should be saved.
            query (dict): The dictionary should contain the following keys.
            "dates" - range of dates or list of dates, "station" - station name (list or str),
            "type" - file type (list or str), "rinex_v" - RINEX version (2, 3, auto).
            unpack (bool, optional): Deleting an archive after unpacking. Defaults to True.

        Raises:
            ValueError: Path to output_dir is strange.
            KeyError: Invalid query.
            ValueError: Start day must be less than or equal to end day.
            ValueError: Rinex version 3 doesn't support.
            ValueError: Unknow rinex version.

        Returns:
            dict: The dictionary contains 3 keys. done, no_exists, no_found_dates.
            The done key stores a list of files that have been successfully created.
            The no_exists key stores a list of files that have not been created.
            The no_found_dates key stores a list of dates that have not been found.

        Examples:
            >>> cddiscli = CDDISClient()
            >>> query = {"dates": {"start": "2020-12-30", "end": "2021-01-02"}, "station": "NOVM", "type": "o", "rinex_v": "2"}
            >>> # or query = {"dates": ["2020-12-12", "2024-05-05"], "station": "NOVM", "type": "o", "rinex_v": "2"}
            >>> res = cddiscli.get_daily_30s_data("/output_path", query))
            >>> res
            {
                "done": ["file_1", "file_2"],
                "no_exists": [],
                "no_found_dates": []
            }
        """

        if not os.path.isdir(output_dir):
            raise ValueError("Path to output_dir is strange.")

        if (not query.get("dates", None) or
            not query.get("station", None) or
            not query.get("rinex_v", None) or
                not query.get("type", None)):
            raise KeyError("Invalid query.")

        list_dates = []
        output_file_list = []
        no_found_dates = []

        if isinstance(query["dates"], dict):
            if (not query["dates"].get("start", None) or not query["dates"].get("end", None)):
                raise KeyError("Invalid query.")
            start_day = datetime.strptime(query["dates"]["start"], "%Y-%m-%d")
            end_day = datetime.strptime(query["dates"]["end"], "%Y-%m-%d")
            if start_day > end_day:
                raise ValueError("Start day must be less than or equal to end day.")
            list_dates = self._generate_list_dates(start_day, end_day)
        elif isinstance(query["dates"], list):
            list_dates = [datetime.strptime(date, "%Y-%m-%d") for date in query["dates"]]
        else:
            raise ValueError("Type of variable of dates should be dict or list.")

        stations = []
        if isinstance(query["station"], str):
            stations.append(query["station"])
        elif isinstance(query["station"], list):
            stations = query["station"]
        else:
            raise ValueError("Type of variable of station should be str or list.")

        types_file = []
        if isinstance(query["type"], str):
            types_file.append(query["type"])
        elif isinstance(query["type"], list):
            types_file = query["type"]
        else:
            raise ValueError("Type of variable of type should be str or list.")

        self.logger.info('Connect to CDDIS FTP.')
        with FTP_TLS('gdc.cddis.eosdis.nasa.gov', timeout=300) as ftps:
            ftps.login(user='anonymous', passwd='anonymous')
            ftps.prot_p()
            ftps.set_pasv(True)

            for date in list_dates:
                year = date.strftime("%Y")
                year_short = date.strftime("%y")
                num_day = date.strftime("%j")

                for station in stations:
                    for type_file in types_file:
                        query_temp = {
                            "station": station,
                            "type": type_file,
                        }

                        dir_on_ftp = f"gnss/data/daily/{year}/{num_day}/{year_short}{query_temp['type'].lower()}/"
                        name_file = ""
                        if query["rinex_v"] == "2":
                            name_file = self._search_daily_30s_data_v2(
                                ftps,
                                query_temp,
                                num_day,
                                year_short,
                                dir_on_ftp
                            )
                            if name_file == "":
                                no_found_dates.append(date.strftime("%Y-%m-%d"))
                                continue
                        elif query["rinex_v"] == "3":
                            name_file = self._search_daily_30s_data_v3(ftps, query_temp, num_day, year, dir_on_ftp)
                            if name_file == "":
                                no_found_dates.append(date.strftime("%Y-%m-%d"))
                                continue
                        elif query["rinex_v"] == "auto":
                            name_file = self._search_daily_30s_data_v2(
                                ftps, query_temp, num_day, year_short, dir_on_ftp)
                            if name_file == "":
                                name_file = self._search_daily_30s_data_v3(ftps, query_temp, num_day, year, dir_on_ftp)
                                if name_file == "":
                                    no_found_dates.append(date.strftime("%Y-%m-%d"))
                                    continue
                        else:
                            raise ValueError("Unknow rinex version.")

                        self.logger.info('File %s downloading', name_file)
                        output_file_zip = os.path.join(output_dir, name_file)
                        try:
                            ftps.retrbinary(f"RETR {dir_on_ftp}{name_file}", open(output_file_zip, 'wb').write)
                        except Exception as e:
                            self.logger.error('Something happened to download %s. %s', output_file_zip, e)
                            continue

                        if unpack:
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
                                    continue

                            output_file_list.append(output_file_rnx)

                            try:
                                os.remove(output_file_zip)
                            except Exception as e:
                                self.logger.error('Something happened to delete %s. %s', output_file_zip, e)
                                continue
                        else:
                            output_file_list.append(output_file_zip)

        output_dict = files_check(output_file_list)
        output_dict["no_found_dates"] = no_found_dates
        return output_dict

    @typechecked
    def _week_products(self, type_prod: str, output_dir: str, query: dict | list, unpack=True) -> dict:
        """
        Args:
            type_prod (str): Type of product. (sp3, clk_5m, clk_30s, erp).
            output_dir (str): The path where the files should be saved.
            query (dict | list): A request containing a start date and an end date.
                Example: {"start": "2020-12-30", "end": "2021-12-30"}. Format date = YYYY-MM-DD
            unpack (bool, optional): Deleting an archive after unpacking. Defaults to True.

        Raises:
            ValueError: Path to output_dir is strange.
            KeyError: The query must have the start and end keys.
            ValueError: Start day must be less than or equal to end day.
            ValueError: Unknow type of product.

        Returns:
            dict: The dictionary contains 3 keys. done, no_exists, no_found_dates.
            The done key stores a list of files that have been successfully created.
            The no_exists key stores a list of files that have not been created.
            The no_found_dates key stores a list of dates that have not been found.
        """
        if not os.path.isdir(output_dir):
            raise ValueError("Path to output_dir is strange.")

        list_dates = []
        output_file_list = []
        no_found_dates = []

        if isinstance(query, dict):
            if not query.get("start", None) or not query.get("end", None):
                raise KeyError("The query must have the start and end keys.")

            start_day = datetime.strptime(query["start"], "%Y-%m-%d")
            end_day = datetime.strptime(query["end"], "%Y-%m-%d")
            if start_day > end_day:
                raise ValueError("Start day must be less than or equal to end day.")
            list_dates = self._generate_list_dates(start_day, end_day)
        elif isinstance(query, list):
            list_dates = [datetime.strptime(date, "%Y-%m-%d") for date in query]

        self.logger.info('Connect to CDDIS FTP.')
        with FTP_TLS('gdc.cddis.eosdis.nasa.gov', timeout=300) as ftps:
            ftps.login(user='anonymous', passwd='anonymous')
            ftps.prot_p()
            ftps.set_pasv(True)

            last_names_erp_files = []

            for date in list_dates:
                gps_week = GPSTime.from_datetime(date).week_number
                gps_day = int(GPSTime.from_datetime(date).time_of_week / (24 * 60 * 60))

                year = date.strftime("%Y")
                num_day = date.strftime("%j")

                dir_on_ftp = f"/gnss/products/{gps_week}/"
                name_file = ""
                temp_name_file_old = ""
                temp_name_file_new = ""
                if type_prod == "sp3":
                    temp_name_file_old = f"igs{gps_week}{gps_day}.sp3.Z"
                    temp_name_file_new = f"IGS0OPSFIN_{year}{num_day}0000_01D_15M_ORB.SP3.gz"
                elif type_prod == "erp":
                    temp_name_file_old = f"igs{gps_week}7.erp.Z"
                    start_of_week = GPSTime(gps_week).to_datetime()
                    start_year = start_of_week.strftime("%Y")
                    start_day = start_of_week.strftime("%j")
                    temp_name_file_new = f"IGS0OPSFIN_{start_year}{start_day}0000_07D_01D_ERP.ERP.gz"

                    if last_names_erp_files == [temp_name_file_old, temp_name_file_new]:
                        continue
                    last_names_erp_files = [temp_name_file_old, temp_name_file_new]
                elif type_prod == "clk_5m":
                    temp_name_file_old = f"igs{gps_week}{gps_day}.clk.Z"
                    temp_name_file_new = f"IGS0OPSFIN_{year}{num_day}0000_01D_05M_CLK.CLK.gz"
                elif type_prod == "clk_30s":
                    temp_name_file_old = f"igs{gps_week}{gps_day}.clk_30s.Z"
                    temp_name_file_new = f"IGS0OPSFIN_{year}{num_day}0000_01D_30S_CLK.CLK.gz"
                else:
                    raise ValueError("Unknow type of product.")

                self.logger.info('Searching file %s', temp_name_file_old)
                try:
                    ftps.size(dir_on_ftp + temp_name_file_old)
                except Exception:
                    self.logger.warning('File %s not found.', temp_name_file_old)
                else:
                    name_file = temp_name_file_old

                if name_file == "":
                    self.logger.info('Searching file %s', temp_name_file_new)
                    try:
                        ftps.size(dir_on_ftp + temp_name_file_new)
                    except Exception:
                        self.logger.error('File %s not found.', temp_name_file_new)
                        no_found_dates.append(date.strftime("%Y-%m-%d"))
                        continue
                    else:
                        name_file = temp_name_file_new

                self.logger.info('File %s downloading', name_file)
                output_file_zip = os.path.join(output_dir, name_file)
                try:
                    ftps.retrbinary(f"RETR {dir_on_ftp}{name_file}", open(output_file_zip, 'wb').write)
                except Exception as e:
                    self.logger.error('Something happened to download %s. %s', output_file_zip, e)
                    continue

                if unpack:
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
                            continue

                    if output_file_rnx not in output_file_list:
                        output_file_list.append(output_file_rnx)

                    try:
                        os.remove(output_file_zip)
                    except Exception as e:
                        self.logger.error('Something happened to delete %s. %s', output_file_zip, e)
                        continue
                else:
                    output_file_list.append(output_file_zip)

        output_dict = files_check(output_file_list)
        output_dict["no_found_dates"] = no_found_dates
        return output_dict

    @typechecked
    def get_precise_orbits(self, output_dir: str, query: dict | list, unpack=True) -> dict:
        """A method for downloading files of final precise orbits (SP3).
        See more here: https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/orbit_products.html

        Args:
            output_dir (str): The path where the files should be saved.
            query (dict | list): A request may containing a start date and an end date.
                Example: {"start": "2020-12-30", "end": "2021-12-30"}. Format date = YYYY-MM-DD.
                Also you can use list of dates. Example: ["2020-12-30", "2021-12-31"]
            unpack (bool, optional): Deleting an archive after unpacking. Defaults to True.

        Returns:
            dict: The dictionary contains 3 keys. done, no_exists, no_found_dates.
            The done key stores a list of files that have been successfully created.
            The no_exists key stores a list of files that have not been created.
            The no_found_dates key stores a list of dates that have not been found.

        Examples:
            >>> cddiscli = CDDISClient()
            >>> query = {"start": "2020-12-30", "end": "2021-01-02"}
            >>> # or query = ["2020-12-30", "2024-05-05"]
            >>> res = cddiscli.get_precise_orbits("/output_dir", query)
            >>> res
            {
                "done": ["file_1", "file_2"],
                "no_exists": [],
                "no_found_dates": []
            }
        """
        return self._week_products("sp3", output_dir, query, unpack)

    @typechecked
    def get_clock_30s(self, output_dir: str, query: dict | list, unpack=True) -> dict:
        """A method for downloading files of final station clock solutions (CLK 30 seconds).
        See more here: https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/clock_products.html

        Args:
            output_dir (str): The path where the files should be saved.
            query (dict | list): A request may containing a start date and an end date.
                Example: {"start": "2020-12-30", "end": "2021-12-30"}. Format date = YYYY-MM-DD.
                Also you can use list of dates. Example: ["2020-12-30", "2021-12-31"]
            unpack (bool, optional): Deleting an archive after unpacking. Defaults to True.

        Returns:
            dict: The dictionary contains 3 keys. done, no_exists, no_found_dates.
            The done key stores a list of files that have been successfully created.
            The no_exists key stores a list of files that have not been created.
            The no_found_dates key stores a list of dates that have not been found.

        Examples:
            >>> cddiscli = CDDISClient()
            >>> query = {"start": "2020-12-30", "end": "2021-01-02"}
            >>> # or query = ["2020-12-30", "2024-05-05"]
            >>> res = cddiscli.get_clock_30s("/output_dir", query)
            >>> res
            {
                "done": ["file_1", "file_2"],
                "no_exists": [],
                "no_found_dates": []
            }
        """
        return self._week_products("clk_30s", output_dir, query, unpack)

    @typechecked
    def get_clock_5m(self, output_dir: str, query: dict | list, unpack=True) -> dict:
        """A method for downloading files of final station clock solutions (CLK 5 minutes).
        See more here: https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/clock_products.html

        Args:
            output_dir (str): The path where the files should be saved.
            query (dict | list): A request may containing a start date and an end date.
                Example: {"start": "2020-12-30", "end": "2021-12-30"}. Format date = YYYY-MM-DD.
                Also you can use list of dates. Example: ["2020-12-30", "2021-12-31"]
            unpack (bool, optional): Deleting an archive after unpacking. Defaults to True.

        Returns:
            dict: The dictionary contains 3 keys. done, no_exists, no_found_dates.
            The done key stores a list of files that have been successfully created.
            The no_exists key stores a list of files that have not been created.
            The no_found_dates key stores a list of dates that have not been found.

        Examples:
            >>> cddiscli = CDDISClient()
            >>> query = {"start": "2020-12-30", "end": "2021-01-02"}
            >>> # or query = ["2020-12-30", "2024-05-05"]
            >>> res = cddiscli.get_clock_5m("/output_dir", query)
            >>> res
            {
                "done": ["file_1", "file_2"],
                "no_exists": [],
                "no_found_dates": []
            }
        """
        return self._week_products("clk_5m", output_dir, query, unpack)

    @typechecked
    def get_earth_orientation(self, output_dir: str, query: dict | list, unpack=True) -> dict:
        """A method for downloading files of final Earth rotation parameters (ERP).
        See more here: https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/orbit_products.html

        Args:
            output_dir (str): The path where the files should be saved.
            query (dict | list): A request may containing a start date and an end date.
                Example: {"start": "2020-12-30", "end": "2021-12-30"}. Format date = YYYY-MM-DD.
                Also you can use list of dates. Example: ["2020-12-30", "2021-12-31"]
            unpack (bool, optional): Deleting an archive after unpacking. Defaults to True.

        Returns:
            dict: The dictionary contains 3 keys. done, no_exists, no_found_dates.
            The done key stores a list of files that have been successfully created.
            The no_exists key stores a list of files that have not been created.
            The no_found_dates key stores a list of dates that have not been found.

        Examples:
            >>> cddiscli = CDDISClient()
            >>> query = {"start": "2020-12-30", "end": "2021-01-20"}
            >>> # or query = ["2020-12-30", "2024-05-05"]
            >>> res = cddiscli.get_earth_orientation("/output_dir", query)
            >>> res
            {
                "done": ["file_1", "file_2"],
                "no_exists": [],
                "no_found_dates": []
            }
        """
        return self._week_products("erp", output_dir, query, unpack)
