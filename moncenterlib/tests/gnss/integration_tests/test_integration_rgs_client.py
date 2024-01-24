import tempfile
import os
from unittest import TestCase, main
from moncenterlib.gnss.rgs_client import RGSClient


class TestRGSClient(TestCase):
    def setUp(self) -> None:
        API_TOKEN = os.getenv("RGS_API_KEY")
        self.rgs_cli = RGSClient(API_TOKEN, False, False)

    def test_get_info_list_of_files(self):
        filter_param = {
            "working_center": "NSK1",
            "date": "2022-01-01",
            "type": "O"
        }
        result = self.rgs_cli.get_info_list_of_files(filter_param)
        self.assertEqual(list, type(result))
        self.assertGreaterEqual(len(result), 1)

        self.assertEqual(dict, type(result[0]))
        self.assertGreaterEqual(len(result[0]), 1)

    def test_get_station_info(self):
        result = self.rgs_cli.get_station_info("NSK1")
        self.assertGreaterEqual(len(result), 1)
        self.assertEqual(dict, type(result))

    def test_get_all_stations_info(self):
        result = self.rgs_cli.get_all_stations_info()
        self.assertGreaterEqual(len(result), 1)
        self.assertEqual(list, type(result))
        self.assertEqual(dict, type(result[0]))

    def test_download_files_1(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            filter_param = {
                "working_center": "NSK1",
                "date": "2020-01-01",
                "type": "O",
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param)
            self.assertEqual([f"{temp_dir}/nsk10010.20o"], result["done"])

        with tempfile.TemporaryDirectory() as temp_dir:
            # year and day
            filter_param = {
                "working_center": "NSK1",
                "year": "2020",
                "day": "2",
                "type": "O",
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param)
            self.assertEqual([f"{temp_dir}/nsk10020.20o"], result["done"])

        with tempfile.TemporaryDirectory() as temp_dir:
            # gps_week and gps_week_day
            filter_param = {
                "working_center": "NSK1",
                "gps_week": "2086",
                "gps_week_day": "5",
                "type": "O",
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param)
            self.assertEqual([f"{temp_dir}/nsk10030.20o"], result["done"])

        with tempfile.TemporaryDirectory() as temp_dir:
            # other type file
            filter_param = {
                "working_center": "NSK1",
                "date": "2020-01-01",
                "type": "N",
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param)
            self.assertEqual([f"{temp_dir}/nsk10010.20n"], result["done"])

    def test_download_files_more_dates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # date
            filter_param = {
                "working_center": "NSK1",

                "date[0]": "2020-01-01",
                "date[1]": "2020-01-02",

                "type[0]": "O",
                "type[1]": "N",
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param)
            self.assertEqual([f"{temp_dir}/nsk10020.20n",
                              f"{temp_dir}/nsk10020.20o",
                              f"{temp_dir}/nsk10010.20n",
                              f"{temp_dir}/nsk10010.20o"],
                             result["done"])

        with tempfile.TemporaryDirectory() as temp_dir:
            filter_param = {
                "working_center": "NSK1",

                "date[from]": "2020-01-04",
                "date[to]": "2020-01-05",

                "type": "O"
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param)
            self.assertEqual([f"{temp_dir}/nsk10050.20o",
                              f"{temp_dir}/nsk10040.20o",],
                             result["done"])

    def test_download_files_more_year_day(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # year and day
            filter_param = {
                "working_center": "NSK1",

                "year[0]": "2020",
                "year[1]": "2021",

                "day[0]": "10",
                "day[1]": "11",

                "type": "O",
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param)
            self.assertEqual([f"{temp_dir}/nsk10110.21o",
                              f"{temp_dir}/nsk10100.21o",
                              f"{temp_dir}/nsk10110.20o",
                              f"{temp_dir}/nsk10100.20o"],
                             result["done"])

        with tempfile.TemporaryDirectory() as temp_dir:
            filter_param = {
                "working_center": "NSK1",

                "year[from]": "2018",
                "year[to]": "2020",

                "day[from]": "22",
                "day[to]": "23",

                "type": "O",
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param)
            self.assertEqual([f"{temp_dir}/nsk10230.20o",
                              f"{temp_dir}/nsk10220.20o",
                              f"{temp_dir}/nsk10230.18o",
                              f"{temp_dir}/nsk10220.18o"],
                             result["done"])

    def test_download_files_more_gps_week(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # gps_week and gps_week_day
            filter_param = {
                "working_center": "NSK1",

                "gps_week[0]": "2086",
                "gps_week[1]": "2088",

                "gps_week_day[0]": "5",
                "gps_week_day[1]": "1",

                "type": "O",
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param)
            self.assertEqual([f"{temp_dir}/nsk10170.20o",
                              f"{temp_dir}/nsk10130.20o",
                              f"{temp_dir}/nsk10030.20o",
                              f"{temp_dir}/nsk13640.19o"],
                             result["done"])

        with tempfile.TemporaryDirectory() as temp_dir:
            filter_param = {
                "working_center": "NSK1",

                "gps_week[from]": "2086",
                "gps_week[to]": "2087",

                "gps_week_day[from]": "1",
                "gps_week_day[to]": "2",

                "type": "O",
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param)
            self.assertEqual([f"{temp_dir}/nsk10070.20o",
                              f"{temp_dir}/nsk10060.20o",
                              f"{temp_dir}/nsk13650.19o",
                              f"{temp_dir}/nsk13640.19o"],
                             result["done"])

    def test_download_files_several_station(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            filter_param = {
                "working_center[0]": "NSK1",
                "working_center[1]": "ARKH",
                "working_center[2]": "SAMR",

                "date": "2020-01-01",
                "type": "O"
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param)
            self.assertEqual([f"{temp_dir}/arkh0010.20o",
                              f"{temp_dir}/nsk10010.20o",
                              f"{temp_dir}/samr0010.20o"],
                             result["done"])

    def test_download_files_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            filter_param = {
                "working_center": "NSK1",
                "date": "2020-01-01",
                "type": "O"
            }
            result = self.rgs_cli.download_files(temp_dir, filter_param, unpack=False)
            self.assertEqual([f"{temp_dir}/nsk10010.20o.gz"], result["done"])


if __name__ == "__main__":
    main()
