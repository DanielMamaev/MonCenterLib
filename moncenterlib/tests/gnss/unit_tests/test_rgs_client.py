import os
from unittest import TestCase
from unittest.mock import MagicMock, patch, call
import logging
from logging import Logger
import json
from moncenterlib.gnss.rgs_client import RGSClient


class TestRgsClient(TestCase):
    def test_init_raises(self):
        with self.assertRaises(Exception):
            rgs_cli = RGSClient(None, 123, 123)

        with self.assertRaises(ValueError):
            rgs_cli = RGSClient("")

    def test_init_with_enable_logger(self):
        rgs_cli = RGSClient("123", True, None)
        self.assertEqual("123", rgs_cli.api_token)
        self.assertTrue(rgs_cli.ssl)
        self.assertEqual(Logger, type(rgs_cli.logger))
        self.assertEqual("RGSClient", rgs_cli.logger.name)

    def test_init_with_disable_logger(self):
        rgs_cli = RGSClient("123", False, False)
        self.assertEqual("123", rgs_cli.api_token)
        self.assertFalse(rgs_cli.ssl)
        self.assertEqual(Logger, type(rgs_cli.logger))
        self.assertEqual("RGSClient", rgs_cli.logger.name)

    def test_init_with_my_logger(self):
        logger = logging.getLogger()
        rgs_cli = RGSClient("123", logger=logger)
        self.assertEqual(logger, rgs_cli.logger)
        self.assertEqual("root", rgs_cli.logger.name)

    def test_init_check_dublicate_handlers(self):
        rgs_cli = RGSClient("123")
        rgs_cli = RGSClient("123")
        self.assertEqual(1, len(rgs_cli.logger.handlers))

    def test_get_info_list_of_files_raises(self):
        rgs_cli = RGSClient(" ", logger=False)
        with self.assertRaises(Exception):
            rgs_cli.get_info_list_of_files(None)

    def test_get_info_list_of_files(self):
        with patch("moncenterlib.gnss.rgs_client.RGSClient._request") as mock_request:
            return_value = [{"info1": "1"}, {"info2": "2"}]
            mock_request.return_value = return_value

            rgs_cli = RGSClient(" ", logger=False)
            filter_param = {"param1": "1", "param2": "2"}
            res = rgs_cli.get_info_list_of_files(filter_param)

            self.assertEqual(return_value, res)
            self.assertEqual(('files', {'param1': '1', 'param2': '2'}), mock_request.mock_calls[0].args)

    def test_get_station_info_raises(self):
        rgs_cli = RGSClient(" ", logger=False)
        with self.assertRaises(Exception):
            rgs_cli.get_station_info(None)

    def test_get_station_info(self):
        with patch("moncenterlib.gnss.rgs_client.RGSClient._request") as mock_request:
            return_value = {"info1": "1", "info2": "2"}
            mock_request.return_value = return_value

            rgs_cli = RGSClient(" ", logger=False)
            fags_name = "test"
            res = rgs_cli.get_station_info(fags_name)
            self.assertEqual(return_value, res)
            self.assertEqual(('fags/TEST', {}), mock_request.mock_calls[0].args)

            mock_request.mock_calls = []
            fags_name = "TESt2"
            res = rgs_cli.get_station_info(fags_name)
            self.assertEqual(return_value, res)
            self.assertEqual(('fags/TEST2', {}), mock_request.mock_calls[0].args)

    def test_get_all_stations_info(self):
        with patch("moncenterlib.gnss.rgs_client.RGSClient._request") as mock_request:
            return_value = [{"info1": "1"}, {"info2": "2"}]
            mock_request.return_value = return_value

            rgs_cli = RGSClient(" ", logger=False)
            res = rgs_cli.get_all_stations_info()

            self.assertEqual(return_value, res)
            self.assertEqual(('fags', {}), mock_request.mock_calls[0].args)

    def test_download_files_raises(self):
        rgs_cli = RGSClient(" ", logger=False)

        with self.assertRaises(Exception):
            rgs_cli.download_files(None, None, None)

        with (patch("moncenterlib.gnss.rgs_client.RGSClient._request") as mock_request,
              patch("moncenterlib.gnss.rgs_client.RGSClient._download_file")):

            with self.assertRaises(ValueError):
                rgs_cli.download_files("", {})

            # exception from get_info_list_of_files
            mock_request.side_effect = Exception()
            with self.assertRaises(Exception) as msg:
                rgs_cli.download_files("/", {})

            mock_request.return_value = []
            mock_request.side_effect = None
            with self.assertRaises(Exception) as msg:
                rgs_cli.download_files("/", {})
            self.assertEqual(str(msg.exception), "List information about files is empty.")

    def test_download_files(self):
        with (patch("moncenterlib.gnss.rgs_client.RGSClient._request") as mock_request,
              patch("moncenterlib.gnss.rgs_client.RGSClient._download_file") as mock_download_file):
            rgs_cli = RGSClient(" ", logger=False)

            mock_request.return_value = [{"name": "something1"}, {"name": "something2"}]
            mock_download_file.side_effect = Exception()

            res = rgs_cli.download_files("/", {})
            self.assertEqual({'done': [], 'error': []}, res)
            self.assertEqual([call('something1', '/', True), call('something2', '/', True)],
                             mock_download_file.mock_calls)

            mock_download_file.mock_calls = []
            mock_download_file.side_effect = ["path1", "path2"]
            res = rgs_cli.download_files("/", {}, unpack=False)
            self.assertEqual({'done': [], 'error': ["path1", "path2"]}, res)
            self.assertEqual([call('something1', '/', False), call('something2', '/', False)],
                             mock_download_file.mock_calls)

    def test__download_file(self):
        rgs_cli = RGSClient(" ", logger=False)

        with self.assertRaises(Exception):
            rgs_cli._download_file(None, None, None)

        unpack = True
        filename = "file.txt.gz"
        output_dir = "/output_dir"
        data_from_gz = "some_data".encode()

        with (patch("moncenterlib.gnss.rgs_client.RGSClient._request") as mock_request,
              patch("moncenterlib.gnss.rgs_client.gzip.decompress") as mock_gzip,
              patch("moncenterlib.gnss.rgs_client.open") as mock_open):
            mock_gzip.return_value = data_from_gz
            mock_write = MagicMock()
            mock_open.return_value.__enter__.return_value.write = mock_write

            path_file = rgs_cli._download_file(filename, output_dir, unpack)

            self.assertEqual("/output_dir/file.txt", path_file)
            self.assertEqual(call('file/file.txt.gz', {}, json_mode=False), mock_request.mock_calls[0])
            self.assertTrue(mock_gzip.called)
            self.assertEqual(call('/output_dir/file.txt', 'w', encoding='utf-8'), mock_open.mock_calls[0])
            self.assertEqual(call('some_data'), mock_write.mock_calls[0])

        unpack = False
        filename = "file.txt.gz"
        output_dir = "/output_dir"
        data_from_request = "some_data".encode()
        with (patch("moncenterlib.gnss.rgs_client.RGSClient._request") as mock_request,
              patch("moncenterlib.gnss.rgs_client.open") as mock_open):

            mock_request.return_value = data_from_request
            mock_write = MagicMock()
            mock_open.return_value.__enter__.return_value.write = mock_write

            path_file = rgs_cli._download_file(filename, output_dir, unpack)

            self.assertEqual("/output_dir/file.txt.gz", path_file)
            self.assertEqual(call('file/file.txt.gz', {}, json_mode=False), mock_request.mock_calls[0])
            self.assertEqual(call('/output_dir/file.txt.gz', 'wb'), mock_open.mock_calls[0])
            self.assertEqual(call(b'some_data'), mock_write.mock_calls[0])

    def test__request_raises(self):
        rgs_cli = RGSClient(" ", logger=False)

        with self.assertRaises(Exception):
            rgs_cli._request(None, None, None)

        with (patch("moncenterlib.gnss.rgs_client.requests.Session") as mock_requests,
              patch("moncenterlib.gnss.rgs_client.json.loads") as mock_json_loads):

            mock_get = MagicMock()
            mock_get.side_effect = Exception()
            mock_requests.return_value.__enter__.return_value.get = mock_get
            with self.assertRaises(Exception):
                rgs_cli._request("None", {}, True)
            self.assertTrue(mock_get.called)

            mock_json_loads.side_effect = Exception()
            mock_requests.return_value.__enter__.return_value.get.side_effect = None
            mock_response = MagicMock()
            mock_response.content = b"some_content"
            mock_requests.return_value.__enter__.return_value.get.return_value = mock_response
            with self.assertRaises(Exception):
                rgs_cli._request("None", {}, True)
            self.assertTrue(mock_json_loads.called)

    def test__request(self):
        rgs_cli = RGSClient(" ", logger=False)

        with (patch("moncenterlib.gnss.rgs_client.requests.Session") as mock_requests):
            # check get with param
            mock_get = MagicMock()
            mock_requests.return_value.__enter__.return_value.get = mock_get
            mock_response = MagicMock()
            mock_response.content = b"some_content"
            mock_get.return_value = mock_response
            with self.assertRaises(Exception):
                rgs_cli._request("fags", {"param1": 1, "param2": 2}, True)

            self.assertEqual(('https://rgs.cgkipd.ru/api/fags?param1=1&param2=2&api_token= ',),
                             mock_get.mock_calls[0].args)
            self.assertEqual({'headers':
                              {
                                  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
                              },
                              'verify': True
                              }, mock_get.mock_calls[0].kwargs)

            self.assertEqual(rgs_cli.ssl, mock_get.mock_calls[0].kwargs["verify"])

            # check get without param
            mock_get.mock_calls = []
            with self.assertRaises(Exception):
                rgs_cli._request("fags", {}, True)

            self.assertEqual(('https://rgs.cgkipd.ru/api/fags?api_token= ',),
                             mock_get.mock_calls[0].args)
            self.assertEqual({'headers':
                              {
                                  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
                              },
                              'verify': True
                              }, mock_get.mock_calls[0].kwargs)

            self.assertEqual(rgs_cli.ssl, mock_get.mock_calls[0].kwargs["verify"])

            # check json mode True
            mock_get.mock_calls = []
            exp_dict = {"something1": 1, "something2": 2}
            mock_response.content = json.dumps(exp_dict).encode()
            res = rgs_cli._request("fags", {}, True)
            self.assertEqual(exp_dict, res)
            self.assertEqual(rgs_cli.ssl, mock_get.mock_calls[0].kwargs["verify"])

            # check json mode False
            mock_get.mock_calls = []
            mock_response.content = b"some_content"
            res = rgs_cli._request("fags", {}, False)
            self.assertEqual(b"some_content", res)
            self.assertEqual(rgs_cli.ssl, mock_get.mock_calls[0].kwargs["verify"])
