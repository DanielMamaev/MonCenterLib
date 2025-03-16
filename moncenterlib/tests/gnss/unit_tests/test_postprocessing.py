from collections import defaultdict
import logging
import tempfile
from unittest import TestCase, main
from unittest.mock import MagicMock, patch, call

from moncenterlib.gnss.postprocessing import RtkLibPost


class TestRtkLibPostPost(TestCase):
    def test_init_raises(self):
        with self.assertRaises(Exception):
            rtklibpost = RtkLibPost("None")

    def test_init_with_enable_logger(self):
        rtklibpost = RtkLibPost()
        self.assertEqual(logging.Logger, type(rtklibpost.logger))
        self.assertEqual("RtkLibPost", rtklibpost.logger.name)

    def test_init_with_disable_logger(self):
        rtklibpost = RtkLibPost(False)
        self.assertEqual(logging.Logger, type(rtklibpost.logger))
        self.assertEqual("RtkLibPost", rtklibpost.logger.name)

    def test_init_with_my_logger(self):
        logger = logging.getLogger()
        rtklibpost = RtkLibPost(logger=logger)
        self.assertEqual(logger, rtklibpost.logger)
        self.assertEqual("root", rtklibpost.logger.name)

    def test_init_check_dublicate_handlers(self):
        rtklibpost = RtkLibPost()
        rtklibpost = RtkLibPost()
        self.assertEqual(1, len(rtklibpost.logger.handlers))

    def test_get_default_config(self):
        config = {
            'pos1-posmode': '0',
            'pos1-frequency':  '2',
            'pos1-soltype':  '0',
            'pos1-elmask':  '15',
            'pos1-snrmask_r':  'off',
            'pos1-snrmask_b':  'off',
            'pos1-snrmask_l1':  '0,0,0,0,0,0,0,0,0',
            'pos1-snrmask_l2':  '0,0,0,0,0,0,0,0,0',
            'pos1-snrmask_l5':  '0,0,0,0,0,0,0,0,0',
            'pos1-dynamics':  '0',
            'pos1-tidecorr':  '0',
            'pos1-ionoopt':  '1',
            'pos1-tropopt':  '1',
            'pos1-sateph':  '0',
            'pos1-posopt1':  '0',
            'pos1-posopt2':  '0',
            'pos1-posopt3':  '0',
            'pos1-posopt4':  '0',
            'pos1-posopt5':  '0',
            'pos1-posopt6':  '0',
            'pos1-exclsats':  '',
            'pos1-navsys':  '1',

            'pos2-armode':  '1',
            'pos2-gloarmode':  '1',
            'pos2-bdsarmode':  '1',
            'pos2-arthres':  '3',
            'pos2-arthres1':  '0.9999',
            'pos2-arthres2':  '0.25',
            'pos2-arthres3':  '0.1',
            'pos2-arthres4':  '0.05',
            'pos2-arlockcnt':  '0',
            'pos2-arelmask':  '0',
            'pos2-arminfix':  '10',
            'pos2-armaxiter':  '1',
            'pos2-elmaskhold':  '0',
            'pos2-aroutcnt':  '5',
            'pos2-maxage':  '30',
            'pos2-syncsol':  'off',
            'pos2-slipthres':  '0.05',
            'pos2-rejionno':  '30',
            'pos2-rejgdop':  '30',
            'pos2-niter':  '1',
            'pos2-baselen':  '0',
            'pos2-basesig':  '0',

            'out-solformat':  '0',
            'out-outhead':  '1',
            'out-outopt':  '1',
            'out-outvel':  '0',
            'out-timesys':  '0',
            'out-timeform':  '1',
            'out-timendec':  '3',
            'out-degform':  '0',
            'out-fieldsep':  '',
            'out-outsingle':  '0',
            'out-maxsolstd':  '0',
            'out-height':  '0',
            'out-geoid':  '0',
            'out-solstatic':  '0',
            'out-nmeaintv1':  '0',
            'out-nmeaintv2':  '0',
            'out-outstat':  '0',

            'stats-eratio1':  '100',
            'stats-eratio2':  '100',
            'stats-errphase':  '0.003',
            'stats-errphaseel':  '0.003',
            'stats-errphasebl':  '0',
            'stats-errdoppler':  '1',
            'stats-stdbias':  '30',
            'stats-stdiono':  '0.03',
            'stats-stdtrop':  '0.3',
            'stats-prnaccelh':  '10',
            'stats-prnaccelv':  '10',
            'stats-prnbias':  '0.0001',
            'stats-prniono':  '0.001',
            'stats-prntrop':  '0.0001',
            'stats-prnpos':  '0',
            'stats-clkstab':  '5E-12',

            'ant1-postype':  '0',
            'ant1-pos1':  '90',
            'ant1-pos2':  '0',
            'ant1-pos3':  '-6335367.62849036',
            'ant1-anttype':  '',
            'ant1-antdele':  '0',
            'ant1-antdeln':  '0',
            'ant1-antdelu':  '0',

            'ant2-postype':  '0',
            'ant2-pos1':  '90',
            'ant2-pos2':  '0',
            'ant2-pos3':  '-6335367.62849036',
            'ant2-anttype':  '',
            'ant2-antdele':  '0',
            'ant2-antdeln':  '0',
            'ant2-antdelu':  '0',
            'ant2-maxaveep':  '0',
            'ant2-initrst':  'off',

            'misc-timeinterp':  'off',
            'misc-sbasatsel':  '0',
            'misc-rnxopt1':  '',
            'misc-rnxopt2':  '',
            'misc-pppopt':  '',
            'file-satantfile':  '',
            'file-rcvantfile':  '',
            'file-staposfile':  '',
            'file-geoidfile':  '',
            'file-ionofile':  '',
            'file-dcbfile':  '',
            'file-eopfile':  '',
            'file-blqfile':  '',
            'file-tempdir':  '',
            'file-geexefile':  '',
            'file-solstatfile':  '',
            'file-tracefile':  ''
        }

        rtklibpost = RtkLibPost(False)
        conf_from = rtklibpost.get_default_config()
        self.assertEqual(config, conf_from)

    def test__get_start_date_from_sp3(self):
        rtklibpost = RtkLibPost(False)

        # invalid version sp3
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ("#dP2022  1  1  0  0  0.00000000      96 ORBIT IGb14 HLM  IGS\n"
                    "## 2190 518400.00000000   900.00000000 59580 0.0000000000000\n")

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            with self.assertRaises(Exception) as e:
                rtklibpost._get_start_date_from_sp3(temp_file.name)
            self.assertEqual(str(e.exception), "Invalid sp3 version #d")

        # get date
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ("#cP2022  1  1  0  0  0.00000000      96 ORBIT IGb14 HLM  IGS\n"
                    "## 2190 518400.00000000   900.00000000 59580 0.0000000000000\n")

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            res = rtklibpost._get_start_date_from_sp3(temp_file.name)
            self.assertEqual("2022-01-01", res)

        # empty date
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ""

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            with self.assertRaises(Exception) as e:
                rtklibpost._get_start_date_from_sp3(temp_file.name)
            self.assertEqual(str(e.exception), "Invalid sp3 version ")

    def test__get_start_date_from_clk(self):
        rtklibpost = RtkLibPost(False)

        # invalid version rinex
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ('     4.00           C                                       RINEX VERSION / TYPE\n'
                    'CCLOCK              IGSACC @ GA and MIT                     PGM / RUN BY / DATE \n'
                    'GPS week: 2086   Day: 3   MJD: 58849                        COMMENT             \n'
                    'THE COMBINED CLOCKS ARE A WEIGHTED AVERAGE OF:              COMMENT             \n'
                    )

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            with self.assertRaises(Exception) as e:
                rtklibpost._get_start_date_from_clk(temp_file.name)
            self.assertEqual(str(e.exception), "Unknown version rinex 4.00")

        # valid version rinex
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ('     3.00           C                                       RINEX VERSION / TYPE\n'
                    'CCLOCK              IGSACC @ GA and MIT                     PGM / RUN BY / DATE \n'
                    'GPS week: 2086   Day: 3   MJD: 58849                        COMMENT             \n'
                    'THE COMBINED CLOCKS ARE A WEIGHTED AVERAGE OF:              COMMENT             \n'
                    )

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            res = rtklibpost._get_start_date_from_clk(temp_file.name)
            self.assertEqual("2020-01-01", res)

        with tempfile.NamedTemporaryFile() as temp_file:
            text = ('     2.00           C                                       RINEX VERSION / TYPE\n'
                    'CCLOCK              IGSACC @ GA and MIT                     PGM / RUN BY / DATE \n'
                    'GPS week: 2086   Day: 3   MJD: 58849                        COMMENT             \n'
                    'THE COMBINED CLOCKS ARE A WEIGHTED AVERAGE OF:              COMMENT             \n'
                    )

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            res = rtklibpost._get_start_date_from_clk(temp_file.name)
            self.assertEqual("2020-01-01", res)

        # empty date
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ""

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            res = rtklibpost._get_start_date_from_clk(temp_file.name)
            self.assertEqual("", res)

    def test__get_dates_from_erp(self):
        rtklibpost = RtkLibPost(False)

        # invalid version erp
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ('version 3\n'
                    'EOP  SOLUTION\n'
                    '  MJD         X        Y     UT1-UTC    LOD   Xsig   Ysig   UTsig LODsig  Nr Nf Nt     Xrt    Yrt  Xrtsig Yrtsig   dpsi    deps\n'
                    '               10**-6"        .1us    .1us/d    10**-6"     .1us  .1us/d                10**-6"/d    10**-6"/d        10**-6\n'
                    '59574.50    63520   269667  -1080050   5520      3      3       0      7   0  0  0   -1562   1332      13     14      0       0\n'
                    '59575.50    61960   271091  -1086063   6556      3      3       0      6   0  0  0   -1676   1512      13     13      0       0\n'
                    '59576.50    60160   272734  -1092382   6326      3      3       0      6   0  0  0   -1923   1587      12     12      0       0\n'
                    '59577.50    58396   274117  -1098201   5364      3      3       0      6   0  0  0   -1476   1133      12     13      0       0\n'
                    '59578.50    57084   275319  -1102520   3248      3      3       0      6   0  0  0   -1532   1110      12     12      0       0\n'
                    '59579.50    55409   276524  -1104540    691      3      3       0      6   0  0  0   -1846    947      12     12      0       0\n'
                    '59580.50    53978   277423  -1104225  -1362      4      4       0      7   0  0  0   -1220    932      14     14      0       0\n'
                    )

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            with self.assertRaises(Exception) as e:
                rtklibpost._get_dates_from_erp(temp_file.name)
            self.assertEqual(str(e.exception), "Unknown version erp 3")

        # valid version erp
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ('version 2\n'
                    'EOP  SOLUTION\n'
                    '  MJD         X        Y     UT1-UTC    LOD   Xsig   Ysig   UTsig LODsig  Nr Nf Nt     Xrt    Yrt  Xrtsig Yrtsig   dpsi    deps\n'
                    '               10**-6"        .1us    .1us/d    10**-6"     .1us  .1us/d                10**-6"/d    10**-6"/d        10**-6\n'
                    '59574.50    63520   269667  -1080050   5520      3      3       0      7   0  0  0   -1562   1332      13     14      0       0\n'
                    '59575.50    61960   271091  -1086063   6556      3      3       0      6   0  0  0   -1676   1512      13     13      0       0\n'
                    '59576.50    60160   272734  -1092382   6326      3      3       0      6   0  0  0   -1923   1587      12     12      0       0\n'
                    '59577.50    58396   274117  -1098201   5364      3      3       0      6   0  0  0   -1476   1133      12     13      0       0\n'
                    '59578.50    57084   275319  -1102520   3248      3      3       0      6   0  0  0   -1532   1110      12     12      0       0\n'
                    '59579.50    55409   276524  -1104540    691      3      3       0      6   0  0  0   -1846    947      12     12      0       0\n'
                    '59580.50    53978   277423  -1104225  -1362      4      4       0      7   0  0  0   -1220    932      14     14      0       0\n'
                    )

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            res = rtklibpost._get_dates_from_erp(temp_file.name)
            self.assertEqual(["2021-12-26",
                              "2021-12-27",
                              "2021-12-28",
                              "2021-12-29",
                              "2021-12-30",
                              "2021-12-31",
                              "2022-01-01"], res)

        # empty date
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ""

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            with self.assertRaises(IndexError):
                res = rtklibpost._get_dates_from_erp(temp_file.name)

    def test__get_start_date_from_ionex(self):

        rtklibpost = RtkLibPost(False)
        # invalid version ionex
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ("     2.0            IONOSPHERE MAPS     MIX                 IONEX VERSION / TYPE\n"
                    "cmpcmb v1.2          GRL/UWM             6-aug-23 18:02     PGM / RUN BY / DATE \n")

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            with self.assertRaises(Exception) as e:
                rtklibpost._get_start_date_from_ionex(temp_file.name)
            self.assertEqual(str(e.exception), "Unknown version ionex 2.0")

        # valid version erp
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ("     1.0            IONOSPHERE MAPS     MIX                 IONEX VERSION / TYPE\n"
                    "cmpcmb v1.2          GRL/UWM             6-aug-23 18:02     PGM / RUN BY / DATE \n"
                    "  2023     7    18     0     0     0                        EPOCH OF FIRST MAP  \n"
                    "  2023     7    19     0     0     0                        EPOCH OF LAST MAP \n")

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            res = rtklibpost._get_start_date_from_ionex(temp_file.name)
            self.assertEqual("2023-07-18", res)

        # empty date
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ""

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            res = rtklibpost._get_start_date_from_ionex(temp_file.name)
            self.assertEqual("", res)

    def test__get_start_date_from_dcb(self):
        rtklibpost = RtkLibPost(False)
        # invalid version dcb
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ("%=BIA 2.00 CAS 19:004:48470   CAS 2019:001:00000 2019:002:00000 R 00003488      \n"
                    "*-------------------------------------------------------------------------------\n"
                    "* Bias Solution INdependent EXchange Format (Bias-SINEX)                        \n"
                    "*-------------------------------------------------------------------------------\n")

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            with self.assertRaises(Exception) as e:
                rtklibpost._get_start_date_from_dcb(temp_file.name)
            self.assertEqual(str(e.exception), "Unknown version dcb 2.00")

        # valid version erp
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ("%=BIA 1.00 CAS 19:004:48470   CAS 2019:001:00000 2019:002:00000 R 00003488      \n"
                    "*-------------------------------------------------------------------------------\n"
                    "* Bias Solution INdependent EXchange Format (Bias-SINEX)                        \n"
                    "*-------------------------------------------------------------------------------\n")

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            res = rtklibpost._get_start_date_from_dcb(temp_file.name)
            self.assertEqual("2019-01-01", res)

        with tempfile.NamedTemporaryFile() as temp_file:
            text = ("%=BIA 0.01 IGG 15:278:77362 IGG 15:001:00000 15:002:00000 P 00000 0\n"
                    "*-------------------------------------------------------------------------------\n"
                    "* Bias Solution INdependent EXchange Format (Bias-SINEX)                        \n"
                    "*-------------------------------------------------------------------------------\n")

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            res = rtklibpost._get_start_date_from_dcb(temp_file.name)
            self.assertEqual("2015-01-01", res)

        # empty date
        with tempfile.NamedTemporaryFile() as temp_file:
            text = ""

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            with self.assertRaises(IndexError):
                res = rtklibpost._get_start_date_from_dcb(temp_file.name)

    def test_start_single_processing_raises(self):
        rtklib = RtkLibPost(False)

        # test types, raises
        with self.assertRaises(Exception):
            rtklib.start_single_processing(None, "", {"": ""}, 0, False)

        with self.assertRaises(Exception):
            rtklib.start_single_processing({"": ""}, None, {"": ""}, 0, False)

        with self.assertRaises(Exception):
            rtklib.start_single_processing({"": ""}, "", None, 0, False)

        with self.assertRaises(Exception):
            rtklib.start_single_processing({"": ""}, "", {"": ""}, None, False)

        with self.assertRaises(Exception):
            rtklib.start_single_processing({"": ""}, "", {"": ""}, 0, None)

        with self.assertRaises(ValueError) as e:
            rtklib.start_single_processing({"rover": "path_to_file.obs"}, "", {"": ""}, 0, False)
        self.assertEqual(str(e.exception), "Output directory does not exist")

        with self.assertRaises(ValueError) as e:
            rtklib.start_single_processing({"nav": "path_to_file.nav"}, "", {"": ""}, 0, False)
        self.assertEqual(str(e.exception), "Rover path is not set")

        with (self.assertRaises(ValueError) as e,
              patch("os.path.isfile") as mock_isfile,
              patch("os.path.isdir") as mock_isdir):
            mock_isdir.return_value = True
            mock_isfile.side_effect = [False]
            rtklib.start_single_processing(
                {"rover": "path_to_file.obs", "nav": "path_to_file.nav"}, "", {"": ""}, 0, False)
        self.assertEqual(str(e.exception), "Path to file 'path_to_file.obs' does not exist")

        with (self.assertRaises(ValueError) as e,
              patch("os.path.isfile") as mock_isfile,
              patch("os.path.isdir") as mock_isdir):
            mock_isdir.return_value = True
            mock_isfile.side_effect = [True, False]
            rtklib.start_single_processing(
                {"rover": "path_to_file.obs", "nav": "path_to_file.nav"}, "", {"": ""}, 0, False)
        self.assertEqual(str(e.exception), "Path to file 'path_to_file.nav' does not exist")

    def test_start_single_processing(self):
        rtklib = RtkLibPost(False)
        mock_dict2config = MagicMock()
        rtklib.dict2config = mock_dict2config

        mock_make_cmd = MagicMock()
        mock_make_cmd.return_value = ["cmd1", "cmd2"]
        rtklib._RtkLibPost__make_cmd = mock_make_cmd

        mock_start_process = MagicMock()
        rtklib._RtkLibPost__start_process = mock_start_process

        mock_create_vars = MagicMock()
        rtklib._RtkLibPost__create_vars = mock_create_vars

        # input path to file
        with (patch("moncenterlib.gnss.postprocessing.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.postprocessing.os.path.isdir") as mock_isdir,
              ):

            mock_isfile.return_value = True
            mock_isdir.side_effect = [True, False]
            paths = {"rover": "path2rover.obs", "nav": "path2nav.nav"}
            config = {"param1": "val1", "param2": "val2"}
            rtklib.start_single_processing(paths, "/output", config, 5, False)

        self.assertTrue(mock_create_vars.called)

        self.assertEqual(mock_dict2config.mock_calls[0].args[0], {'param1': 'val1', 'param2': 'val2'})
        self.assertEqual(type(mock_dict2config.mock_calls[0].args[1]), tempfile._TemporaryFileWrapper)
        self.assertEqual(mock_dict2config.mock_calls[0].args[2], {'rover': 'path2rover.obs', 'nav': 'path2nav.nav'})

        self.assertEqual(mock_make_cmd.mock_calls[0].args[0], {'rover': 'path2rover.obs', 'nav': 'path2nav.nav'})
        self.assertEqual(mock_make_cmd.mock_calls[0].args[1], '/output')
        self.assertEqual(mock_make_cmd.mock_calls[0].args[2], 5)
        self.assertEqual(type(mock_make_cmd.mock_calls[0].args[3]), tempfile._TemporaryFileWrapper)

        self.assertEqual(mock_start_process.mock_calls[0].args, (["cmd1", "cmd2"], False))

    def test_start_multi_processing_raises(self):
        rtklib = RtkLibPost(False)

        with self.assertRaises(Exception):
            rtklib.start_multi_processing(None, "", {"": ""}, 0, 1)

        with self.assertRaises(Exception):
            rtklib.start_multi_processing({"": ""}, None, {"": ""}, 0, 1)

        with self.assertRaises(Exception):
            rtklib.start_multi_processing({"": ""}, "", None, 0, 1)

        with self.assertRaises(Exception):
            rtklib.start_multi_processing({"": ""}, "", {"": ""}, None, 1)

        with self.assertRaises(Exception):
            rtklib.start_multi_processing({"": ""}, "", {"": ""}, 0, None)

        with self.assertRaises(ValueError) as e:
            rtklib.start_multi_processing({"rover": "path_to_file.obs"}, "", {"": ""}, 0, False)
        self.assertEqual(str(e.exception), "Output directory does not exist")

    @patch("queue.Queue")
    @patch("os.path.isdir")
    @patch("threading.Thread")
    @patch("threading.Semaphore")
    def test_start_multi_processing(self, mock_semaphore, mock_thread, mock_isdir, mock_queue):
        mock_isdir.return_value = True

        rtklib = RtkLibPost(False)
        mock_dict2config = MagicMock()
        rtklib.dict2config = mock_dict2config

        # mock_make_cmd = MagicMock()
        # mock_make_cmd.return_value = ["cmd1", "cmd2"]
        # rtklib._RtkLibPost__make_cmd = mock_make_cmd

        # mock_start_process = MagicMock()
        # rtklib._RtkLibPost__start_process = mock_start_process

        # mock_create_vars = MagicMock()
        # rtklib._RtkLibPost__create_vars = mock_create_vars

        match_list = {
            "2025-01-01": {
                "rovers": ["path2rover1.obs"], "nav": "path2nav1.nav"
            },

            "2025-01-02": {
                "rovers": ["path2rover2.obs"], "nav": "path2nav2.nav"
            }
        }
        config = {"param1": "val1", "param2": "val2"}
        rtklib.start_multi_processing(match_list, "/output_dir", config, 5, 4)

        self.assertEqual(mock_queue.mock_calls[1].args, ({'nav': 'path2nav1.nav', 'rover': 'path2rover1.obs'}, ))
        self.assertEqual(mock_queue.mock_calls[2].args, ({'nav': 'path2nav2.nav', 'rover': 'path2rover2.obs'}, ))
        self.assertEqual(mock_semaphore.mock_calls[0], call(4))

        # TODO: не доделан. Нет понимания как протестировать

    def test_get_last_status(self):
        rtk_post = RtkLibPost(False)

        self.assertEqual(rtk_post.get_last_status(), {})

        mock_process = MagicMock()
        rtk_post._RtkLibPost__process = {"/home/file1": mock_process}
        rtk_post.std_log = {
            "/home/file1": {
                "stdout": ["Status: Running", " "],
                "stderr": ["Error: File not found",  " "]
            }
        }

        self.assertEqual(rtk_post.get_last_status(), {
                         '/home/file1': {'stdout': 'Status: Running', 'stderr': 'Error: File not found', 'isStop': True}})

        rtk_post._RtkLibPost__process = {"/home/file1": None}
        self.assertEqual(rtk_post.get_last_status(), {
                         '/home/file1': {'stdout': 'Status: Running', 'stderr': 'Error: File not found', 'isStop': False}})

        mock_process.pull.return_value = "Not None"
        self.assertEqual(rtk_post.get_last_status(), {
                         '/home/file1': {'stdout': 'Status: Running', 'stderr': 'Error: File not found', 'isStop': False}})

        mock_process = MagicMock()
        rtk_post._RtkLibPost__process = {"/home/file1": mock_process}
        rtk_post.std_log = {
            "/home/file1": {
                "stdout": ["Status: Running", "ddsdsds", " "],
                "stderr": ["Error: File not found", "dssdsdsd", " "]
            }
        }
        self.assertEqual(rtk_post.get_last_status(), {
                         '/home/file1': {'stdout': 'ddsdsds', 'stderr': 'dssdsdsd', 'isStop': True}})

    def test_get_full_status(self):
        rtk_post = RtkLibPost(False)
        self.assertEqual(rtk_post.get_full_status(), {})

        rtk_post.std_log = {
            "/home/file1": {
                "stdout": ["Status: Running", "ddsdsds"],
                "stderr": ["Error: File not found", "dssdsdsd"]
            }
        }

        self.assertEqual(rtk_post.get_full_status(), {
            "/home/file1": {
                "stdout": ["Status: Running", "ddsdsds"],
                "stderr": ["Error: File not found", "dssdsdsd"]
            }
        })

    def test_match_files_input_raises(self):
        rtklib = RtkLibPost(False)

        with self.assertRaises(Exception):
            rtklib.match_files(None, True)

        with self.assertRaises(Exception):
            rtklib.match_files("", None)

        with self.assertRaises(ValueError) as e:
            rtklib.match_files({"fcb": ""})
        self.assertEqual(str(e.exception), "Does not support fcb")

        with self.assertRaises(ValueError) as e:
            rtklib.match_files({"sbas": ""})
        self.assertEqual(str(e.exception), "Does not support sbas")

        with self.assertRaises(ValueError) as e:
            rtklib.match_files({"otl": "bla"})
        self.assertEqual(str(e.exception), "Invalid file path: bla")

        with self.assertRaises(ValueError) as e:
            rtklib.match_files({"satant": "bla"})
        self.assertEqual(str(e.exception), "Invalid file path: bla")

        with self.assertRaises(ValueError) as e:
            rtklib.match_files({"rcvant": "bla"})
        self.assertEqual(str(e.exception), "Invalid file path: bla")

        with self.assertRaises(ValueError) as e:
            rtklib.match_files({"rover": "path2dir_obs"})
        self.assertEqual(str(e.exception), "Invalid file path: path2dir_obs")

    @patch("os.path.isdir")
    @patch("os.path.isfile")
    @patch("moncenterlib.gnss.tools.get_start_date_from_obs")
    @patch("moncenterlib.gnss.tools.get_start_date_from_nav")
    @patch("moncenterlib.tools.get_files_from_dir")
    def test_match_files(self, mock_get_files, mock_get_nav, mock_get_obs, mock_isdir, mock_isfile):
        mock_isdir.retutn_value = True
        mock_isfile.retutn_value = True

        rtklibpost = RtkLibPost(False)

        # rover, several days
        input_rnx = {"rover": "path2dir_obs"}
        mock_get_files.return_value = ["path2file_obs1", "path2file_obs2"]
        mock_get_obs.side_effect = ["2020-01-01", "2020-01-02"]
        match_list, no_match = rtklibpost.match_files(input_rnx)
        self.assertEqual(match_list, {"2020-01-01": {"rovers": ["path2file_obs1"]},
                                      "2020-01-02": {"rovers": ["path2file_obs2"]}})
        self.assertEqual(no_match, {})

        # rover, same days
        input_rnx = {"rover": "path2dir_obs"}
        mock_get_files.return_value = ["path2file_obs1", "path2file_obs2"]
        mock_get_obs.side_effect = ["2020-01-01", "2020-01-01"]
        match_list, no_match = rtklibpost.match_files(input_rnx)
        self.assertEqual(match_list, {"2020-01-01": {"rovers": ["path2file_obs1", "path2file_obs2"]}})
        self.assertEqual(no_match, {})

        # rover, Exception
        input_rnx = {"rover": "path2dir_obs"}
        mock_get_files.return_value = ["path2file_obs1", "path2file_obs2", "path2file_obs3"]
        mock_get_obs.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        match_list, no_match = rtklibpost.match_files(input_rnx)
        self.assertEqual(match_list, {"2020-01-01": {"rovers": ["path2file_obs1"]},
                                      "2020-01-03": {"rovers": ["path2file_obs3"]}})
        self.assertEqual(no_match, {})

        # base, several days, Exception
        input_rnx = {"base": "path2dir_obs"}
        mock_get_files.return_value = ["path2file_base1", "path2file_base2", "path2file_base3"]
        mock_get_obs.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        match_list, no_match = rtklibpost.match_files(input_rnx)
        self.assertEqual(match_list, {"2020-01-01": {"base": "path2file_base1"},
                                      "2020-01-03": {"base": "path2file_base3"}})
        self.assertEqual(no_match, {})

        # nav, several days, Exception
        input_rnx = {"nav": "path2dir_nav"}
        mock_get_files.return_value = ["path2file_nav1", "path2file_nav2", "path2file_nav3"]
        mock_get_nav.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        match_list, no_match = rtklibpost.match_files(input_rnx)
        self.assertEqual(match_list, {"2020-01-01": {"nav": "path2file_nav1"},
                                      "2020-01-03": {"nav": "path2file_nav3"}})
        self.assertEqual(no_match, {})

        # sp3, several days, Exception
        input_rnx = {"sp3": "path2dir_sp3"}
        mock_get_files.return_value = ["path2file_sp31", "path2file_sp32", "path2file_sp33"]
        mock_get_sp3 = MagicMock()
        mock_get_sp3.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        rtklibpost._get_start_date_from_sp3 = mock_get_sp3
        match_list, no_match = rtklibpost.match_files(input_rnx)
        self.assertEqual(match_list, {"2020-01-01": {"sp3": "path2file_sp31"},
                                      "2020-01-03": {"sp3": "path2file_sp33"}})
        self.assertEqual(no_match, {})

        # clk, several days, Exception
        input_rnx = {"clk": "path2dir_clk"}
        mock_get_files.return_value = ["path2file_clk1", "path2file_clk2", "path2file_clk3"]
        mock_get_clk = MagicMock()
        mock_get_clk.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        rtklibpost._get_start_date_from_clk = mock_get_clk
        match_list, no_match = rtklibpost.match_files(input_rnx)
        self.assertEqual(match_list, {"2020-01-01": {"clk": "path2file_clk1"},
                                      "2020-01-03": {"clk": "path2file_clk3"}})
        self.assertEqual(no_match, {})

        # erp, several days
        input_rnx = {"erp": "path2dir_erp"}
        mock_get_files.return_value = ["path2file_erp1", "path2file_erp2", "path2file_erp3"]
        mock_get_erp = MagicMock()
        mock_get_erp.side_effect = [["2020-01-01", "2020-01-02"], Exception(), ["2020-01-03", "2020-01-04"]]
        rtklibpost._get_dates_from_erp = mock_get_erp
        match_list, no_match = rtklibpost.match_files(input_rnx)
        self.assertEqual(match_list, {"2020-01-01": {"erp": "path2file_erp1"},
                                      "2020-01-02": {"erp": "path2file_erp1"},
                                      "2020-01-03": {"erp": "path2file_erp3"},
                                      "2020-01-04": {"erp": "path2file_erp3"}})
        self.assertEqual(no_match, {})

        # dcb, several days, Exception
        input_rnx = {"dcb": "path2dir_dcb"}
        mock_get_files.return_value = ["path2file_dcb1", "path2file_dcb2", "path2file_dcb3"]
        mock_get_dcb = MagicMock()
        mock_get_dcb.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        rtklibpost._get_start_date_from_dcb = mock_get_dcb
        match_list, no_match = rtklibpost.match_files(input_rnx)
        self.assertEqual(match_list, {"2020-01-01": {"dcb": "path2file_dcb1"},
                                      "2020-01-03": {"dcb": "path2file_dcb3"}})
        self.assertEqual(no_match, {})

        # ionex, several days, Exception
        input_rnx = {"ionex": "path2dir_ionex"}
        mock_get_files.return_value = ["path2file_ionex1", "path2file_ionex2", "path2file_ionex3"]
        mock_get_ionex = MagicMock()
        mock_get_ionex.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        rtklibpost._get_start_date_from_ionex = mock_get_ionex
        match_list, no_match = rtklibpost.match_files(input_rnx)
        self.assertEqual(match_list, {"2020-01-01": {"ionex": "path2file_ionex1"},
                                      "2020-01-03": {"ionex": "path2file_ionex3"}})
        self.assertEqual(no_match, {})

        # all types
        input_rnx = {"ionex": "path2dir_ionex",
                     "dcb": "path2dir_dcb",
                     "erp": "path2dir_erp",
                     "clk": "path2dir_clk",
                     "sp3": "path2dir_sp3",
                     "nav": "path2dir_nav",
                     "base": "path2dir_obs",
                     "rover": "path2dir_obs"}

        mock_get_ionex.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        mock_get_dcb.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        mock_get_erp.side_effect = [["2020-01-01", "2020-01-02"], Exception(), ["2020-01-03", "2020-01-04"]]
        mock_get_clk.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        mock_get_sp3.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        mock_get_nav.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        mock_get_obs.side_effect = ["2020-01-01", Exception, "2020-01-03", "2020-01-01", Exception, "2020-01-03"]
        mock_get_files.side_effect = [["path2file_ionex1", "path2file_ionex2", "path2file_ionex3"],
                                      ["path2file_dcb1", "path2file_dcb2", "path2file_dcb3"],
                                      ["path2file_erp1", "path2file_erp2", "path2file_erp3"],
                                      ["path2file_clk1", "path2file_clk2", "path2file_clk3"],
                                      ["path2file_sp31", "path2file_sp32", "path2file_sp33"],
                                      ["path2file_nav1", "path2file_nav2", "path2file_nav3"],
                                      ["path2file_base1", "path2file_base2", "path2file_base3"],
                                      ["path2file_obs1", "path2file_obs2", "path2file_obs3"]]
        match_list, no_match = rtklibpost.match_files(input_rnx)
        self.assertEqual(match_list, {"2020-01-01": {'rovers': ['path2file_obs1'], 'base': 'path2file_base1', 'nav': 'path2file_nav1', 'sp3': 'path2file_sp31', 'clk': 'path2file_clk1', 'ionex': 'path2file_ionex1', 'erp': 'path2file_erp1', 'dcb': 'path2file_dcb1'},
                                      "2020-01-03": {'rovers': ['path2file_obs3'], 'base': 'path2file_base3', 'nav': 'path2file_nav3', 'sp3': 'path2file_sp33', 'clk': 'path2file_clk3', 'ionex': 'path2file_ionex3', 'erp': 'path2file_erp3', 'dcb': 'path2file_dcb3'}})
        self.assertEqual(no_match, {"2020-01-02": {'erp': 'path2file_erp1'},
                                    "2020-01-04": {'erp': 'path2file_erp3'}})

        # test add additional files
        input_rnx = {"nav": "path2dir_nav",
                     "rover": "path2dir_obs",
                     "otl": "path2dtl.otl",
                     "satant": "path2satant.atx",
                     "rcvant": "path2rcvant.atx"
                     }

        mock_get_nav.side_effect = ["2020-01-01", Exception, "2020-01-03"]
        mock_get_obs.side_effect = ["2020-01-01", Exception, "2020-01-03", "2020-01-01", Exception, "2020-01-03"]
        mock_get_files.side_effect = [["path2file_nav1", "path2file_nav2", "path2file_nav3"],
                                      ["path2file_obs1", "path2file_obs2", "path2file_obs3"]]

        match_list, no_match = rtklibpost.match_files(input_rnx)

        self.assertEqual(match_list, {"2020-01-01": {'rovers': ['path2file_obs1'], 'nav': 'path2file_nav1', 'otl': 'path2dtl.otl', 'satant': 'path2satant.atx', 'rcvant': 'path2rcvant.atx'},
                                      "2020-01-03": {'rovers': ['path2file_obs3'], 'nav': 'path2file_nav3', 'otl': 'path2dtl.otl', 'satant': 'path2satant.atx', 'rcvant': 'path2rcvant.atx'}})
        self.assertEqual(no_match, {})

    def test_config2dict(self):
        rtklibpost = RtkLibPost(False)

        # raises
        with self.assertRaises(Exception):
            rtklibpost.config2dict(None)

        with self.assertRaises(ValueError) as e:
            rtklibpost.config2dict("/blablalba/")
        self.assertEqual(str(e.exception), "Path to path2conf is strange.")

        with tempfile.NamedTemporaryFile() as temp_file:
            text = ("# rtkpost options (v.2.4.3 b34)\n"
                    "pos1-posmode       =single     # Positioning Mode (0:single,1:dgps,2:kinematic,3:static,4:movingbase,5:fixed,6:ppp-kine,7:ppp-static,8:ppp-fixed)\n"
                    "pos1-frequency     =l1+2       # Frequencies (1:l1,2:l1+2,3:l1+2+3,4:l1+2+3+4,5:l1+2+3+4+5)\n"
                    "pos1-soltype       =forward    # Filter Type (0:forward,1:backward,2:combined)\n"
                    "pos1-elmask        =15         # Elevation Mask (deg)\n"
                    "pos1-snrmask_r     =off        # SNR Mask (0:off,1:on)\n"
                    "pos1-snrmask_b     =off        # SNR Mask (0:off,1:on)\n"
                    "pos1-snrmask_L1    =0,0,0,0,0,0,0,0,0 # SNR Mask\n"
                    "pos1-snrmask_L2    =0,0,0,0,0,0,0,0,0 # SNR Mask\n"
                    )

            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            res = rtklibpost.config2dict(temp_file.name)
            self.assertEqual({'pos1-posmode': 'single',
                              'pos1-frequency': 'l1+2',
                              'pos1-soltype': 'forward',
                              'pos1-elmask': '15',
                              'pos1-snrmask_r': 'off',
                              'pos1-snrmask_b': 'off',
                              'pos1-snrmask_L1': '0,0,0,0,0,0,0,0,0',
                              'pos1-snrmask_L2': '0,0,0,0,0,0,0,0,0'
                              }, res)

    @patch("builtins.open")
    def test_dict2config(self, mock_open):
        rtklib = RtkLibPost(False)

        with self.assertRaises(Exception):
            rtklib.dict2config(None, "", {"", ""})

        with self.assertRaises(Exception):
            rtklib.dict2config({"": ""}, None, {"", ""})

        with self.assertRaises(Exception):
            rtklib.dict2config({"": ""}, "", None)

        # check path2config
        rtklib.dict2config({"": ""}, "/path2config", {"": ""})
        self.assertEqual(mock_open.mock_calls[0], call('/path2config', 'w', encoding='utf-8'))

        # check tempfile
        mock_open.reset_mock()
        with tempfile.NamedTemporaryFile() as temp_file:
            rtklib.dict2config({"": ""}, temp_file, {"": ""})
            self.assertEqual(mock_open.mock_calls[0], call(temp_file.name, 'w', encoding='utf-8'))

        # check add additional files, empty
        mock_open.reset_mock()
        rtklib.dict2config({"param1": "val1"}, "/path2config", {"": ""})
        self.assertEqual(mock_open.mock_calls[2], call().__enter__().write('param1=val1\n'))
        self.assertEqual(mock_open.mock_calls[3], call().__enter__().write('file-eopfile=\n'))
        self.assertEqual(mock_open.mock_calls[4], call().__enter__().write('file-dcbfile=\n'))
        self.assertEqual(mock_open.mock_calls[5], call().__enter__().write('file-blqfile=\n'))
        self.assertEqual(mock_open.mock_calls[6], call().__enter__().write('file-satantfile=\n'))
        self.assertEqual(mock_open.mock_calls[7], call().__enter__().write('file-rcvantfile=\n'))

        # check add additional files
        mock_open.reset_mock()
        config = {'param1': "val1"}
        input_rnx = {
            'erp': 'eop',
            'dcb': 'dcb',
            'otl': 'blq',
            'satant': 'sat',
            'rcvant': 'rcv'
        }
        rtklib.dict2config(config, "/path2config", input_rnx)
        self.assertEqual(mock_open.mock_calls[2], call().__enter__().write('param1=val1\n'))
        self.assertEqual(mock_open.mock_calls[3], call().__enter__().write('file-eopfile=eop\n'))
        self.assertEqual(mock_open.mock_calls[4], call().__enter__().write('file-dcbfile=dcb\n'))
        self.assertEqual(mock_open.mock_calls[5], call().__enter__().write('file-blqfile=blq\n'))
        self.assertEqual(mock_open.mock_calls[6], call().__enter__().write('file-satantfile=sat\n'))
        self.assertEqual(mock_open.mock_calls[7], call().__enter__().write('file-rcvantfile=rcv\n'))

    @patch("moncenterlib.tools.get_path2bin")
    def test__make_cmd(self, mock_get_path2bin):
        rtkpost = RtkLibPost(False)

        mock_get_path2bin.return_value = '/rnx2rtkp_bin'
        input_rnx = {
            'rover': 'rover_file',
            'base': 'base_file',
            'nav': 'nav_file',
            'sp3': 'sp3_file',
            'clk': 'clk_file',
            'ionex': 'ionex_file'
        }
        output_dir = '/output_dir'
        timeint = 5
        temp_file = ''
        with tempfile.NamedTemporaryFile() as temp_file:
            cmd = rtkpost._RtkLibPost__make_cmd(input_rnx, output_dir, timeint, temp_file)
            except_cmd = ['/rnx2rtkp_bin', '-ti', '5', '-k', temp_file.name, 'rover_file', 'base_file',
                          'nav_file', 'sp3_file', 'clk_file', 'ionex_file', '-o', '/output_dir/rover_file.pos']
            self.assertEqual(cmd, except_cmd)

    @patch("subprocess.Popen")
    @patch("threading.Thread")
    def test_start_process(self, mock_thread, mock_Popen):
        rtkpost = RtkLibPost(False)

        cmd = ['/rnx2rtkp_bin',
               '-ti', '5',
               '-k', "file_config",
               'rover_file',
               'base_file',
               'nav_file',
               'sp3_file',
               'clk_file',
               'ionex_file',
               '-o', '/output_dir/rover_file.pos']
        rtkpost._RtkLibPost__start_process(cmd, False)

        self.assertEqual(mock_Popen.call_args[0][0], cmd)
        self.assertEqual(mock_Popen.call_args[1], {'stderr': -1, 'stdout': -1,
                         'text': True, 'bufsize': 1, 'universal_newlines': True})

        mock_thread_start = mock_thread()
        self.assertEqual(mock_thread_start.mock_calls, [call.start(), call.start()])

        rtkpost._RtkLibPost__start_process(cmd, True)
        self.assertEqual(rtkpost._RtkLibPost__process['/output_dir/rover_file.pos'].mock_calls[0], call.wait())


if __name__ == '__main__':
    main()
