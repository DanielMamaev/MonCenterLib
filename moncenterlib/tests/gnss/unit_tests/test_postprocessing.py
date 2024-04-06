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

    def test_scan_dirs(self):
        rtklibpost = RtkLibPost(False)
        with self.assertRaises(Exception):
            rtklibpost.scan_dirs("")

        with self.assertRaises(Exception):
            rtklibpost.scan_dirs({"": ""}, None)

        with self.assertRaises(Exception):
            rtklibpost.scan_dirs({123: ""})

        with self.assertRaises(Exception):
            rtklibpost.scan_dirs({"123": 123})

        with self.assertRaises(Exception):
            rtklibpost.scan_dirs({123: ""})

        with self.assertRaises(ValueError) as e:
            rtklibpost.scan_dirs({"123": ""})
        self.assertEqual(str(e.exception), 'Unidentified key 123')

        with patch("moncenterlib.tools.get_files_from_dir") as mock_get_files:
            # check types of files
            mock_get_files.side_effect = [["file1", "file2"],
                                          ["file3", "file4"],
                                          ["file5", "file6"],
                                          ["file7", "file8"],
                                          ["file9", "file10"],
                                          ["file11", "file12"]]
            res = rtklibpost.scan_dirs({'rover': "some_dir",
                                        'base': "some_dir",
                                        'nav': "some_dir",
                                        'sp3': 'some_dir',
                                        'clk': 'some_dir',
                                        'erp': "some_dir"})
            self.assertEqual({'rover': ['file1', 'file2'],
                              'base': ['file3', 'file4'],
                              'nav': ['file5', 'file6'],
                              'sp3': ['file7', 'file8'],
                              'clk': ['file9', 'file10'],
                              'erp': ['file11', 'file12']}, res)
            self.assertEqual(("some_dir", False), mock_get_files.call_args.args)

            # check recursion
            mock_get_files.side_effect = [["file1", "file2"]]
            res = rtklibpost.scan_dirs({"rover": "some_dir"}, True)
            self.assertEqual({'rover': ['file1', 'file2']}, res)
            self.assertEqual(("some_dir", True), mock_get_files.call_args.args)

            # empty folder
            mock_get_files.side_effect = [["file1", "file2"], [], ["file5", "file6"]]
            res = rtklibpost.scan_dirs({"rover": "some_dir", "nav": "some_dir", "sp3": "some_dir"}, True)
            self.assertEqual({'rover': ['file1', 'file2'], 'sp3': ['file5', 'file6'], "nav": []}, res)
            self.assertEqual(("some_dir", True), mock_get_files.call_args.args)

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

    def test_start_input_args(self):
        rtklib = RtkLibPost(False)

        # test types, raises
        with self.assertRaises(Exception):
            rtklib.start(None, "", "", False, 0, False, True)

        with self.assertRaises(Exception):
            rtklib.start({"": ""}, None, "", False, 0, False, True)

        with self.assertRaises(Exception):
            rtklib.start({"": ""}, "", None, False, 0, False, True)

        with self.assertRaises(Exception):
            rtklib.start({"": ""}, "", "", None, 0, False, True)

        with self.assertRaises(Exception):
            rtklib.start({"": ""}, "", "", False, None, False, True)

        with self.assertRaises(Exception):
            rtklib.start({"": ""}, "", "", False, 0, None, True)

        with self.assertRaises(Exception):
            rtklib.start({"": ""}, "", "", False, 0, False, None)

        # test input_rnx and config
        with patch("moncenterlib.gnss.postprocessing.os.path.isfile") as mock_isfile:
            mock_isfile.return_value = True
            res = rtklib.start({"": ""}, "/", "", False, 0, False, True)
            self.assertEqual({'done': [], 'no_exists': [], 'no_match': []}, res)

            res = rtklib.start({"": [""]}, "/", "", False, 0, False, True)
            self.assertEqual({'done': [], 'no_exists': [], 'no_match': []}, res)

            res = rtklib.start({"": [""]}, "/", {"": ""}, False, 0, False, True)
            self.assertEqual({'done': [], 'no_exists': [], 'no_match': []}, res)

        with self.assertRaises(ValueError) as e:
            res = rtklib.start({"": ""}, "blablabla", {"": ""}, False, 0, False, True)
        self.assertEqual(str(e.exception), "Output directory does not exist")

        with self.assertRaises(ValueError) as e:
            res = rtklib.start({"": ""}, "/", "blablabla", False, 0, False, True)
        self.assertEqual(str(e.exception), "Config file does not exist")

    def test_start_variants_input_rnx(self):
        rtklibpost = RtkLibPost(False)

        rtklibpost.scan_dirs = MagicMock()

        # input path to file
        with (patch("moncenterlib.gnss.postprocessing.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.postprocessing.os.path.isdir") as mock_isdir,
              patch("moncenterlib.gnss.postprocessing.mcl_gnss_tools.get_start_date_from_obs") as mock_date_obs):

            mock_isfile.return_value = True
            mock_isdir.side_effect = [True, False]

            rtklibpost.start({"rover": "/path2file_obs"}, "/", {"": ""}, False, 0, False, False)
            self.assertEqual(mock_date_obs.call_count, 1)
            self.assertEqual(("/path2file_obs", ), mock_date_obs.call_args.args)

        # input path to directory
        with (patch("moncenterlib.gnss.postprocessing.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.postprocessing.os.path.isdir") as mock_isdir,
              patch("moncenterlib.gnss.postprocessing.mcl_gnss_tools.get_start_date_from_obs") as mock_date_obs):

            mock_isfile.return_value = False
            mock_isdir.side_effect = [True, True]
            rtklibpost.scan_dirs.return_value = {"rover": ["/path2file1", "/path2file2"]}

            rtklibpost.start({"rover": "/path2dir_obs"}, "/", {"": ""}, False, 0, False, False)

            self.assertEqual(({'rover': '/path2dir_obs'}, False), rtklibpost.scan_dirs.call_args.args)
            self.assertEqual([call('/path2file1'), call('/path2file2')], mock_date_obs.call_args_list)

        # input path from method scan_dirs
        with (patch("moncenterlib.gnss.postprocessing.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.postprocessing.os.path.isdir") as mock_isdir,
              patch("moncenterlib.gnss.postprocessing.mcl_gnss_tools.get_start_date_from_obs") as mock_date_obs):

            mock_isfile.return_value = False
            mock_isdir.side_effect = [True, False]
            input_data = {"rover": ["/path2file1", "/path2file2"]}

            rtklibpost.start(input_data, "/", {"": ""}, False, 0, False, False)

            self.assertEqual(({'rover': '/path2dir_obs'}, False), rtklibpost.scan_dirs.call_args.args)
            self.assertEqual([call('/path2file1'), call('/path2file2')], mock_date_obs.call_args_list)

    def test_start_matching_dict(self):
        # check match list in function len where if len(path_files) != len(input_rnx):.
        # path_files is part of match list

        rtklibpost = RtkLibPost(False)
        with (patch("moncenterlib.gnss.postprocessing.len") as mock_len,
              patch("moncenterlib.gnss.postprocessing.mcl_gnss_tools.get_start_date_from_obs") as mock_get_start_date_from_obs,
              patch("moncenterlib.gnss.postprocessing.mcl_gnss_tools.get_start_date_from_nav") as mock_get_start_date_from_nav):
            # rover, several days
            input_rnx = {"rover": ["path2file_obs1", "path2file_obs2"]}
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-02"]
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'rovers': ['path2file_obs1']}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'rovers': ['path2file_obs2']}, mock_len.call_args_list[2].args[0])

            # rover, same days
            mock_len.reset_mock()
            input_rnx = {"rover": ["path2file_obs1", "path2file_obs2"]}
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-01"]
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'rovers': ['path2file_obs1', 'path2file_obs2']}, mock_len.call_args_list[0].args[0])

            # base, several days
            mock_len.reset_mock()
            input_rnx = {"base": ["path2file_obs_base1", "path2file_obs_base2"]}
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-02"]
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'base': 'path2file_obs_base1'}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'base': 'path2file_obs_base2'}, mock_len.call_args_list[2].args[0])

            # nav, several days
            mock_len.reset_mock()
            input_rnx = {"nav": ["path2file_nav1", "path2file_nav2"]}
            mock_get_start_date_from_nav.side_effect = ["2020-01-01", "2020-01-02"]
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'nav': 'path2file_nav1'}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'nav': 'path2file_nav2'}, mock_len.call_args_list[2].args[0])

            # sp3, several days
            mock_len.reset_mock()
            rtklibpost._get_start_date_from_sp3 = MagicMock()
            rtklibpost._get_start_date_from_sp3.side_effect = ["2020-01-01", "2020-01-02"]
            input_rnx = {"sp3": ["path2file_sp3_1", "path2file_sp3_2"]}
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'sp3': 'path2file_sp3_1'}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'sp3': 'path2file_sp3_2'}, mock_len.call_args_list[2].args[0])

            # clk, several days
            mock_len.reset_mock()
            rtklibpost._get_start_date_from_clk = MagicMock()
            rtklibpost._get_start_date_from_clk.side_effect = ["2020-01-01", "2020-01-02"]
            input_rnx = {"clk": ["path2file_clk_1", "path2file_clk_2"]}
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'clk': 'path2file_clk_1'}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'clk': 'path2file_clk_2'}, mock_len.call_args_list[2].args[0])

            # erp, several days
            mock_len.reset_mock()
            rtklibpost._get_dates_from_erp = MagicMock()
            rtklibpost._get_dates_from_erp.side_effect = [["2020-01-01", "2020-01-02"], ["2020-01-07", "2020-01-08"]]
            input_rnx = {"erp": ["path2file_erp_1", "path2file_erp_2"]}
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'erp': 'path2file_erp_1'}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'erp': 'path2file_erp_1'}, mock_len.call_args_list[2].args[0])
            self.assertEqual({'erp': 'path2file_erp_2'}, mock_len.call_args_list[4].args[0])
            self.assertEqual({'erp': 'path2file_erp_2'}, mock_len.call_args_list[6].args[0])

            # CHECK EXCEPTIONS, continue
            # rover, several days
            mock_len.reset_mock()
            input_rnx = {"rover": ["path2file_obs1", "path2file_obs2", "path2file_obs3"]}
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", Exception(), "2020-01-03"]
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'rovers': ['path2file_obs1']}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'rovers': ['path2file_obs3']}, mock_len.call_args_list[2].args[0])

            # rover, same days
            mock_len.reset_mock()
            input_rnx = {"rover": ["path2file_obs1", "path2file_obs2", "path2file_obs3"]}
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", Exception(), "2020-01-01"]
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'rovers': ['path2file_obs1', 'path2file_obs3']}, mock_len.call_args_list[0].args[0])

            # base, several days
            mock_len.reset_mock()
            input_rnx = {"base": ["path2file_obs_base1", "path2file_obs_base2", "path2file_obs_base3"]}
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", Exception(), "2020-01-02"]
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'base': 'path2file_obs_base1'}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'base': 'path2file_obs_base3'}, mock_len.call_args_list[2].args[0])

            # nav, several days
            mock_len.reset_mock()
            input_rnx = {"nav": ["path2file_nav1", "path2file_nav2", "path2file_nav3"]}
            mock_get_start_date_from_nav.side_effect = ["2020-01-01", Exception(), "2020-01-02"]
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'nav': 'path2file_nav1'}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'nav': 'path2file_nav3'}, mock_len.call_args_list[2].args[0])

            # sp3, several days
            mock_len.reset_mock()
            rtklibpost._get_start_date_from_sp3 = MagicMock()
            rtklibpost._get_start_date_from_sp3.side_effect = ["2020-01-01", Exception(), "2020-01-02"]
            input_rnx = {"sp3": ["path2file_sp3_1", "path2file_sp3_2", "path2file_sp3_3"]}
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'sp3': 'path2file_sp3_1'}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'sp3': 'path2file_sp3_3'}, mock_len.call_args_list[2].args[0])

            # clk, several days
            mock_len.reset_mock()
            rtklibpost._get_start_date_from_clk = MagicMock()
            rtklibpost._get_start_date_from_clk.side_effect = ["2020-01-01", Exception(), "2020-01-02"]
            input_rnx = {"clk": ["path2file_clk_1", "path2file_clk_2", "path2file_clk_3"]}
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'clk': 'path2file_clk_1'}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'clk': 'path2file_clk_3'}, mock_len.call_args_list[2].args[0])

            # erp, several days
            mock_len.reset_mock()
            rtklibpost._get_dates_from_erp = MagicMock()
            rtklibpost._get_dates_from_erp.side_effect = [["2020-01-01", "2020-01-02"],
                                                          Exception(),
                                                          ["2020-01-14", "2020-01-15"]]
            input_rnx = {"erp": ["path2file_erp_1", "path2file_erp_2", "path2file_erp_3"]}
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'erp': 'path2file_erp_1'}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'erp': 'path2file_erp_1'}, mock_len.call_args_list[2].args[0])
            self.assertEqual({'erp': 'path2file_erp_3'}, mock_len.call_args_list[4].args[0])
            self.assertEqual({'erp': 'path2file_erp_3'}, mock_len.call_args_list[6].args[0])

            # all types
            mock_len.reset_mock()
            input_rnx = {"rover": ["path2file_obs1", "path2file_obs2"],
                         "base": ["path2file_obs_base1", "path2file_obs_base2"],
                         "nav": ["path2file_nav1", "path2file_nav2"],
                         "sp3": ["path2file_sp3_1", "path2file_sp3_2"],
                         "clk": ["path2file_clk_1", "path2file_clk_2"],
                         "erp": ["path2file_erp_1", "path2file_erp_2"]}

            mock_get_start_date_from_obs.side_effect = ["2020-01-01",
                                                        "2020-01-02",
                                                        "2020-01-01",
                                                        "2020-01-02"]  # called 4 times
            mock_get_start_date_from_nav.side_effect = ["2020-01-01", "2020-01-02"]
            rtklibpost._get_start_date_from_sp3.side_effect = ["2020-01-01", "2020-01-02"]
            rtklibpost._get_start_date_from_clk.side_effect = ["2020-01-01", "2020-01-02"]
            rtklibpost._get_dates_from_erp.side_effect = [["2020-01-01", "2020-01-02"]]
            rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'rovers': ['path2file_obs1'],
                              'base': 'path2file_obs_base1',
                              'nav': 'path2file_nav1',
                              'sp3': 'path2file_sp3_1',
                              'clk': 'path2file_clk_1',
                              'erp': 'path2file_erp_1'}, mock_len.call_args_list[0].args[0])
            self.assertEqual({'rovers': ['path2file_obs2'],
                              'base': 'path2file_obs_base2',
                              'nav': 'path2file_nav2',
                              'sp3': 'path2file_sp3_2',
                              'clk': 'path2file_clk_2',
                              'erp': 'path2file_erp_1'}, mock_len.call_args_list[2].args[0])

    def test_start_make_config(self):
        rtklibpost = RtkLibPost(False)
        with (patch("moncenterlib.gnss.postprocessing.mcl_gnss_tools.get_start_date_from_obs") as mock_get_start_date_from_obs,
              patch("moncenterlib.gnss.postprocessing.mcl_gnss_tools.get_start_date_from_nav") as mock_get_start_date_from_nav,
              patch("moncenterlib.gnss.postprocessing.tempfile.NamedTemporaryFile") as mock_temp_file,
              patch("moncenterlib.gnss.postprocessing.open") as mock_open,
              patch("moncenterlib.gnss.postprocessing.os.path.isfile") as mock_isfile):

            rtklibpost._get_start_date_from_sp3 = MagicMock()
            rtklibpost._get_start_date_from_clk = MagicMock()
            rtklibpost._get_dates_from_erp = MagicMock()

            mock_temp_file().__enter__().name = "my_temp_file"
            # mock_open = mock_open().__enter__()

            # check condition if len(path_files) != len(input_rnx):
            # broke sp3 and base, for example
            input_rnx = {"rover": ["path2file_obs1", "path2file_obs2"],
                         "base": ["path2file_obs_base1", "path2file_obs_base2"],
                         "nav": ["path2file_nav1", "path2file_nav2"],
                         "sp3": ["path2file_sp3_1", "path2file_sp3_2"],
                         "clk": ["path2file_clk_1", "path2file_clk_2"],
                         "erp": ["path2file_erp_1", "path2file_erp_2"]}

            mock_get_start_date_from_obs.side_effect = ["2020-01-01",
                                                        "2020-01-02",
                                                        "2020-01-01",
                                                        "2020-01-03"]  # called 4 times
            mock_get_start_date_from_nav.side_effect = ["2020-01-01", "2020-01-02"]
            rtklibpost._get_start_date_from_sp3.side_effect = ["2020-01-01", "2020-01-03"]
            rtklibpost._get_start_date_from_clk.side_effect = ["2020-01-01", "2020-01-02"]
            rtklibpost._get_dates_from_erp.side_effect = [["2020-01-01", "2020-01-02"]]

            res = rtklibpost.start(input_rnx, "/", {"": ""}, show_info_rtklib=False)
            self.assertEqual({'rovers': ['path2file_obs2'],
                              'nav': 'path2file_nav2',
                              'clk': 'path2file_clk_2',
                              'erp': 'path2file_erp_1'}, res["no_match"][0])  # because not found base and sp3 file date 2020-01-02

            self.assertEqual({'base': 'path2file_obs_base2',
                              'sp3': 'path2file_sp3_2'}, res["no_match"][1])  # base and sp3 2020-01-03

            # make config, config is dict
            mock_open.reset_mock()
            input_rnx = {"rover": ["path2file_obs1"],
                         "base": ["path2file_obs_base1"],
                         "nav": ["path2file_nav1"],
                         "sp3": ["path2file_sp3_1"],
                         "clk": ["path2file_clk_1"],
                         "erp": ["path2file_erp_1"]}

            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-01"]
            mock_get_start_date_from_nav.side_effect = ["2020-01-01"]
            rtklibpost._get_start_date_from_sp3.side_effect = ["2020-01-01"]
            rtklibpost._get_start_date_from_clk.side_effect = ["2020-01-01"]
            rtklibpost._get_dates_from_erp.side_effect = [["2020-01-01"]]

            res = rtklibpost.start(input_rnx, "/", {"param1": "value1"}, show_info_rtklib=False)
            self.assertEqual(call('my_temp_file', 'w', encoding='utf-8'), mock_open.mock_calls[0])
            self.assertEqual('().__enter__().write', mock_open.mock_calls[2][0])
            self.assertEqual(('param1=value1\n',), mock_open.mock_calls[2][1])
            self.assertEqual('().__enter__().write', mock_open.mock_calls[3][0])
            self.assertEqual(('file-eopfile=path2file_erp_1\n',), mock_open.mock_calls[3][1])

            # make config, config is str, erp_from_config = True
            mock_open.reset_mock()
            mock_isfile.return_value = True
            mock_open_from_config_temp_file = MagicMock()
            mock_open_from_config_file = MagicMock()

            mock_open.side_effect = [mock_open_from_config_temp_file, mock_open_from_config_file]

            input_rnx = {"rover": ["path2file_obs1"],
                         "base": ["path2file_obs_base1"],
                         "nav": ["path2file_nav1"],
                         "sp3": ["path2file_sp3_1"],
                         "clk": ["path2file_clk_1"],
                         "erp": ["path2file_erp_1"]}

            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-01"]
            mock_get_start_date_from_nav.side_effect = ["2020-01-01"]
            rtklibpost._get_start_date_from_sp3.side_effect = ["2020-01-01"]
            rtklibpost._get_start_date_from_clk.side_effect = ["2020-01-01"]
            rtklibpost._get_dates_from_erp.side_effect = [["2020-01-01"]]

            res = rtklibpost.start(input_rnx, "/", "file_config", show_info_rtklib=False, erp_from_config=True)
            self.assertEqual(call('my_temp_file', 'w', encoding='utf-8'), mock_open.call_args_list[0])
            self.assertEqual(call('file_config', 'r', encoding='utf-8'), mock_open.call_args_list[1])
            self.assertEqual('__enter__().read', mock_open_from_config_file.mock_calls[1][0])
            self.assertEqual('__enter__().write', mock_open_from_config_temp_file.mock_calls[1][0])

            # make config, config is str, erp_from_config = False
            mock_open.reset_mock()
            mock_isfile.return_value = True
            mock_open_from_config_temp_file = MagicMock()
            mock_open_from_config_file = MagicMock()

            mock_open.side_effect = [mock_open_from_config_temp_file, mock_open_from_config_file]
            mock_open_from_config_file.__enter__().readlines.return_value = ["par1=val1", "file-eopfile=", "par2=val2"]

            input_rnx = {"rover": ["path2file_obs1"],
                         "base": ["path2file_obs_base1"],
                         "nav": ["path2file_nav1"],
                         "sp3": ["path2file_sp3_1"],
                         "clk": ["path2file_clk_1"],
                         "erp": ["path2file_erp_1"]}

            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-01"]
            mock_get_start_date_from_nav.side_effect = ["2020-01-01"]
            rtklibpost._get_start_date_from_sp3.side_effect = ["2020-01-01"]
            rtklibpost._get_start_date_from_clk.side_effect = ["2020-01-01"]
            rtklibpost._get_dates_from_erp.side_effect = [["2020-01-01"]]

            res = rtklibpost.start(input_rnx, "/", "file_config", show_info_rtklib=False, erp_from_config=False)

            self.assertEqual(call('my_temp_file', 'w', encoding='utf-8'), mock_open.call_args_list[0])
            self.assertEqual(call('file_config', 'r', encoding='utf-8'), mock_open.call_args_list[1])
            self.assertEqual('__enter__().write', mock_open_from_config_temp_file.mock_calls[1][0])
            self.assertEqual(('par1=val1\n',), mock_open_from_config_temp_file.mock_calls[1][1])
            self.assertEqual('__enter__().write', mock_open_from_config_temp_file.mock_calls[2][0])
            self.assertEqual(('file-eopfile=path2file_erp_1\n',), mock_open_from_config_temp_file.mock_calls[2][1])
            self.assertEqual('__enter__().write', mock_open_from_config_temp_file.mock_calls[3][0])
            self.assertEqual(('par2=val2\n',), mock_open_from_config_temp_file.mock_calls[3][1])
            self.assertEqual('__enter__().readlines', mock_open_from_config_file.mock_calls[2][0])

    def test_start_make_command(self):
        rtklibpost = RtkLibPost(False)
        input_rnx = {"rover": ["path2file_obs1", "path2file_obs2"],
                     "base": ["path2file_obs_base1"],
                     "nav": ["path2file_nav1"],
                     "sp3": ["path2file_sp3_1"],
                     "clk": ["path2file_clk_1"],
                     "erp": ["path2file_erp_1"]}

        with (patch("moncenterlib.gnss.postprocessing.mcl_gnss_tools.get_start_date_from_obs") as mock_get_start_date_from_obs,
              patch("moncenterlib.gnss.postprocessing.mcl_gnss_tools.get_start_date_from_nav") as mock_get_start_date_from_nav,
              patch("moncenterlib.gnss.postprocessing.tempfile.NamedTemporaryFile") as mock_temp_file,
              patch("moncenterlib.gnss.postprocessing.open"),
              patch("moncenterlib.gnss.postprocessing.os.path.isfile"),
              patch("moncenterlib.gnss.postprocessing.subprocess.run") as mock_run_subprocess,
              patch("moncenterlib.gnss.postprocessing.mcl_tools.get_path2bin") as mock_get_path2bin
              ):
            mock_get_path2bin.return_value = "path2bin"
            mock_temp_file().__enter__().name = "config_file"

            rtklibpost._get_start_date_from_sp3 = MagicMock()
            rtklibpost._get_start_date_from_clk = MagicMock()
            rtklibpost._get_dates_from_erp = MagicMock()

            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-01", "2020-01-01"]  # called 2 times
            mock_get_start_date_from_nav.side_effect = ["2020-01-01"]
            rtklibpost._get_start_date_from_sp3.side_effect = ["2020-01-01"]
            rtklibpost._get_start_date_from_clk.side_effect = ["2020-01-01"]
            rtklibpost._get_dates_from_erp.side_effect = [["2020-01-01", "2020-01-02"]]

            res = rtklibpost.start(input_rnx,
                                   "/",
                                   {"": ""},
                                   erp_from_config=False,
                                   timeint=5,
                                   show_info_rtklib=False,
                                   )

            # check several rover files
            self.assertEqual(['path2bin',
                              '-ti', '5',
                              '-k', 'config_file',
                              'path2file_obs1',
                              'path2file_obs_base1',
                              'path2file_nav1',
                              'path2file_sp3_1',
                              'path2file_clk_1',
                              '-o', '/path2file_obs1.pos'], mock_run_subprocess.mock_calls[0].args[0])
            self.assertEqual({'check': False, 'stdout': -3, 'stderr': -3}, mock_run_subprocess.mock_calls[0].kwargs)
            self.assertEqual(['path2bin',
                              '-ti', '5',
                              '-k', 'config_file',
                              'path2file_obs2',
                              'path2file_obs_base1',
                              'path2file_nav1',
                              'path2file_sp3_1',
                              'path2file_clk_1',
                              '-o', '/path2file_obs2.pos'], mock_run_subprocess.mock_calls[1].args[0])
            self.assertEqual({'check': False, 'stdout': -3, 'stderr': -3}, mock_run_subprocess.mock_calls[1].kwargs)
            self.assertEqual({"done": [],
                              "no_exists": ['/path2file_obs1.pos', "/path2file_obs2.pos"],
                              "no_match": [{"erp": "path2file_erp_1"}]}, res)

            # check flag show_info_rtklib
            mock_run_subprocess.reset_mock()
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-01", "2020-01-01"]  # called 2 times
            mock_get_start_date_from_nav.side_effect = ["2020-01-01"]
            rtklibpost._get_start_date_from_sp3.side_effect = ["2020-01-01"]
            rtklibpost._get_start_date_from_clk.side_effect = ["2020-01-01"]
            rtklibpost._get_dates_from_erp.side_effect = [["2020-01-01", "2020-01-02"]]

            res = rtklibpost.start(input_rnx,
                                   "/",
                                   {"": ""},
                                   erp_from_config=False,
                                   timeint=5,
                                   show_info_rtklib=True,
                                   )
            self.assertEqual({'check': False, 'stdout': -3}, mock_run_subprocess.mock_calls[0].kwargs)

    def test_start_output(self):
        pass


if __name__ == '__main__':
    main()
