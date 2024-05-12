from datetime import datetime
from unittest import TestCase, main
from unittest.mock import MagicMock, patch, call
import logging
from logging import Logger
from moncenterlib.gnss.cddis_client import CDDISClient


class TestCddisClient(TestCase):
    def test_init_raises(self):
        with self.assertRaises(Exception):
            cddis_cli = CDDISClient("None")

    def test_init_with_enable_logger(self):
        cddis_cli = CDDISClient()
        self.assertEqual(Logger, type(cddis_cli.logger))
        self.assertEqual("CDDISCLient", cddis_cli.logger.name)

    def test_init_with_disable_logger(self):
        cddis_cli = CDDISClient(False)
        self.assertEqual(Logger, type(cddis_cli.logger))
        self.assertEqual("CDDISCLient", cddis_cli.logger.name)

    def test_init_with_my_logger(self):
        logger = logging.getLogger()
        cddis_cli = CDDISClient(logger=logger)
        self.assertEqual(logger, cddis_cli.logger)
        self.assertEqual("root", cddis_cli.logger.name)

    def test_init_check_dublicate_handlers(self):
        cddis_cli = CDDISClient()
        cddis_cli = CDDISClient()
        self.assertEqual(1, len(cddis_cli.logger.handlers))

    def test__generate_list_dates(self):
        cddis_cli = CDDISClient(False)
        with self.assertRaises(Exception):
            cddis_cli._generate_list_dates(None, None)

        start_day = datetime(2020, 1, 1)
        end_day = datetime(2020, 1, 1)
        res = cddis_cli._generate_list_dates(start_day, end_day)
        self.assertEqual([datetime(2020, 1, 1)], res)

        start_day = datetime(2020, 1, 1)
        end_day = datetime(2020, 1, 2)
        res = cddis_cli._generate_list_dates(start_day, end_day)
        self.assertEqual([datetime(2020, 1, 1), datetime(2020, 1, 2)], res)

        start_day = datetime(2020, 1, 2)
        end_day = datetime(2020, 1, 1)
        res = cddis_cli._generate_list_dates(start_day, end_day)
        self.assertEqual([], res)

    def test__search_daily_30s_data_v2(self):
        cddis_cli = CDDISClient(False)
        with self.assertRaises(Exception):
            cddis_cli._search_daily_30s_data_v2(None, None, None, None, None)

        with patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps:
            # name with .gz
            query = {
                "station": "AAAA",
                "type": "O",
            }
            res = cddis_cli._search_daily_30s_data_v2(mock_ftps, query, "001", "22", "/dir/")
            self.assertEqual("aaaa0010.22o.gz", res)

            # name with .Z
            mock_size = MagicMock()
            mock_size.side_effect = [Exception(), True]
            mock_ftps.size = mock_size

            res = cddis_cli._search_daily_30s_data_v2(mock_ftps, query, "001", "22", "/dir/")
            self.assertEqual("aaaa0010.22o.Z", res)

            # second size return exeption
            mock_size = MagicMock()
            mock_size.side_effect = [Exception(), Exception()]
            mock_ftps.size = mock_size

            res = cddis_cli._search_daily_30s_data_v2(mock_ftps, query, "001", "22", "/dir/")
            self.assertEqual("", res)

    def test__search_daily_30s_data_v3(self):
        cddis_cli = CDDISClient(False)

        with self.assertRaises(Exception):
            cddis_cli._search_daily_30s_data_v3(None, None, None, None, None)

        with patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps:
            # ftp error
            mock_nlst = MagicMock()
            mock_nlst.side_effect = Exception()
            mock_ftps.nlst = mock_nlst

            query = {
                "station": "AAAA",
                "type": "O",
            }
            res = cddis_cli._search_daily_30s_data_v3(mock_ftps, query, "001", "2022", "/dir/")
            self.assertEqual("", res)

            # find file
            mock_nlst.side_effect = None
            list_files_ftp = ["/dir/BBBB_aaa_2022001_01D_aaa", "/dir/AAAA_aaa_2022001_01D_aaa"]
            mock_nlst.return_value = list_files_ftp
            mock_ftps.nlst = mock_nlst

            query = {
                "station": "AAAA",
                "type": "O",
            }
            res = cddis_cli._search_daily_30s_data_v3(mock_ftps, query, "001", "2022", "/dir/")
            self.assertEqual("AAAA_aaa_2022001_01D_aaa", res)

            # no find file
            list_files_ftp = ["/dir/BBBB_aaa_2022001_01D_aaa", "/dir/AAAB_aaa_2022001_01D_aaa"]
            mock_nlst.return_value = list_files_ftp
            mock_ftps.nlst = mock_nlst

            query = {
                "station": "AAAA",
                "type": "O",
            }
            res = cddis_cli._search_daily_30s_data_v3(mock_ftps, query, "001", "2022", "/dir/")
            self.assertEqual("", res)

            # no list file
            list_files_ftp = []
            mock_nlst.return_value = list_files_ftp
            mock_ftps.nlst = mock_nlst

            query = {
                "station": "AAAA",
                "type": "O",
            }
            res = cddis_cli._search_daily_30s_data_v3(mock_ftps, query, "001", "2022", "/dir/")
            self.assertEqual("", res)

    def test__week_products_raises(self):
        cddis_cli = CDDISClient(False)

        with self.assertRaises(Exception):
            cddis_cli._week_products(None, None, None, None)

        with self.assertRaises(ValueError) as msg:
            cddis_cli._week_products("", "None", {})
        self.assertEqual(str(msg.exception), "Path to output_dir is strange.")

        with self.assertRaises(KeyError) as msg:
            cddis_cli._week_products("", "/", {})
        self.assertEqual(str(msg.exception), "'The query must have the start and end keys.'")

        with self.assertRaises(KeyError) as msg:
            cddis_cli._week_products("", "/", {"start": 1})
        self.assertEqual(str(msg.exception), "'The query must have the start and end keys.'")

        with self.assertRaises(KeyError) as msg:
            cddis_cli._week_products("", "/", {"end": 1})
        self.assertEqual(str(msg.exception), "'The query must have the start and end keys.'")

        with self.assertRaises(ValueError) as msg:
            cddis_cli._week_products("", "/", {"start": "2020-01-02", "end": "2020-01-01"})
        self.assertEqual(str(msg.exception), "Start day must be less than or equal to end day.")

        with self.assertRaises(Exception) as msg:
            cddis_cli._week_products("", "/", {"start": "aaa", "end": "2020-01-01"})

        with self.assertRaises(Exception) as msg:
            cddis_cli._week_products("", "/", {"start": "2020-01-02", "end": "aaa"})

        with patch("moncenterlib.gnss.cddis_client.FTP_TLS"):
            with self.assertRaises(ValueError) as msg:
                cddis_cli._week_products("", "/", {"start": "2020-01-01", "end": "2020-01-02"})
            self.assertEqual(str(msg.exception), "Unknow type of product.")

    def test__week_products_check_connection2ftp(self):
        cddis_cli = CDDISClient(False)
        with patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps:
            query = {"start": "2020-01-01", "end": "2020-01-02"}
            instance_mock_ftps = mock_ftps.return_value.__enter__()

            cddis_cli._week_products("sp3", "/", query)

            self.assertEqual(call('gdc.cddis.eosdis.nasa.gov', timeout=300), mock_ftps.call_args)
            self.assertEqual([call(user='anonymous', passwd='anonymous')], instance_mock_ftps.login.mock_calls)
            self.assertTrue(instance_mock_ftps.prot_p.called)
            self.assertEqual([call(True)], instance_mock_ftps.set_pasv.mock_calls)

    def test__week_products_check_types_product_old_format(self):
        cddis_cli = CDDISClient(False)
        with patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps:

            instance_mock_ftps = mock_ftps.return_value.__enter__()

            query = {"start": "2020-01-01", "end": "2020-01-02"}
            cddis_cli._week_products("sp3", "/", query)
            self.assertEqual([('/gnss/products/2086/igs20863.sp3.Z',), ('/gnss/products/2086/igs20864.sp3.Z',)],
                             [instance_mock_ftps.size.call_args_list[0].args,
                              instance_mock_ftps.size.call_args_list[1].args])

            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("clk_5m", "/", query)
            self.assertEqual([('/gnss/products/2086/igs20863.clk.Z',), ('/gnss/products/2086/igs20864.clk.Z',)],
                             [instance_mock_ftps.size.call_args_list[0].args,
                              instance_mock_ftps.size.call_args_list[1].args])

            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("clk_30s", "/", query)
            self.assertEqual([('/gnss/products/2086/igs20863.clk_30s.Z',), ('/gnss/products/2086/igs20864.clk_30s.Z',)],
                             [instance_mock_ftps.size.call_args_list[0].args,
                              instance_mock_ftps.size.call_args_list[1].args])

            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("erp", "/", query)
            self.assertEqual(('/gnss/products/2086/igs20867.erp.Z',), instance_mock_ftps.size.call_args_list[0].args)
            self.assertEqual(1, instance_mock_ftps.size.call_count)

            # new query
            query = {"start": "2019-12-31", "end": "2020-01-10"}
            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("sp3", "/", query)
            self.assertEqual([('/gnss/products/2086/igs20862.sp3.Z',), ('/gnss/products/2087/igs20875.sp3.Z',)],
                             [instance_mock_ftps.size.call_args_list[0].args,
                              instance_mock_ftps.size.call_args_list[10].args])

            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("clk_5m", "/", query)
            self.assertEqual([('/gnss/products/2086/igs20862.clk.Z',), ('/gnss/products/2087/igs20875.clk.Z',)],
                             [instance_mock_ftps.size.call_args_list[0].args,
                              instance_mock_ftps.size.call_args_list[10].args])

            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("clk_30s", "/", query)
            self.assertEqual([('/gnss/products/2086/igs20862.clk_30s.Z',), ('/gnss/products/2087/igs20875.clk_30s.Z',)],
                             [instance_mock_ftps.size.call_args_list[0].args,
                              instance_mock_ftps.size.call_args_list[10].args])

            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("erp", "/", query)
            self.assertEqual([('/gnss/products/2086/igs20867.erp.Z',), ('/gnss/products/2087/igs20877.erp.Z',)],
                             [instance_mock_ftps.size.call_args_list[0].args,
                              instance_mock_ftps.size.call_args_list[1].args])
            self.assertEqual(2, instance_mock_ftps.size.call_count)

    def test__week_products_check_types_product_new_format(self):
        cddis_cli = CDDISClient(False)
        with patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps:
            instance_mock_ftps = mock_ftps.return_value.__enter__()
            instance_mock_ftps.size.side_effect = [Exception(), True]

            query = {"start": "2020-01-01", "end": "2020-01-02"}
            cddis_cli._week_products("sp3", "/", query)
            self.assertEqual([('/gnss/products/2086/IGS0OPSFIN_20200010000_01D_15M_ORB.SP3.gz',),
                              ('/gnss/products/2086/IGS0OPSFIN_20200020000_01D_15M_ORB.SP3.gz',)],
                             [instance_mock_ftps.size.call_args_list[1].args,
                              instance_mock_ftps.size.call_args_list[3].args])

            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("clk_5m", "/", query)
            self.assertEqual([('/gnss/products/2086/IGS0OPSFIN_20200010000_01D_05M_CLK.CLK.gz',),
                              ('/gnss/products/2086/IGS0OPSFIN_20200020000_01D_05M_CLK.CLK.gz',)],
                             [instance_mock_ftps.size.call_args_list[1].args,
                              instance_mock_ftps.size.call_args_list[3].args])

            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("clk_30s", "/", query)
            self.assertEqual([('/gnss/products/2086/IGS0OPSFIN_20200010000_01D_30S_CLK.CLK.gz',),
                              ('/gnss/products/2086/IGS0OPSFIN_20200020000_01D_30S_CLK.CLK.gz',)],
                             [instance_mock_ftps.size.call_args_list[1].args,
                              instance_mock_ftps.size.call_args_list[3].args])

            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("erp", "/", query)
            self.assertEqual(('/gnss/products/2086/IGS0OPSFIN_20193630000_07D_01D_ERP.ERP.gz',),
                             instance_mock_ftps.size.call_args_list[1].args)
            self.assertEqual(2, instance_mock_ftps.size.call_count)

            # new query
            query = {"start": "2019-12-31", "end": "2020-01-01"}
            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("sp3", "/", query)
            self.assertEqual([('/gnss/products/2086/IGS0OPSFIN_20193650000_01D_15M_ORB.SP3.gz',),
                              ('/gnss/products/2086/IGS0OPSFIN_20200010000_01D_15M_ORB.SP3.gz',)],
                             [instance_mock_ftps.size.call_args_list[1].args,
                              instance_mock_ftps.size.call_args_list[3].args])

            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("clk_5m", "/", query)
            self.assertEqual([('/gnss/products/2086/IGS0OPSFIN_20193650000_01D_05M_CLK.CLK.gz',),
                              ('/gnss/products/2086/IGS0OPSFIN_20200010000_01D_05M_CLK.CLK.gz',)],
                             [instance_mock_ftps.size.call_args_list[1].args,
                              instance_mock_ftps.size.call_args_list[3].args])

            instance_mock_ftps.size.reset_mock()
            cddis_cli._week_products("clk_30s", "/", query)
            self.assertEqual([('/gnss/products/2086/IGS0OPSFIN_20193650000_01D_30S_CLK.CLK.gz',),
                              ('/gnss/products/2086/IGS0OPSFIN_20200010000_01D_30S_CLK.CLK.gz',)],
                             [instance_mock_ftps.size.call_args_list[1].args,
                              instance_mock_ftps.size.call_args_list[3].args])

            instance_mock_ftps.size.reset_mock()
            query = {"start": "2019-12-31", "end": "2020-01-10"}
            cddis_cli._week_products("erp", "/", query)
            self.assertEqual([('/gnss/products/2086/IGS0OPSFIN_20193630000_07D_01D_ERP.ERP.gz',),
                              ('/gnss/products/2087/IGS0OPSFIN_20200050000_07D_01D_ERP.ERP.gz',)],
                             [instance_mock_ftps.size.call_args_list[1].args,
                              instance_mock_ftps.size.call_args_list[3].args])
            self.assertEqual(4, instance_mock_ftps.size.call_count)

    def test__week_products_check_download_file(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps,
              patch("moncenterlib.gnss.cddis_client.open") as mock_open):
            instance_mock_ftps = mock_ftps.return_value.__enter__()
            instance_mock_ftps.retrbinary.side_effect = [True]

            query = {"start": "2020-01-01", "end": "2020-01-02"}
            cddis_cli._week_products("sp3", "/", query, False)

            self.assertEqual(['RETR /gnss/products/2086/igs20863.sp3.Z',
                              'RETR /gnss/products/2086/igs20864.sp3.Z'],
                             [instance_mock_ftps.retrbinary.call_args_list[0].args[0],
                              instance_mock_ftps.retrbinary.call_args_list[1].args[0]])
            self.assertEqual([call('/igs20863.sp3.Z', 'wb'), call('/igs20864.sp3.Z', 'wb')], mock_open.call_args_list)
            self.assertTrue(hasattr(mock_open.return_value, "write"))

            # check continue
            instance_mock_ftps.retrbinary.side_effect = [True, Exception(), True]

            query = {"start": "2020-01-01", "end": "2020-01-03"}
            res = cddis_cli._week_products("sp3", "/", query, False)
            self.assertEqual(['/igs20863.sp3.Z', '/igs20865.sp3.Z'], res["no_exists"])

    def test__week_products_check_unpack_file_with_gz(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps,
              patch("moncenterlib.gnss.cddis_client.open") as mock_open,
              patch("moncenterlib.gnss.cddis_client.gzip.open") as mock_gzip_open,
              patch("moncenterlib.gnss.cddis_client.shutil.copyfileobj") as mock_shutil_copyfileobj):

            # unpack if file ending with .gz
            instance_mock_ftps = mock_ftps.return_value.__enter__()
            instance_mock_ftps.size.side_effect = [Exception(), True, Exception(), True]
            mock_gzip_open.return_value.__enter__().name = "file_gz"
            mock_open.return_value.__enter__().name = "file_rnx"

            query = {"start": "2020-01-01", "end": "2020-01-02"}
            res = cddis_cli._week_products("sp3", "/", query)
            self.assertEqual(['/IGS0OPSFIN_20200010000_01D_15M_ORB.SP3',
                              '/IGS0OPSFIN_20200020000_01D_15M_ORB.SP3'],
                             res["no_exists"])
            self.assertEqual([('/IGS0OPSFIN_20200010000_01D_15M_ORB.SP3.gz', 'rb'),
                              ('/IGS0OPSFIN_20200020000_01D_15M_ORB.SP3.gz', 'rb')],
                             [mock_gzip_open.call_args_list[0].args,
                              mock_gzip_open.call_args_list[1].args])
            self.assertEqual([('/IGS0OPSFIN_20200010000_01D_15M_ORB.SP3', 'wb'),
                              ('/IGS0OPSFIN_20200020000_01D_15M_ORB.SP3', 'wb')],
                             [mock_open.call_args_list[1].args,
                              mock_open.call_args_list[3].args])
            self.assertEqual(["file_gz", "file_rnx", "file_gz", "file_rnx"],
                             [mock_shutil_copyfileobj.call_args_list[0].args[0].name,
                              mock_shutil_copyfileobj.call_args_list[0].args[1].name,
                              mock_shutil_copyfileobj.call_args_list[1].args[0].name,
                              mock_shutil_copyfileobj.call_args_list[1].args[1].name])
            # and check continue
            instance_mock_ftps.size.side_effect = [Exception(), True, Exception(), True, Exception(), True]
            mock_gzip_open.side_effect = [MagicMock(), Exception(), MagicMock()]
            query = {"start": "2020-01-01", "end": "2020-01-03"}
            res = cddis_cli._week_products("sp3", "/", query)
            self.assertEqual(['/IGS0OPSFIN_20200010000_01D_15M_ORB.SP3',
                              '/IGS0OPSFIN_20200030000_01D_15M_ORB.SP3'],
                             res["no_exists"])

    def test__week_products_check_unpack_file_with_Z(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS"),
              patch("moncenterlib.gnss.cddis_client.open") as mock_open,
              patch("moncenterlib.gnss.cddis_client.subprocess.run") as mock_subproc,
              patch("moncenterlib.gnss.cddis_client.charset_normalizer.detect") as mock_detect,
              patch("moncenterlib.gnss.cddis_client.os.remove") as mock_remove):

            # unpack if file ending with .Z, encoding utf-8
            mock_detect.return_value = {"encoding": "utf-8"}
            query = {"start": "2020-01-01", "end": "2020-01-02"}
            res = cddis_cli._week_products("sp3", "/", query)
            self.assertEqual(['/igs20863.sp3', '/igs20864.sp3'], res["no_exists"])
            self.assertEqual([('/igs20863.sp3', 'wb'),
                              ('/igs20863.sp3', 'rb'),
                              ('/igs20864.sp3', 'wb'),
                              ('/igs20864.sp3', 'rb')],
                             [mock_open.call_args_list[1].args,
                              mock_open.call_args_list[2].args,
                              mock_open.call_args_list[4].args,
                              mock_open.call_args_list[5].args])
            self.assertEqual([(['gunzip', '-c', '/igs20863.sp3.Z'],),
                              (['gunzip', '-c', '/igs20864.sp3.Z'],)],
                             [mock_subproc.call_args_list[0].args,
                              mock_subproc.call_args_list[1].args])
            self.assertEqual([{"check": True, "stdout": mock_open().__enter__()},
                              {"check": True, "stdout": mock_open().__enter__()}],
                             [mock_subproc.call_args_list[0].kwargs,
                              mock_subproc.call_args_list[1].kwargs])
            self.assertEqual([call('/igs20863.sp3.Z'), call('/igs20864.sp3.Z')], mock_remove.call_args_list)

            # unpack if file ending with .Z, encoding unknow
            mock_open.reset_mock()
            mock_detect.return_value = {"encoding": "unknow"}
            query = {"start": "2020-01-01", "end": "2020-01-02"}
            res = cddis_cli._week_products("sp3", "/", query)
            self.assertEqual([call('/igs20863.sp3', 'wb'),
                              call('/igs20863.sp3', 'rb'),
                              call('/igs20863.sp3', 'r', encoding='unknow'),
                              call('/igs20863.sp3', 'w', encoding='utf-8')],
                             mock_open.call_args_list[1:5])
            self.assertEqual([call('/igs20864.sp3', 'wb'),
                              call('/igs20864.sp3', 'rb'),
                              call('/igs20864.sp3', 'r', encoding='unknow'),
                              call('/igs20864.sp3', 'w', encoding='utf-8')],
                             mock_open.call_args_list[6:])

            # check except - continue
            mock_subproc.side_effect = [True, Exception(), True]
            query = {"start": "2020-01-01", "end": "2020-01-03"}
            res = cddis_cli._week_products("sp3", "/", query)
            self.assertEqual(['/igs20863.sp3', '/igs20865.sp3'], res["no_exists"])

    def test__week_products_check_output(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps,
              patch("moncenterlib.gnss.cddis_client.files_check") as mock_files_check):
            instance_mock_ftps = mock_ftps.return_value.__enter__()
            instance_mock_ftps.size.side_effect = Exception()
            mock_files_check.return_value = {"done": [], "no_exists": []}

            # check no_found_dates
            result = cddis_cli._week_products("sp3", "/", {"start": "2020-01-01", "end": "2020-01-02"}, False)
            self.assertEqual({"done": [], "no_exists": [], "no_found_dates": ["2020-01-01", "2020-01-02"]}, result)
            self.assertTrue(mock_files_check.called)
            mock_files_check.reset_mock()

            instance_mock_ftps.size.side_effect = None
            result = cddis_cli._week_products("sp3", "/", {"start": "2020-01-01", "end": "2020-01-02"}, False)
            self.assertEqual({"done": [], "no_exists": [], "no_found_dates": []}, result)
            self.assertTrue(mock_files_check.called)
            mock_files_check.reset_mock()

            # check done and no_exists
            mock_files_check.return_value = {"done": ["2020-01-01"], "no_exists": ["2020-01-02"]}
            result = cddis_cli._week_products("sp3", "/", {"start": "2020-01-01", "end": "2020-01-02"}, False)
            self.assertEqual({"done": ["2020-01-01"], "no_exists": ["2020-01-02"], "no_found_dates": []}, result)
            self.assertTrue(mock_files_check.called)
            mock_files_check.reset_mock()

    def test_get_precise_orbits(self):
        cddis_cli = CDDISClient(False)
        with self.assertRaises(Exception):
            res = cddis_cli.get_precise_orbits(None, None, None)

        cddis_cli._week_products = MagicMock()
        cddis_cli._week_products.return_value = {"done": [], "no_exists": [], "no_found_dates": []}

        query = {"start": "2020-01-01", "end": "2020-01-03"}
        res = cddis_cli.get_precise_orbits("/", query)

        self.assertEqual({"done": [], "no_exists": [], "no_found_dates": []}, res)
        self.assertEqual(('sp3', '/', {'start': '2020-01-01', 'end': '2020-01-03'}, True),
                         cddis_cli._week_products.call_args_list[0].args)

    def test_get_clock_30s(self):
        cddis_cli = CDDISClient(False)
        with self.assertRaises(Exception):
            res = cddis_cli.get_clock_30s(None, None, None)

        cddis_cli._week_products = MagicMock()
        cddis_cli._week_products.return_value = {"done": [], "no_exists": [], "no_found_dates": []}

        query = {"start": "2020-01-01", "end": "2020-01-03"}
        res = cddis_cli.get_clock_30s("/", query)

        self.assertEqual({"done": [], "no_exists": [], "no_found_dates": []}, res)
        self.assertEqual(('clk_30s', '/', {'start': '2020-01-01', 'end': '2020-01-03'}, True),
                         cddis_cli._week_products.call_args_list[0].args)

    def test_get_clock_5m(self):
        cddis_cli = CDDISClient(False)
        with self.assertRaises(Exception):
            res = cddis_cli.get_clock_5m(None, None, None)

        cddis_cli._week_products = MagicMock()
        cddis_cli._week_products.return_value = {"done": [], "no_exists": [], "no_found_dates": []}

        query = {"start": "2020-01-01", "end": "2020-01-03"}
        res = cddis_cli.get_clock_5m("/", query)

        self.assertEqual({"done": [], "no_exists": [], "no_found_dates": []}, res)
        self.assertEqual(('clk_5m', '/', {'start': '2020-01-01', 'end': '2020-01-03'}, True),
                         cddis_cli._week_products.call_args_list[0].args)

    def test_get_earth_orientation(self):
        cddis_cli = CDDISClient(False)
        with self.assertRaises(Exception):
            res = cddis_cli.get_earth_orientation(None, None, None)

        cddis_cli._week_products = MagicMock()
        cddis_cli._week_products.return_value = {"done": [], "no_exists": [], "no_found_dates": []}

        query = {"start": "2020-01-01", "end": "2020-01-03"}
        res = cddis_cli.get_earth_orientation("/", query)

        self.assertEqual({"done": [], "no_exists": [], "no_found_dates": []}, res)
        self.assertEqual(('erp', '/', {'start': '2020-01-01', 'end': '2020-01-03'}, True),
                         cddis_cli._week_products.call_args_list[0].args)

    def test_get_daily_multi_gnss_brd_eph_raises(self):
        cddis_cli = CDDISClient(False)
        with self.assertRaises(Exception):
            cddis_cli.get_daily_multi_gnss_brd_eph(None, None, None)

        with self.assertRaises(ValueError) as msg:
            cddis_cli.get_daily_multi_gnss_brd_eph("", {})
        self.assertEqual(str(msg.exception), "Path to output_dir is strange.")

        with self.assertRaises(KeyError) as msg:
            cddis_cli.get_daily_multi_gnss_brd_eph("/", {})
        self.assertEqual(str(msg.exception), "'The query must have the start and end keys.'")

        with self.assertRaises(KeyError) as msg:
            cddis_cli.get_daily_multi_gnss_brd_eph("/", {"start": 1})
        self.assertEqual(str(msg.exception), "'The query must have the start and end keys.'")

        with self.assertRaises(KeyError) as msg:
            cddis_cli.get_daily_multi_gnss_brd_eph("/", {"end": 1})
        self.assertEqual(str(msg.exception), "'The query must have the start and end keys.'")

        with self.assertRaises(ValueError) as msg:
            cddis_cli.get_daily_multi_gnss_brd_eph("/", {"start": "2020-01-02", "end": "2020-01-01"})
        self.assertEqual(str(msg.exception), "Start day must be less than or equal to end day.")

        with self.assertRaises(Exception) as msg:
            cddis_cli.get_daily_multi_gnss_brd_eph("/", {"start": "aaa", "end": "2020-01-01"})

        with self.assertRaises(Exception) as msg:
            cddis_cli.get_daily_multi_gnss_brd_eph("/", {"start": "2020-01-02", "end": "aaa"})

    def test_get_daily_multi_gnss_brd_eph_check_connection2ftp(self):
        cddis_cli = CDDISClient(False)
        with patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps:
            instance_mock_ftps = mock_ftps.return_value.__enter__()

            query = {"start": "2019-12-31", "end": "2020-01-01"}

            cddis_cli.get_daily_multi_gnss_brd_eph("/", query)

            self.assertEqual(call('gdc.cddis.eosdis.nasa.gov', timeout=300), mock_ftps.call_args)
            self.assertEqual([call(user='anonymous', passwd='anonymous')], instance_mock_ftps.login.mock_calls)
            self.assertTrue(instance_mock_ftps.prot_p.called)
            self.assertEqual([call(True)], instance_mock_ftps.set_pasv.mock_calls)

    def test_get_daily_multi_gnss_brd_eph_check_file_names(self):
        cddis_cli = CDDISClient(False)
        with patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps:
            instance_mock_ftps = mock_ftps.return_value.__enter__()

            query = {"start": "2019-12-31", "end": "2020-01-01"}

            cddis_cli.get_daily_multi_gnss_brd_eph("/", query)

            self.assertEqual([('gnss/data/daily/2019/brdc/BRDC00IGS_R_20193650000_01D_MN.rnx.gz',),
                              ('gnss/data/daily/2020/brdc/BRDC00IGS_R_20200010000_01D_MN.rnx.gz',)],
                             [instance_mock_ftps.size.call_args_list[0].args,
                              instance_mock_ftps.size.call_args_list[1].args])

            # second name
            instance_mock_ftps.reset_mock()
            instance_mock_ftps.size.side_effect = [Exception, True]
            query = {"start": "2019-12-31", "end": "2020-01-01"}

            cddis_cli.get_daily_multi_gnss_brd_eph("/", query)

            self.assertEqual([('gnss/data/daily/2019/brdc/BRDM00DLR_S_20193650000_01D_MN.rnx.gz',),
                              ('gnss/data/daily/2020/brdc/BRDM00DLR_S_20200010000_01D_MN.rnx.gz',)],
                             [instance_mock_ftps.size.call_args_list[1].args,
                              instance_mock_ftps.size.call_args_list[3].args])

    def test_get_daily_multi_gnss_brd_eph_downloads(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps,
              patch("moncenterlib.gnss.cddis_client.open") as mock_open):
            instance_mock_ftps = mock_ftps.return_value.__enter__()

            query = {"start": "2019-12-31", "end": "2020-01-01"}

            cddis_cli.get_daily_multi_gnss_brd_eph("/", query)

            self.assertEqual(['RETR gnss/data/daily/2019/brdc/BRDC00IGS_R_20193650000_01D_MN.rnx.gz',
                              'RETR gnss/data/daily/2020/brdc/BRDC00IGS_R_20200010000_01D_MN.rnx.gz'],
                             [instance_mock_ftps.retrbinary.call_args_list[0].args[0],
                              instance_mock_ftps.retrbinary.call_args_list[1].args[0]])
            self.assertEqual([call('/BRDC00IGS_R_20193650000_01D_MN.rnx.gz', 'wb'),
                              call('/BRDC00IGS_R_20200010000_01D_MN.rnx.gz', 'wb')], mock_open.call_args_list)
            self.assertTrue(hasattr(mock_open.return_value, "write"))

            # check continue
            instance_mock_ftps.retrbinary.side_effect = [True, Exception(), True]

            query = {"start": "2020-01-01", "end": "2020-01-03"}
            res = cddis_cli.get_daily_multi_gnss_brd_eph("/", query, False)
            self.assertEqual(['/BRDC00IGS_R_20200010000_01D_MN.rnx.gz',
                             '/BRDC00IGS_R_20200030000_01D_MN.rnx.gz'], res["no_exists"])

    def test_get_daily_multi_gnss_brd_eph_unpacks(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS"),
              patch("moncenterlib.gnss.cddis_client.open") as mock_open,
              patch("moncenterlib.gnss.cddis_client.gzip.open") as mock_gzip_open,
              patch("moncenterlib.gnss.cddis_client.shutil.copyfileobj") as mock_shutil_copyfileobj):

            mock_gzip_open.return_value.__enter__().name = "file_gz"
            mock_open.return_value.__enter__().name = "file_rnx"

            query = {"start": "2020-01-01", "end": "2020-01-02"}
            res = cddis_cli.get_daily_multi_gnss_brd_eph("/", query)
            self.assertEqual(['/BRDC00IGS_R_20200010000_01D_MN.rnx', '/BRDC00IGS_R_20200020000_01D_MN.rnx'],
                             res["no_exists"])
            self.assertEqual([('/BRDC00IGS_R_20200010000_01D_MN.rnx.gz', 'rb'),
                              ('/BRDC00IGS_R_20200020000_01D_MN.rnx.gz', 'rb')],
                             [mock_gzip_open.call_args_list[0].args,
                              mock_gzip_open.call_args_list[1].args])
            self.assertEqual([('/BRDC00IGS_R_20200010000_01D_MN.rnx', 'wb'),
                              ('/BRDC00IGS_R_20200020000_01D_MN.rnx', 'wb')],
                             [mock_open.call_args_list[1].args,
                              mock_open.call_args_list[3].args])
            self.assertEqual(["file_gz", "file_rnx", "file_gz", "file_rnx"],
                             [mock_shutil_copyfileobj.call_args_list[0].args[0].name,
                              mock_shutil_copyfileobj.call_args_list[0].args[1].name,
                              mock_shutil_copyfileobj.call_args_list[1].args[0].name,
                              mock_shutil_copyfileobj.call_args_list[1].args[1].name])

    def test_get_daily_multi_gnss_brd_eph_remove(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS"),
              patch("moncenterlib.gnss.cddis_client.open"),
              patch("moncenterlib.gnss.cddis_client.gzip.open"),
              patch("moncenterlib.gnss.cddis_client.shutil.copyfileobj"),
              patch("moncenterlib.gnss.cddis_client.os.remove") as mock_remove):

            query = {"start": "2020-01-01", "end": "2020-01-02"}
            cddis_cli.get_daily_multi_gnss_brd_eph("/", query)

            self.assertEqual([call('/BRDC00IGS_R_20200010000_01D_MN.rnx.gz',),
                              call('/BRDC00IGS_R_20200020000_01D_MN.rnx.gz',)], mock_remove.call_args_list)
    
    def test_get_daily_multi_gnss_brd_eph_output(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps,
              patch("moncenterlib.gnss.cddis_client.files_check") as mock_files_check):
            instance_mock_ftps = mock_ftps.return_value.__enter__()
            instance_mock_ftps.size.side_effect = Exception()
            mock_files_check.return_value = {"done": [], "no_exists": []}

            # check no_found_dates
            result = cddis_cli.get_daily_multi_gnss_brd_eph("/", {"start": "2020-01-01", "end": "2020-01-02"}, False)
            self.assertEqual({"done": [], "no_exists": [], "no_found_dates": ["2020-01-01", "2020-01-02"]}, result)
            self.assertTrue(mock_files_check.called)
            mock_files_check.reset_mock()

            instance_mock_ftps.size.side_effect = None
            result = cddis_cli.get_daily_multi_gnss_brd_eph("/", {"start": "2020-01-01", "end": "2020-01-02"}, False)
            self.assertEqual({"done": [], "no_exists": [], "no_found_dates": []}, result)
            self.assertTrue(mock_files_check.called)
            mock_files_check.reset_mock()

            # check done and no_exists
            mock_files_check.return_value = {"done": ["2020-01-01"], "no_exists": ["2020-01-02"]}
            result = cddis_cli.get_daily_multi_gnss_brd_eph("/", {"start": "2020-01-01", "end": "2020-01-02"}, False)
            self.assertEqual({"done": ["2020-01-01"], "no_exists": ["2020-01-02"], "no_found_dates": []}, result)
            self.assertTrue(mock_files_check.called)
            mock_files_check.reset_mock()

    def test_get_daily_30s_data_raises(self):
        cddis_cli = CDDISClient(False)
        with self.assertRaises(Exception):
            cddis_cli.get_daily_30s_data(None, None, None)

        with self.assertRaises(ValueError) as msg:
            cddis_cli.get_daily_30s_data("", {})
        self.assertEqual(str(msg.exception), "Path to output_dir is strange.")

        with self.assertRaises(KeyError) as msg:
            cddis_cli.get_daily_30s_data("/", {})
        self.assertEqual(str(msg.exception), "'Invalid query.'")

        with self.assertRaises(KeyError) as msg:
            cddis_cli.get_daily_30s_data("/", {"start": 1})
        self.assertEqual(str(msg.exception), "'Invalid query.'")

        with self.assertRaises(KeyError) as msg:
            cddis_cli.get_daily_30s_data("/", {"end": 1})
        self.assertEqual(str(msg.exception), "'Invalid query.'")

        with self.assertRaises(KeyError) as msg:
            cddis_cli.get_daily_30s_data("/", {"start": 1, "end": 1})
        self.assertEqual(str(msg.exception), "'Invalid query.'")

        with self.assertRaises(KeyError) as msg:
            cddis_cli.get_daily_30s_data("/", {"start": 1, "end": 1, "station": 1})
        self.assertEqual(str(msg.exception), "'Invalid query.'")

        with self.assertRaises(KeyError) as msg:
            cddis_cli.get_daily_30s_data("/", {"start": 1, "end": 1, "station": 1, "rinex_v": 1})
        self.assertEqual(str(msg.exception), "'Invalid query.'")

        with self.assertRaises(KeyError) as msg:
            cddis_cli.get_daily_30s_data("/", {"start": 1, "end": 1, "station": 1, "type": 1})
        self.assertEqual(str(msg.exception), "'Invalid query.'")

        with self.assertRaises(ValueError) as msg:
            cddis_cli.get_daily_30s_data(
                "/", {"start": "2020-01-02", "end": "2020-01-01", "station": 1, "rinex_v": 1, "type": 1})
        self.assertEqual(str(msg.exception), "Start day must be less than or equal to end day.")

        with self.assertRaises(Exception) as msg:
            cddis_cli.get_daily_30s_data("/", {"start": "aaa", "end": "2020-01-01"})

        with self.assertRaises(Exception) as msg:
            cddis_cli.get_daily_30s_data("/", {"start": "2020-01-02", "end": "aaa"})

        with (self.assertRaises(ValueError) as msg,
              patch("moncenterlib.gnss.cddis_client.FTP_TLS")):
            cddis_cli.get_daily_30s_data("/", {"start": "2020-01-01", "end": "2020-01-02",
                                         "station": "1", "rinex_v": "1", "type": "1"})
        self.assertEqual(str(msg.exception), "Unknow rinex version.")

    def test_get_daily_30s_data_connection2ftp(self):
        cddis_cli = CDDISClient(False)
        with patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps:
            instance_mock_ftps = mock_ftps.return_value.__enter__()

            query = {"start": "2019-12-31",
                     "end": "2020-01-01",
                     "station": "NOVM",
                     "rinex_v": "3",
                     "type": "O"}

            cddis_cli.get_daily_30s_data("/", query)

            self.assertEqual(call('gdc.cddis.eosdis.nasa.gov', timeout=300), mock_ftps.call_args)
            self.assertEqual([call(user='anonymous', passwd='anonymous')], instance_mock_ftps.login.mock_calls)
            self.assertTrue(instance_mock_ftps.prot_p.called)
            self.assertEqual([call(True)], instance_mock_ftps.set_pasv.mock_calls)

    def test_get_daily_30s_data_check_rinex_versions(self):
        cddis_cli = CDDISClient(False)
        with patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps:
            instance_mock_ftps = mock_ftps.return_value.__enter__()
            instance_mock_ftps.name = "FTPS"

            # rinex v2
            mock_search_daily_30s_data_v2 = MagicMock()
            cddis_cli._search_daily_30s_data_v2 = mock_search_daily_30s_data_v2
            query = {"start": "2019-12-31",
                     "end": "2020-01-01",
                     "station": "NOVM",
                     "rinex_v": "2",
                     "type": "O"}

            cddis_cli.get_daily_30s_data("/", query)

            exp = [(query, "365", "19", 'gnss/data/daily/2019/365/19o/'),
                   (query, "001", "20", 'gnss/data/daily/2020/001/20o/')]
            res = [mock_search_daily_30s_data_v2.call_args_list[0].args[1:],
                   mock_search_daily_30s_data_v2.call_args_list[1].args[1:]]
            self.assertEqual(exp, res)

            exp = ["FTPS", "FTPS"]
            res = [mock_search_daily_30s_data_v2.call_args_list[0].args[0].name,
                   mock_search_daily_30s_data_v2.call_args_list[1].args[0].name]
            self.assertEqual(exp, res)
            mock_search_daily_30s_data_v2.reset_mock()

            # rinex v3
            mock_search_daily_30s_data_v3 = MagicMock()
            cddis_cli._search_daily_30s_data_v3 = mock_search_daily_30s_data_v3
            query = {"start": "2019-12-31",
                     "end": "2020-01-01",
                     "station": "NOVM",
                     "rinex_v": "3",
                     "type": "O"}

            cddis_cli.get_daily_30s_data("/", query)

            exp = [(query, "365", "2019", 'gnss/data/daily/2019/365/19o/'),
                   (query, "001", "2020", 'gnss/data/daily/2020/001/20o/')]
            res = [mock_search_daily_30s_data_v3.call_args_list[0].args[1:],
                   mock_search_daily_30s_data_v3.call_args_list[1].args[1:]]
            self.assertEqual(exp, res)

            exp = ["FTPS", "FTPS"]
            res = [mock_search_daily_30s_data_v3.call_args_list[0].args[0].name,
                   mock_search_daily_30s_data_v3.call_args_list[1].args[0].name]
            self.assertEqual(exp, res)
            mock_search_daily_30s_data_v3.reset_mock()

            # rinex auto, find v2
            query = {"start": "2019-12-31",
                     "end": "2020-01-01",
                     "station": "NOVM",
                     "rinex_v": "auto",
                     "type": "O"}

            cddis_cli.get_daily_30s_data("/", query)

            exp = [(query, "365", "19", 'gnss/data/daily/2019/365/19o/'),
                   (query, "001", "20", 'gnss/data/daily/2020/001/20o/')]
            res = [mock_search_daily_30s_data_v2.call_args_list[0].args[1:],
                   mock_search_daily_30s_data_v2.call_args_list[1].args[1:]]
            self.assertEqual(exp, res)

            exp = ["FTPS", "FTPS"]
            res = [mock_search_daily_30s_data_v2.call_args_list[0].args[0].name,
                   mock_search_daily_30s_data_v2.call_args_list[1].args[0].name]
            self.assertEqual(exp, res)

            # rinex auto, find v3
            mock_search_daily_30s_data_v2.return_value = ""
            query = {"start": "2019-12-31",
                     "end": "2020-01-01",
                     "station": "NOVM",
                     "rinex_v": "auto",
                     "type": "O"}

            cddis_cli.get_daily_30s_data("/", query)

            exp = [(query, "365", "2019", 'gnss/data/daily/2019/365/19o/'),
                   (query, "001", "2020", 'gnss/data/daily/2020/001/20o/')]
            res = [mock_search_daily_30s_data_v3.call_args_list[0].args[1:],
                   mock_search_daily_30s_data_v3.call_args_list[1].args[1:]]
            self.assertEqual(exp, res)

            exp = ["FTPS", "FTPS"]
            res = [mock_search_daily_30s_data_v3.call_args_list[0].args[0].name,
                   mock_search_daily_30s_data_v3.call_args_list[1].args[0].name]
            self.assertEqual(exp, res)

    def test_get_daily_30s_data_check_continue_in_rinex_versions(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps,
              patch("moncenterlib.gnss.cddis_client.open")):
            instance_mock_ftps = mock_ftps.return_value.__enter__()
            instance_mock_ftps.name = "FTPS"

            # rinex v2
            mock_search_daily_30s_data_v2 = MagicMock()
            mock_search_daily_30s_data_v2.side_effect = ["some_file1", "", "some_file3"]
            cddis_cli._search_daily_30s_data_v2 = mock_search_daily_30s_data_v2

            instance_mock_ftps.retrbinary.side_effect = [Exception(), Exception(), Exception()]

            query = {"start": "2019-12-31",
                     "end": "2020-01-02",
                     "station": "NOVM",
                     "rinex_v": "2",
                     "type": "O"}

            cddis_cli.get_daily_30s_data("/", query, False)
            self.assertEqual(['RETR gnss/data/daily/2019/365/19o/some_file1',
                              'RETR gnss/data/daily/2020/002/20o/some_file3'],
                             [instance_mock_ftps.retrbinary.call_args_list[0].args[0],
                             instance_mock_ftps.retrbinary.call_args_list[1].args[0]])

            # rinex v3
            instance_mock_ftps.retrbinary.reset_mock()
            mock_search_daily_30s_data_v3 = MagicMock()
            mock_search_daily_30s_data_v3.side_effect = ["some_file1", "", "some_file3"]
            cddis_cli._search_daily_30s_data_v3 = mock_search_daily_30s_data_v3

            instance_mock_ftps.retrbinary.side_effect = [Exception(), Exception(), Exception()]

            query = {"start": "2019-12-31",
                     "end": "2020-01-02",
                     "station": "NOVM",
                     "rinex_v": "3",
                     "type": "O"}

            cddis_cli.get_daily_30s_data("/", query, False)
            self.assertEqual(['RETR gnss/data/daily/2019/365/19o/some_file1',
                              'RETR gnss/data/daily/2020/002/20o/some_file3'],
                             [instance_mock_ftps.retrbinary.call_args_list[0].args[0],
                             instance_mock_ftps.retrbinary.call_args_list[1].args[0]])

            # rinex auto, 2x - v2, 1 - v3
            instance_mock_ftps.retrbinary.reset_mock()
            mock_search_daily_30s_data_v2.side_effect = ["some_file1_v2", "", "some_file3_v2"]
            mock_search_daily_30s_data_v3.side_effect = ["some_file_v3"]
            instance_mock_ftps.retrbinary.side_effect = [Exception(), Exception(), Exception()]

            query = {"start": "2019-12-31",
                     "end": "2020-01-02",
                     "station": "NOVM",
                     "rinex_v": "auto",
                     "type": "O"}

            cddis_cli.get_daily_30s_data("/", query, False)
            self.assertEqual(['RETR gnss/data/daily/2019/365/19o/some_file1_v2',
                              'RETR gnss/data/daily/2020/002/20o/some_file3_v2'],
                             [instance_mock_ftps.retrbinary.call_args_list[0].args[0],
                             instance_mock_ftps.retrbinary.call_args_list[2].args[0]])

            self.assertEqual('RETR gnss/data/daily/2020/001/20o/some_file_v3',
                             instance_mock_ftps.retrbinary.call_args_list[1].args[0])

            # rinex auto, not found
            instance_mock_ftps.retrbinary.reset_mock()
            mock_search_daily_30s_data_v2.side_effect = ["", "", ""]
            mock_search_daily_30s_data_v3.side_effect = ["", "", ""]
            instance_mock_ftps.retrbinary.side_effect = [Exception(), Exception(), Exception()]

            query = {"start": "2019-12-31",
                     "end": "2020-01-02",
                     "station": "NOVM",
                     "rinex_v": "auto",
                     "type": "O"}

            cddis_cli.get_daily_30s_data("/", query, False)
            self.assertEqual([], instance_mock_ftps.retrbinary.call_args_list)

    def test_get_daily_30s_data_downloads(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps,
              patch("moncenterlib.gnss.cddis_client.open") as mock_open):
            instance_mock_ftps = mock_ftps.return_value.__enter__()

            query = {"start": "2019-12-31",
                     "end": "2020-01-01",
                     "station": "NOVM",
                     "rinex_v": "2",
                     "type": "O"}

            cddis_cli.get_daily_30s_data("/", query, False)

            self.assertEqual(['RETR gnss/data/daily/2019/365/19o/novm3650.19o.gz',
                              'RETR gnss/data/daily/2020/001/20o/novm0010.20o.gz'],
                             [instance_mock_ftps.retrbinary.call_args_list[0].args[0],
                              instance_mock_ftps.retrbinary.call_args_list[1].args[0]])
            self.assertEqual([call('/novm3650.19o.gz', 'wb'),
                              call('/novm0010.20o.gz', 'wb')], mock_open.call_args_list)
            self.assertTrue(hasattr(mock_open.return_value, "write"))

            # check continue
            instance_mock_ftps.retrbinary.side_effect = [True, Exception(), True]

            query = {"start": "2019-12-31",
                     "end": "2020-01-02",
                     "station": "NOVM",
                     "rinex_v": "2",
                     "type": "O"}

            res = cddis_cli.get_daily_30s_data("/", query, False)
            self.assertEqual(['/novm3650.19o.gz', '/novm0020.20o.gz'], res["no_exists"])

    def test_get_daily_30s_data_unpack_with_gz(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps,
              patch("moncenterlib.gnss.cddis_client.open") as mock_open,
              patch("moncenterlib.gnss.cddis_client.gzip.open") as mock_gzip_open,
              patch("moncenterlib.gnss.cddis_client.shutil.copyfileobj") as mock_shutil_copyfileobj):

            # unpack if file ending with .gz
            instance_mock_ftps = mock_ftps.return_value.__enter__()
            instance_mock_ftps.size.side_effect = [Exception(), True, Exception(), True]
            mock_gzip_open.return_value.__enter__().name = "file_gz"
            mock_open.return_value.__enter__().name = "file_rnx"

            mock_search_daily_30s_data_v3 = MagicMock()
            mock_search_daily_30s_data_v3.side_effect = ["some_file1.gz", "", "some_file3.gz"]
            cddis_cli._search_daily_30s_data_v3 = mock_search_daily_30s_data_v3

            query = {"start": "2019-12-31",
                     "end": "2020-01-02",
                     "station": "NOVM",
                     "rinex_v": "3",
                     "type": "O"}

            res = cddis_cli.get_daily_30s_data("/", query)
            self.assertEqual(['/some_file1', '/some_file3'],
                             res["no_exists"])
            self.assertEqual([('/some_file1.gz', 'rb'),
                              ('/some_file3.gz', 'rb')],
                             [mock_gzip_open.call_args_list[0].args,
                              mock_gzip_open.call_args_list[1].args])
            self.assertEqual([('/some_file1', 'wb'),
                              ('/some_file3', 'wb')],
                             [mock_open.call_args_list[1].args,
                              mock_open.call_args_list[3].args])
            self.assertEqual(["file_gz", "file_rnx", "file_gz", "file_rnx"],
                             [mock_shutil_copyfileobj.call_args_list[0].args[0].name,
                              mock_shutil_copyfileobj.call_args_list[0].args[1].name,
                              mock_shutil_copyfileobj.call_args_list[1].args[0].name,
                              mock_shutil_copyfileobj.call_args_list[1].args[1].name])

            # and check continue
            mock_search_daily_30s_data_v3.side_effect = ["some_file1.gz", "some_file2.gz", "some_file3.gz"]
            mock_gzip_open.side_effect = [MagicMock(), Exception(), MagicMock()]
            query = {"start": "2019-12-31",
                     "end": "2020-01-02",
                     "station": "NOVM",
                     "rinex_v": "3",
                     "type": "O"}
            res = cddis_cli.get_daily_30s_data("/", query)
            self.assertEqual(['/some_file1', '/some_file3'], res["no_exists"])

    def test_get_daily_30s_data_unpack_with_Z(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS"),
              patch("moncenterlib.gnss.cddis_client.open") as mock_open,
              patch("moncenterlib.gnss.cddis_client.subprocess.run") as mock_subproc,
              patch("moncenterlib.gnss.cddis_client.charset_normalizer.detect") as mock_detect,
              patch("moncenterlib.gnss.cddis_client.os.remove") as mock_remove):

            # unpack if file ending with .Z, encoding utf-8
            mock_detect.return_value = {"encoding": "utf-8"}
            mock_search_daily_30s_data_v3 = MagicMock()
            mock_search_daily_30s_data_v3.side_effect = ["some_file1.Z", "", "some_file3.Z"]
            cddis_cli._search_daily_30s_data_v3 = mock_search_daily_30s_data_v3

            query = {"start": "2019-12-31",
                     "end": "2020-01-02",
                     "station": "NOVM",
                     "rinex_v": "3",
                     "type": "O"}
            res = cddis_cli.get_daily_30s_data("/", query)
            self.assertEqual(['/some_file1', '/some_file3'], res["no_exists"])

            self.assertEqual([('/some_file1', 'wb'),
                              ('/some_file1', 'rb'),
                              ('/some_file3', 'wb'),
                              ('/some_file3', 'rb')],
                             [mock_open.call_args_list[1].args,
                              mock_open.call_args_list[2].args,
                              mock_open.call_args_list[4].args,
                              mock_open.call_args_list[5].args])
            self.assertEqual([(['gunzip', '-c', '/some_file1.Z'],),
                              (['gunzip', '-c', '/some_file3.Z'],)],
                             [mock_subproc.call_args_list[0].args,
                              mock_subproc.call_args_list[1].args])
            self.assertEqual([{"check": True, "stdout": mock_open().__enter__()},
                              {"check": True, "stdout": mock_open().__enter__()}],
                             [mock_subproc.call_args_list[0].kwargs,
                              mock_subproc.call_args_list[1].kwargs])
            self.assertEqual([call('/some_file1.Z'), call('/some_file3.Z')], mock_remove.call_args_list)

            # unpack if file ending with .Z, encoding unknow
            mock_open.reset_mock()
            mock_detect.return_value = {"encoding": "unknow"}
            query = {"start": "2019-12-31",
                     "end": "2020-01-02",
                     "station": "NOVM",
                     "rinex_v": "3",
                     "type": "O"}
            mock_search_daily_30s_data_v3.side_effect = ["some_file1.Z", "", "some_file3.Z"]

            res = cddis_cli.get_daily_30s_data("/", query)

            self.assertEqual([call('/some_file1', 'wb'),
                              call('/some_file1', 'rb'),
                              call('/some_file1', 'r', encoding='unknow'),
                              call('/some_file1', 'w', encoding='utf-8')],
                             mock_open.call_args_list[1:5])
            self.assertEqual([call('/some_file3', 'wb'),
                              call('/some_file3', 'rb'),
                              call('/some_file3', 'r', encoding='unknow'),
                              call('/some_file3', 'w', encoding='utf-8')],
                             mock_open.call_args_list[6:])

            # check except - continue
            mock_subproc.side_effect = [True, Exception(), True]
            mock_search_daily_30s_data_v3.side_effect = ["some_file1.Z", "some_file2.Z", "some_file3.Z"]
            query = {"start": "2019-12-31",
                     "end": "2020-01-02",
                     "station": "NOVM",
                     "rinex_v": "3",
                     "type": "O"}
            res = cddis_cli.get_daily_30s_data("/", query)
            self.assertEqual(['/some_file1', '/some_file3'], res["no_exists"])

    def test_get_daily_30s_data_remove(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS"),
              patch("moncenterlib.gnss.cddis_client.open"),
              patch("moncenterlib.gnss.cddis_client.gzip.open"),
              patch("moncenterlib.gnss.cddis_client.shutil.copyfileobj"),
              patch("moncenterlib.gnss.cddis_client.os.remove") as mock_remove):

            mock_search_daily_30s_data_v3 = MagicMock()
            mock_search_daily_30s_data_v3.side_effect = ["some_file1.gz", "", "some_file3.gz"]
            cddis_cli._search_daily_30s_data_v3 = mock_search_daily_30s_data_v3

            query = {"start": "2019-12-31",
                     "end": "2020-01-02",
                     "station": "NOVM",
                     "rinex_v": "3",
                     "type": "O"}

            cddis_cli.get_daily_30s_data("/", query)

            self.assertEqual([call('/some_file1.gz'), call('/some_file3.gz')], mock_remove.call_args_list)

    def test_get_daily_30s_output(self):
        cddis_cli = CDDISClient(False)
        with (patch("moncenterlib.gnss.cddis_client.FTP_TLS") as mock_ftps,
              patch("moncenterlib.gnss.cddis_client.files_check") as mock_files_check):
            instance_mock_ftps = mock_ftps.return_value.__enter__()
            instance_mock_ftps.size.side_effect = Exception()
            mock_files_check.return_value = {"done": [], "no_exists": []}

            # check no_found_dates
            result = cddis_cli.get_daily_30s_data("/", {"start": "2020-01-01",
                                                        "end": "2020-01-02",
                                                        "station": "NOVM",
                                                        "rinex_v": "2",
                                                        "type": "O"},
                                                  False)
            self.assertEqual({"done": [], "no_exists": [], "no_found_dates": ["2020-01-01", "2020-01-02"]}, result)
            self.assertTrue(mock_files_check.called)
            mock_files_check.reset_mock()

            instance_mock_ftps.size.side_effect = None
            result = cddis_cli.get_daily_30s_data("/", {"start": "2020-01-01",
                                                        "end": "2020-01-02",
                                                        "station": "NOVM",
                                                        "rinex_v": "2",
                                                        "type": "O"},
                                                  False)
            self.assertEqual({"done": [], "no_exists": [], "no_found_dates": []}, result)
            self.assertTrue(mock_files_check.called)
            mock_files_check.reset_mock()

            # check done and no_exists
            mock_files_check.return_value = {"done": ["2020-01-01"], "no_exists": ["2020-01-02"]}
            result = cddis_cli.get_daily_30s_data("/", {"start": "2020-01-01",
                                                        "end": "2020-01-02",
                                                        "station": "NOVM",
                                                        "rinex_v": "2",
                                                        "type": "O"},
                                                  False)
            self.assertEqual({"done": ["2020-01-01"], "no_exists": ["2020-01-02"], "no_found_dates": []}, result)
            self.assertTrue(mock_files_check.called)
            mock_files_check.reset_mock()


if __name__ == "__main__":
    main()
