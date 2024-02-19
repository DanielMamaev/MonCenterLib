from io import TextIOWrapper, BytesIO
from logging import Logger
import logging
import tempfile
from unittest import TestCase, main
from unittest.mock import MagicMock, patch, call
from moncenterlib.gnss.quality_check import Anubis


class TestAnubis(TestCase):
    def setUp(self) -> None:
        self.anubis = Anubis(False)

    def test_init_raises(self):
        with self.assertRaises(Exception):
            anubis = Anubis("None")

    def test_init_with_enable_logger(self):
        anubis = Anubis()
        self.assertEqual(Logger, type(anubis.logger))
        self.assertEqual("Anubis", anubis.logger.name)

    def test_init_with_disable_logger(self):
        anubis = Anubis(False)
        self.assertEqual(Logger, type(anubis.logger))
        self.assertEqual("Anubis", anubis.logger.name)

    def test_init_with_my_logger(self):
        logger = logging.getLogger()
        anubis = Anubis(logger=logger)
        self.assertEqual(logger, anubis.logger)
        self.assertEqual("root", anubis.logger.name)

    def test_init_check_dublicate_handlers(self):
        anubis = Anubis()
        anubis = Anubis()
        self.assertEqual(1, len(anubis.logger.handlers))

    def test_scan_dirs_raises(self):
        with self.assertRaises(Exception):
            self.anubis.scan_dirs(None, None, None)

        with self.assertRaises(ValueError) as msg:
            self.anubis.scan_dirs("/some path", "/")
        self.assertEqual(str(msg.exception), "Please, remove spaces in path.")

        with self.assertRaises(ValueError) as msg:
            self.anubis.scan_dirs("/", "/some path")
        self.assertEqual(str(msg.exception), "Please, remove spaces in path.")

    def test_scan_dirs(self):
        with (patch("moncenterlib.gnss.quality_check.mcl_tools.get_files_from_dir") as mock_get_files_from_dir,
              patch("moncenterlib.gnss.quality_check.mcl_tools.get_start_date_from_nav") as mock_get_start_date_from_nav,
              patch("moncenterlib.gnss.quality_check.mcl_tools.get_start_date_from_obs") as mock_get_start_date_from_obs,
              patch("moncenterlib.gnss.quality_check.mcl_tools.get_marker_name") as mock_get_marker_name):

            # check send arg to get_files_from_dir
            mock_get_files_from_dir.return_value = []

            self.anubis.scan_dirs("/obs", "/nav")
            self.assertEqual([call('/obs', False), call('/nav', False)], mock_get_files_from_dir.call_args_list)

            mock_get_files_from_dir.reset_mock()
            self.anubis.scan_dirs("/obs", "/nav", True)
            self.assertEqual([call('/obs', True), call('/nav', True)], mock_get_files_from_dir.call_args_list)

            # check send arg to get_start_date_from_nav, get_start_date_from_obs
            mock_get_files_from_dir.side_effect = [["obs1", "obs2"], ["nav1", "nav2"]]
            self.anubis.scan_dirs("/obs", "/nav")
            self.assertEqual([call("nav1"), call("nav2")], mock_get_start_date_from_nav.call_args_list)
            self.assertEqual([call("obs1"), call("obs2")], mock_get_start_date_from_obs.call_args_list)

            # no found nav, found obs
            mock_get_files_from_dir.side_effect = [["obs1", "obs2"], ["nav1", "nav2"]]
            mock_get_start_date_from_nav.side_effect = []
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-02"]
            mock_get_marker_name.return_value = "AAAA"
            result = self.anubis.scan_dirs("/obs", "/nav")
            self.assertEqual({}, result)

            # no found obs, found nav
            mock_get_files_from_dir.side_effect = [["obs1", "obs2"], ["nav1", "nav2"]]
            mock_get_start_date_from_nav.side_effect = ["2020-01-01", "2020-01-02"]
            mock_get_start_date_from_obs.side_effect = []
            mock_get_marker_name.return_value = "AAAA"
            result = self.anubis.scan_dirs("/obs", "/nav")
            self.assertEqual({}, result)

            # check continue in nav
            mock_get_files_from_dir.side_effect = [["obs1", "obs2", "obs3"], ["nav1", "nav2", "nav3"]]
            mock_get_start_date_from_nav.side_effect = ["2020-01-01", Exception(), "2020-01-03"]
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-02", "2020-01-03"]
            mock_get_marker_name.return_value = "AAAA"
            result = self.anubis.scan_dirs("/obs", "/nav")
            self.assertEqual({"AAAA": [['obs1', 'nav1'], ['obs3', 'nav3']]}, result)

            # check continue in obs date
            mock_get_files_from_dir.side_effect = [["obs1", "obs2", "obs3"], ["nav1", "nav2", "nav3"]]
            mock_get_start_date_from_nav.side_effect = ["2020-01-01", "2020-01-02", "2020-01-03"]
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", Exception(), "2020-01-03"]
            mock_get_marker_name.return_value = "AAAA"
            result = self.anubis.scan_dirs("/obs", "/nav")
            self.assertEqual({"AAAA": [['obs1', 'nav1'], ['obs3', 'nav3']]}, result)

            # check continue in obs marker name
            mock_get_files_from_dir.side_effect = [["obs1", "obs2", "obs3"], ["nav1", "nav2", "nav3"]]
            mock_get_start_date_from_nav.side_effect = ["2020-01-01", "2020-01-02", "2020-01-03"]
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-02", "2020-01-03"]
            mock_get_marker_name.side_effect = ["AAAA", Exception(), "CCCC"]
            result = self.anubis.scan_dirs("/obs", "/nav")
            self.assertEqual({"AAAA": [['obs1', 'nav1']], "CCCC": [['obs3', 'nav3']]}, result)

            # check if date_obs is not existing in filter_files_nav
            mock_get_files_from_dir.side_effect = [["obs1", "obs2", "obs3"], ["nav1", "nav2", "nav3"]]
            mock_get_start_date_from_nav.side_effect = ["2020-01-01", "2020-01-02", "2020-01-03"]
            mock_get_start_date_from_obs.side_effect = ["2020-01-01", "2020-01-02", "2020-01-05"]
            mock_get_marker_name.side_effect = None
            mock_get_marker_name.return_value = "AAAA"
            result = self.anubis.scan_dirs("/obs", "/nav")
            self.assertEqual({'AAAA': [['obs1', 'nav1'], ['obs2', 'nav2']]}, result)

    def test_start_raises(self):
        with self.assertRaises(Exception):
            self.anubis.start(None, False, "")

        with self.assertRaises(Exception):
            self.anubis.start({}, None, "")

        with self.assertRaises(Exception):
            self.anubis.start({}, False, 1)

        with (patch("moncenterlib.gnss.quality_check.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.quality_check.os.path.isdir") as mock_isdir):
            # check is file
            mock_isfile.return_value = True
            with self.assertRaises(ValueError) as msg:
                self.anubis.start(("/nav 1.txt", "nav2.txt"), False)
            self.assertEqual(str(msg.exception), "Please, remove spaces in path.")

            with self.assertRaises(ValueError) as msg:
                self.anubis.start(("/nav1.txt", "/nav 2.txt"), False)
            self.assertEqual(str(msg.exception), "Please, remove spaces in path.")

            # check is dir
            mock_isfile.return_value = False
            mock_isdir.return_value = False
            with self.assertRaises(ValueError) as msg:
                self.anubis.start(("/obs", "/nav"), False)
            self.assertEqual(str(msg.exception), "Path to file or dir is strange.")

    def test_start_different_input_data(self):
        with (patch("moncenterlib.gnss.quality_check.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.quality_check.os.path.isdir") as mock_isdir,
              patch("moncenterlib.gnss.quality_check.mcl_tools.get_path2bin") as mock_get_path2bin,
              patch("moncenterlib.gnss.quality_check.subprocess.run")):
            mock_create_config = MagicMock()
            mock_parsing_xtr = MagicMock()
            anubis = Anubis(False)
            anubis._create_config = mock_create_config
            anubis._parsing_xtr = mock_parsing_xtr
            mock_get_path2bin.return_value = "anubis_bin"

            # check dict
            mock_parsing_xtr.side_effect = [{"date": "1"},
                                            {"date": "1"},
                                            {"date": "1"},
                                            {"date": "1"}]
            input_data = {
                "station1": [["obs1", "nav1"], ["obs2", "nav2"]],
                "station2": [["obs3", "nav3"], ["obs4", "nav4"]],
            }

            anubis.start(input_data)
            self.assertEqual([["obs1", "nav1"],
                              ["obs2", "nav2"],
                              ["obs3", "nav3"],
                              ["obs4", "nav4"]], [mock_create_config.call_args_list[0].args[0],
                                                  mock_create_config.call_args_list[1].args[0],
                                                  mock_create_config.call_args_list[2].args[0],
                                                  mock_create_config.call_args_list[3].args[0]])

            # check tuple one file
            mock_create_config.reset_mock()
            mock_isfile.return_value = True
            mock_parsing_xtr.side_effect = [{"date": "1"}]
            input_data = ("obs.txt", "nav.txt")
            anubis.start(input_data)
            self.assertEqual(["obs.txt", "nav.txt"], mock_create_config.call_args_list[0].args[0])

            # check tuple dir
            mock_create_config.reset_mock()
            mock_isfile.return_value = False
            mock_isdir.return_value = True
            mock_parsing_xtr.side_effect = [{"date": "None"},
                                            {"date": "None"},
                                            {"date": "None"},
                                            {"date": "None"}]
            mock_scan_dirs = MagicMock()
            mock_scan_dirs.return_value = {
                "station1": [["obs1", "nav1"], ["obs2", "nav2"]],
                "station2": [["obs3", "nav3"], ["obs4", "nav4"]],
            }
            anubis.scan_dirs = mock_scan_dirs
            anubis.start(("/obs", "/nav"))
            self.assertEqual([["obs1", "nav1"],
                              ["obs2", "nav2"],
                              ["obs3", "nav3"],
                              ["obs4", "nav4"]], [mock_create_config.call_args_list[0].args[0],
                                                  mock_create_config.call_args_list[1].args[0],
                                                  mock_create_config.call_args_list[2].args[0],
                                                  mock_create_config.call_args_list[3].args[0]])

    def test_start_check_recursion(self):
        with (patch("moncenterlib.gnss.quality_check.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.quality_check.os.path.isdir") as mock_isdir,
              patch("moncenterlib.gnss.quality_check.mcl_tools.get_path2bin") as mock_get_path2bin,
              patch("moncenterlib.gnss.quality_check.subprocess.run")):
            mock_get_path2bin.side_effect = Exception()
            mock_scan_dirs = MagicMock()
            anubis = Anubis(False)
            anubis.scan_dirs = mock_scan_dirs

            mock_isfile.return_value = False
            mock_isdir.return_value = True
            anubis.start(("/obs", "/nav"))
            self.assertEqual([call('/obs', '/nav', False)], mock_scan_dirs.call_args_list)

            mock_scan_dirs.reset_mock()
            anubis.start(("/obs", "/nav"), True)
            self.assertEqual([call('/obs', '/nav', True)], mock_scan_dirs.call_args_list)

    def test_start_check_output_dir_xtr(self):
        with (patch("moncenterlib.gnss.quality_check.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.quality_check.os.path.isdir") as mock_isdir,
              patch("moncenterlib.gnss.quality_check.mcl_tools.get_path2bin"),
              patch("moncenterlib.gnss.quality_check.subprocess.run") as mock_subprocess):
            mock_scan_dirs = MagicMock()
            anubis = Anubis(False)
            anubis.scan_dirs = mock_scan_dirs
            mock_scan_dirs.return_value = {
                "station1": [["obs1", "nav1"], ["obs2", "nav2"]],
                "station2": [["obs3", "nav3"], ["obs4", "nav4"]],
            }

            mock_create_config = MagicMock()
            anubis._create_config = mock_create_config

            mock_subprocess.side_effect = [True, Exception()]
            mock_isfile.return_value = False
            mock_isdir.return_value = True

            with self.assertRaises(Exception):
                anubis.start(("/obs", "/nav"), False, "/some_path")

            self.assertEqual('/some_path', mock_create_config.call_args_list[0].args[2])

    def test_start_check_subprocces(self):
        with (patch("moncenterlib.gnss.quality_check.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.quality_check.os.path.isdir") as mock_isdir,
              patch("moncenterlib.gnss.quality_check.mcl_tools.get_path2bin") as mock_get_path2bin,
              patch("moncenterlib.gnss.quality_check.subprocess.run") as mock_subprocess,
              patch("moncenterlib.gnss.quality_check.tempfile.NamedTemporaryFile") as mock_temp_file):
            mock_return_name_temp_file = MagicMock()
            mock_return_name_temp_file.name = "/temp_file"
            mock_temp_file.return_value.__enter__.return_value = mock_return_name_temp_file

            anubis = Anubis(False)
            mock_scan_dirs = MagicMock()
            anubis.scan_dirs = mock_scan_dirs
            mock_scan_dirs.return_value = {
                "station1": [["obs1", "nav1"], ["obs2", "nav2"]],
                "station2": [["obs3", "nav3"], ["obs4", "nav4"]],
            }

            mock_parsing_xtr = MagicMock()
            mock_parsing_xtr.side_effect = [True, Exception()]

            mock_create_config = MagicMock()
            anubis._create_config = mock_create_config

            mock_get_path2bin.return_value = "/anubis_bin"

            mock_isfile.return_value = False
            mock_isdir.return_value = True

            with self.assertRaises(Exception):
                anubis.start(("/obs", "/nav"), False, "/some_path")

            self.assertEqual((['/anubis_bin', '-x', '/temp_file'], ), mock_subprocess.call_args_list[0].args)
            self.assertEqual({'stderr': -3, 'check': False}, mock_subprocess.call_args_list[0].kwargs)

    def test_start_check_parsing_xtr(self):
        with (patch("moncenterlib.gnss.quality_check.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.quality_check.os.path.isdir") as mock_isdir,
              patch("moncenterlib.gnss.quality_check.mcl_tools.get_path2bin"),
              patch("moncenterlib.gnss.quality_check.subprocess.run"),
              patch("moncenterlib.gnss.quality_check.tempfile.NamedTemporaryFile") as mock_temp_file):

            mock_return_name_temp_file = MagicMock()
            mock_return_name_temp_file.name = "/temp_file"
            mock_temp_file.return_value.__enter__.return_value = mock_return_name_temp_file

            mock_isfile.return_value = False
            mock_isdir.return_value = True

            anubis = Anubis(False)

            mock_scan_dirs = MagicMock()
            anubis.scan_dirs = mock_scan_dirs
            mock_scan_dirs.return_value = {
                "station1": [["/obs1", "/nav1"], ["/obs2", "/nav2"]],
                "station2": [["/obs3", "/nav3"], ["/obs4", "/nav4"]],
            }
            mock_parsing_xtr = MagicMock()
            anubis._parsing_xtr = mock_parsing_xtr
            anubis._create_config = MagicMock()

            # with output output_dir_xtr
            anubis.start(("/obs", "/nav"), False, "/some_path")

            self.assertEqual([call('/some_path/obs1.xtr'),
                              call('/some_path/obs2.xtr'),
                              call('/some_path/obs3.xtr'),
                              call('/some_path/obs4.xtr')], mock_parsing_xtr.call_args_list)

            # without output output_dir_xtr
            mock_parsing_xtr.reset_mock()
            anubis.start(("/obs", "/nav"), False)
            self.assertEqual([call('/obs1.xtr'),
                              call('/obs2.xtr'),
                              call('/obs3.xtr'),
                              call('/obs4.xtr')], mock_parsing_xtr.call_args_list)

    def test_start_missing_file(self):
        with (patch("moncenterlib.gnss.quality_check.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.quality_check.os.path.isdir") as mock_isdir,
              patch("moncenterlib.gnss.quality_check.mcl_tools.get_path2bin"),
              patch("moncenterlib.gnss.quality_check.subprocess.run"),
              patch("moncenterlib.gnss.quality_check.tempfile.NamedTemporaryFile") as mock_temp_file):

            mock_return_name_temp_file = MagicMock()
            mock_return_name_temp_file.name = "/temp_file"
            mock_temp_file.return_value.__enter__.return_value = mock_return_name_temp_file

            mock_isfile.return_value = False
            mock_isdir.return_value = True

            anubis = Anubis(False)

            mock_scan_dirs = MagicMock()
            anubis.scan_dirs = mock_scan_dirs
            mock_scan_dirs.return_value = {
                "station1": [["/obs1"], ["/obs2", "/nav2"]],
                "station2": [["/obs3", "/nav3"], ["/obs4"]],
            }
            mock_parsing_xtr = MagicMock()
            anubis._parsing_xtr = mock_parsing_xtr
            anubis._create_config = MagicMock()

            anubis.start(("/obs", "/nav"), False, "/some_path")

            self.assertEqual([call('/some_path/obs2.xtr'),
                              call('/some_path/obs3.xtr')], mock_parsing_xtr.call_args_list)

    def test_start_output(self):
        with (patch("moncenterlib.gnss.quality_check.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.quality_check.os.path.isdir") as mock_isdir,
              patch("moncenterlib.gnss.quality_check.mcl_tools.get_path2bin"),
              patch("moncenterlib.gnss.quality_check.subprocess.run"),
              patch("moncenterlib.gnss.quality_check.tempfile.NamedTemporaryFile") as mock_temp_file):

            mock_return_name_temp_file = MagicMock()
            mock_return_name_temp_file.name = "/temp_file"
            mock_temp_file.return_value.__enter__.return_value = mock_return_name_temp_file

            mock_isfile.return_value = False
            mock_isdir.return_value = True

            anubis = Anubis(False)

            mock_scan_dirs = MagicMock()
            anubis.scan_dirs = mock_scan_dirs
            mock_scan_dirs.return_value = {
                "station1": [["/obs1", "/nav1"], ["/obs2", "/nav2"]],
                "station2": [["/obs3", "/nav3"], ["/obs4", "/nav4"]],
            }
            mock_parsing_xtr = MagicMock()
            mock_parsing_xtr.side_effect = [{"date": "1", "metric1": 1, "metric2": 2},
                                            {"date": "2", "metric3": 3, "metric4": 4},
                                            {"date": "3", "metric5": 5, "metric6": 6},
                                            {"date": "4", "metric7": 7, "metric8": 8}]
            anubis._parsing_xtr = mock_parsing_xtr
            anubis._create_config = MagicMock()

            result = anubis.start(("/obs", "/nav"), False, "/some_path")
            self.assertEqual({"station1": {"1": {"date": "1", "metric1": 1, "metric2": 2},
                                           "2": {"date": "2", "metric3": 3, "metric4": 4}},
                              "station2": {"3": {"date": "3", "metric5": 5, "metric6": 6},
                                           "4": {"date": "4", "metric7": 7, "metric8": 8}}}, result)

    def test__create_config(self):
        # without output_files_xtr
        with tempfile.NamedTemporaryFile() as temp_file:
            self.anubis._create_config(["/obs1", "/nav1"], temp_file.name, None)
            exp = '<config><qc sec_sum="1" sec_hdr="0" sec_obs="1" sec_gap="1" sec_bnd="1" sec_pre="1" sec_mpx="1" sec_snr="1" sec_est="0" sec_ele="0" sec_sat="0" /><inputs><rinexo>/obs1</rinexo><rinexn>/nav1</rinexn></inputs><outputs><xtr>/obs1.xtr</xtr></outputs></config>'
            with open(temp_file.name, "r", encoding="utf-8") as f:
                self.assertEqual(exp, f.read())

        # with output_files_xtr
        with (tempfile.NamedTemporaryFile() as temp_file,
              tempfile.TemporaryDirectory() as temp_dir):
            self.anubis._create_config(["/obs1", "/nav1"], temp_file.name, temp_dir)
            exp = f'<config><qc sec_sum="1" sec_hdr="0" sec_obs="1" sec_gap="1" sec_bnd="1" sec_pre="1" sec_mpx="1" sec_snr="1" sec_est="0" sec_ele="0" sec_sat="0" /><inputs><rinexo>/obs1</rinexo><rinexn>/nav1</rinexn></inputs><outputs><xtr>{temp_dir}/obs1.xtr</xtr></outputs></config>'
            with open(temp_file.name, "r", encoding="utf-8") as f:
                self.assertEqual(exp, f.read())

    def test__parsing_xtr_raises(self):
        with self.assertRaises(Exception):
            self.anubis._parsing_xtr(None)

    def test__parsing_xtr_read_file(self):
        with patch("moncenterlib.gnss.quality_check.open") as mock_open:
            self.anubis._parsing_xtr("/some_path")

            self.assertEqual(("/some_path", 'r'), mock_open.call_args_list[0].args)
            self.assertEqual({"encoding": "utf-8"}, mock_open.call_args_list[0].kwargs)

            # Exeption
            mock_open.side_effect = Exception()
            res = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(res)

    def test__parsing_xtr_TOTSUM(self):
        data = ['# G-Nut/Anubis [2.3] compiled: Dec 21 2023 18:34:14 ($Rev: 2843 $)\n',
                '\n',
                '#====== Summary statistics (v.1)\n',
                '#TOTSUM First_Epoch________ Last_Epoch_________ Hours_ Sample MinEle #_Expt #_Have %Ratio o/slps woElev Exp>10 Hav>10 %Rt>10\n',
                '=TOTSUM 2022-01-08 00:00:00 2022-01-08 23:59:30  24.00  30.00   4.82  45706  41328  90.42    155  13730  36283  36000  99.22\n',
                '\n']

        with patch("moncenterlib.gnss.quality_check.open") as mock_open:
            mock_readlines = MagicMock()
            mock_readlines.return_value = data
            mock_open.return_value.__enter__.return_value.readlines = mock_readlines
            result = self.anubis._parsing_xtr("/some_path")

            self.assertEqual({"date": "2022-01-08 00:00:00",
                              "total_time": 24.00,
                              "expt_obs": 45706,
                              "exis_obs": 41328,
                              "ratio": 90.42,
                              "expt_obs10": 36283,
                              "exis_obs10": 36000,
                              "ratio10": 99.22}, result)

            data[4] = '=TOTSUM 2022-01-08 00:00:00 2022-01-08 23:59:30  -  30.00   4.82  45706  41328  90.42    155  13730  36283  36000  99.22\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

            data[4] = '=TOTSUM 2022-01-08 00:00:00 2022-01-08 23:59:30  24.00  30.00   4.82  -  41328  90.42    155  13730  36283  36000  99.22\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

            data[4] = '=TOTSUM 2022-01-08 00:00:00 2022-01-08 23:59:30  24.00  30.00   4.82  45706  -  90.42    155  13730  36283  36000  99.22\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

            data[4] = '=TOTSUM 2022-01-08 00:00:00 2022-01-08 23:59:30  24.00  30.00   4.82  45706  41328  -    155  13730  36283  36000  99.22\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

            data[4] = '=TOTSUM 2022-01-08 00:00:00 2022-01-08 23:59:30  24.00  30.00   4.82  45706  41328  90.42    155  13730  -  36000  99.22\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

            data[4] = '=TOTSUM 2022-01-08 00:00:00 2022-01-08 23:59:30  24.00  30.00   4.82  45706  41328  90.42    155  13730  36283  -  99.22\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

            data[4] = '=TOTSUM 2022-01-08 00:00:00 2022-01-08 23:59:30  24.00  30.00   4.82  45706  41328  90.42    155  13730  36283  36000  -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

    def test__parsing_xtr_GNSSUM(self):
        data = ['# G-Nut/Anubis [2.3] compiled: Dec 21 2023 18:34:14 ($Rev: 2843 $)\n',
                '\n',
                '#====== Summary statistics (v.1)\n',
                '#GNSSUM 2022-01-08 00:00:00 Epoch_Statistics_ Excl_Epochs&Satellites_  CycleSlips/Interruptions_And_Other_Discontinuities Code_Multipath_Mean_Statistics_Over_All_Signals\n',
                '#GNSSUM 2022-01-08 00:00:00 ExpEp HavEp UseEp xCoEp xPhEp xCoSv xPhSv  csAll  csEpo  csSat  csSig  nSlp  nJmp  nGap  nPcs   mp1   mp2   mp3   mpx   mp5   mp6   mp7   mp8\n',
                '=GPSSUM 2022-01-08 00:00:00  2880  2880  2880     0     0   106   106    855      5    242     83   530     0     0     0  50.0  35.2     -     -     -     -     -     -\n',
                '=GLOSUM 2022-01-08 00:00:00  2880  2880  2336   544   544  4420  4422    966      0    240    726     0     0     0     0     -     -     -     -     -     -     -     -\n',
                '\n']

        with patch("moncenterlib.gnss.quality_check.open") as mock_open:
            mock_readlines = MagicMock()
            mock_readlines.return_value = data
            mock_open.return_value.__enter__.return_value.readlines = mock_readlines
            result = self.anubis._parsing_xtr("/some_path")

            self.assertEqual({"miss_epoch": {'GPS': 5, 'GLO': 0},
                              "code_multi": {'GPSMP1': 50.0, 'GPSMP2': 35.2, 'GLOMP1': '-', 'GLOMP2': '-'},
                              "n_slip": {'GPS': 530, 'GLO': 0}},
                             result)
            # GPS
            data[5] = '=GPSSUM 2022-01-08 00:00:00  2880  2880  2880     0     0   106   106    855      -    242     83   530     0     0     0  50.0  35.2     -     -     -     -     -     -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

            data[5] = '=GPSSUM 2022-01-08 00:00:00  2880  2880  2880     0     0   106   106    855      5    242     83   -     0     0     0  50.0  35.2     -     -     -     -     -     -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

            data[5] = '=GPSSUM 2022-01-08 00:00:00  2880  2880  2880     0     0   106   106    855      5    242     83   530     0     0     0  -  35.2     -     -     -     -     -     -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertEqual({"miss_epoch": {'GPS': 5, 'GLO': 0},
                              "code_multi": {'GPSMP1': "-", 'GPSMP2': 35.2, 'GLOMP1': '-', 'GLOMP2': '-'},
                              "n_slip": {'GPS': 530, 'GLO': 0}},
                             result)

            data[5] = '=GPSSUM 2022-01-08 00:00:00  2880  2880  2880     0     0   106   106    855      5    242     83   530     0     0     0  50.0  -     -     -     -     -     -     -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertEqual({"miss_epoch": {'GPS': 5, 'GLO': 0},
                              "code_multi": {'GPSMP1': 50.0, 'GPSMP2': "-", 'GLOMP1': '-', 'GLOMP2': '-'},
                              "n_slip": {'GPS': 530, 'GLO': 0}},
                             result)

            # GLO
            data[6] = '=GLOSUM 2022-01-08 00:00:00  2880  2880  2336   544   544  4420  4422    966      -    240    726     0     0     0     0     -     -     -     -     -     -     -     -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

            data[6] = '=GLOSUM 2022-01-08 00:00:00  2880  2880  2336   544   544  4420  4422    966      0    240    726     -     0     0     0     -     -     -     -     -     -     -     -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

            data[6] = '=GLOSUM 2022-01-08 00:00:00  2880  2880  2336   544   544  4420  4422    966      0    240    726     0     0     0     0     5     -     -     -     -     -     -     -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertEqual({"miss_epoch": {'GPS': 5, 'GLO': 0},
                              "code_multi": {'GPSMP1': 50.0, 'GPSMP2': "-", 'GLOMP1': 5.0, 'GLOMP2': '-'},
                              "n_slip": {'GPS': 530, 'GLO': 0}},
                             result)

            data[6] = '=GLOSUM 2022-01-08 00:00:00  2880  2880  2336   544   544  4420  4422    966      0    240    726     0     0     0     0     -     5     -     -     -     -     -     -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertEqual({"miss_epoch": {'GPS': 5, 'GLO': 0},
                              "code_multi": {'GPSMP1': 50.0, 'GPSMP2': "-", 'GLOMP1': '-', 'GLOMP2': 5.0},
                              "n_slip": {'GPS': 530, 'GLO': 0}},
                             result)

    # def test__parsing_xtr_GNSSUM(self):
    #     self.anubis._parsing_xtr("/home/danisimo/MonCenter_Project/test_script/xtr/novm0080.22o.xtr")

    def test__parsing_xtr_GNSSYS(self):
        data = ['# G-Nut/Anubis [2.3] compiled: Dec 21 2023 18:34:14 ($Rev: 2843 $)\n',
                '\n',
                '#====== Observation types (v.1)\n',
                '=GNSSYS 2022-01-08 00:00:00       2 GPS GLO\n',
                '\n',
                '=GPSSAT 2022-01-08 00:00:00      29 G01 G02 G03 G04 G05 G06 G07 G08 G09 G10   - G12 G13 G14 G15 G16 G17 G18 G19 G20 G21   - G23 G24 G25 G26 G27   - G29 G30 G31 G32   -   -   -   -\n',
                '=GLOSAT 2022-01-08 00:00:00      17 R01 R02 R03 R04 R05   - R07 R08 R09   -   - R12 R13 R14 R15   - R17 R18   -   - R21 R22   - R24   -   -   -   -   -   -   -   -   -   -   -   -\n',
                '\n']

        with patch("moncenterlib.gnss.quality_check.open") as mock_open:
            mock_readlines = MagicMock()
            mock_readlines.return_value = data
            mock_open.return_value.__enter__.return_value.readlines = mock_readlines

            result = self.anubis._parsing_xtr("/some_path")

            self.assertEqual({"sat_healthy": {'GPS': 29, 'GLO': 17}}, result)

            data[5] = '=GLOSAT 2022-01-08 00:00:00      - R01 R02 R03 R04 R05   - R07 R08 R09   -   - R12 R13 R14 R15   - R17 R18   -   - R21 R22   - R24   -   -   -   -   -   -   -   -   -   -   -   -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

            data[5] = '=GPSSAT 2022-01-08 00:00:00      - G01 G02 G03 G04 G05 G06 G07 G08 G09 G10   - G12 G13 G14 G15 G16 G17 G18 G19 G20 G21   - G23 G24 G25 G26 G27   - G29 G30 G31 G32   -   -   -   -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertIsNone(result)

    def test__parsing_xtr_GNSSxx(self):
        data = ['# G-Nut/Anubis [2.3] compiled: Dec 21 2023 18:34:14 ($Rev: 2843 $)\n',
                '\n',
                '#====== Signal to noise ratio (v.1)\n',
                '#GNSSxx 2022-01-08 00:00:00    mean x01 x02 x03 x04 x05 x06 x07 x08 x09 x10 x11 x12 x13 x14 x15 x16 x17 x18 x19 x20 x21 x22 x23 x24 x25 x26 x27 x28 x29 x30 x31 x32 x33 x34 x35 x36\n',
                '=GPSSS1 2022-01-08 00:00:00   30.99  34  28  33  25  32  34  35  33  33  38   -  32  22  27  33  22  35  27  29  23  23   -  28  33  34  33  33   -  34  34  33  39   -   -   -   -\n',
                '=GPSSS2 2022-01-08 00:00:00   31.14  34  28  33  25  32  34  35  33  34  39   -  32  22  27  33  22  36  27  29  23  23   -  27  33  35  33  34   -  34  34  33  39   -   -   -   -\n',
                '=GLOSS1 2022-01-08 00:00:00   37.85  36  41  38  38  39   -  38  38  39   -   -  40  31  42  39   -  38  40   -   -  38  30   -  39   -   -   -   -   -   -   -   -   -   -   -   -\n',
                '=GLOSS2 2022-01-08 00:00:00   36.10  36  26  39  40  40   -  41  39  37   -   -  29  38  40  21   -  40  40   -   -  39  28   -  40   -   -   -   -   -   -   -   -   -   -   -   -\n']

        with patch("moncenterlib.gnss.quality_check.open") as mock_open:
            mock_readlines = MagicMock()
            mock_readlines.return_value = data
            mock_open.return_value.__enter__.return_value.readlines = mock_readlines

            result = self.anubis._parsing_xtr("/some_path")

            self.assertEqual({"sig2noise": {'GPSSS1': 30.99, 'GPSSS2': 31.14,
                             "GLOSS1": 37.85, "GLOSS2": 36.10}}, result)

            data[4] = '=GPSSS1 2022-01-08 00:00:00   -  34  28  33  25  32  34  35  33  33  38   -  32  22  27  33  22  35  27  29  23  23   -  28  33  34  33  33   -  34  34  33  39   -   -   -   -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertEqual({"sig2noise": {'GPSSS2': 31.14,
                             "GLOSS1": 37.85, "GLOSS2": 36.10}}, result)

            data[5] = '=GPSSS2 2022-01-08 00:00:00   -  34  28  33  25  32  34  35  33  34  39   -  32  22  27  33  22  36  27  29  23  23   -  27  33  35  33  34   -  34  34  33  39   -   -   -   -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertEqual({"sig2noise": {"GLOSS1": 37.85, "GLOSS2": 36.10}}, result)

            data[7] = '=GLOSS2 2022-01-08 00:00:00   -  36  26  39  40  40   -  41  39  37   -   -  29  38  40  21   -  40  40   -   -  39  28   -  40   -   -   -   -   -   -   -   -   -   -   -   -\n'
            result = self.anubis._parsing_xtr("/some_path")
            self.assertEqual({"sig2noise": {"GLOSS1": 37.85}}, result)

    def test__parsing_xtr_output(self):
        text = """# G-Nut/Anubis [2.3] compiled: Dec 21 2023 18:34:14 ($Rev: 2843 $)

#====== Summary statistics (v.1)
#TOTSUM First_Epoch________ Last_Epoch_________ Hours_ Sample MinEle #_Expt #_Have %Ratio o/slps woElev Exp>10 Hav>10 %Rt>10
=TOTSUM 2022-01-08 00:00:00 2022-01-08 23:59:30  24.00  30.00   4.82  45706  41328  90.42    155  13730  36283  36000  99.22

#GNSSUM 2022-01-08 00:00:00 Epoch_Statistics_ Excl_Epochs&Satellites_  CycleSlips/Interruptions_And_Other_Discontinuities Code_Multipath_Mean_Statistics_Over_All_Signals
#GNSSUM 2022-01-08 00:00:00 ExpEp HavEp UseEp xCoEp xPhEp xCoSv xPhSv  csAll  csEpo  csSat  csSig  nSlp  nJmp  nGap  nPcs   mp1   mp2   mp3   mpx   mp5   mp6   mp7   mp8
=GPSSUM 2022-01-08 00:00:00  2880  2880  2880     0     0   106   106    855      0    242     83   530     0     0     0  50.0  35.2     -     -     -     -     -     -
=GLOSUM 2022-01-08 00:00:00  2880  2880  2336   544   544  4420  4422    966      0    240    726     0     0     0     0     -     -     -     -     -     -     -     -

#====== Observation types (v.1)
=GNSSYS 2022-01-08 00:00:00       2 GPS GLO

=GPSSAT 2022-01-08 00:00:00      29 G01 G02 G03 G04 G05 G06 G07 G08 G09 G10   - G12 G13 G14 G15 G16 G17 G18 G19 G20 G21   - G23 G24 G25 G26 G27   - G29 G30 G31 G32   -   -   -   -
=GLOSAT 2022-01-08 00:00:00      17 R01 R02 R03 R04 R05   - R07 R08 R09   -   - R12 R13 R14 R15   - R17 R18   -   - R21 R22   - R24   -   -   -   -   -   -   -   -   -   -   -   -

=GNSHDR 2022-01-08 00:00:00       9 C1  P1  L1  D1  S1  P2  L2  D2  S2 
=GPSOBS 2022-01-08 00:00:00       9 P1  P2  C1  L1  L2  D1  D2  S1  S2 
=GLOOBS 2022-01-08 00:00:00       9 P1  P2  C1  L1  L2  D1  D2  S1  S2 

#====== Band available (v.1)
#GNSxEP 2022-01-08 00:00:00 FewBand x01 x02 x03 x04 x05 x06 x07 x08 x09 x10 x11 x12 x13 x14 x15 x16 x17 x18 x19 x20 x21 x22 x23 x24 x25 x26 x27 x28 x29 x30 x31 x32 x33 x34 x35 x36
=GPSCEP 2022-01-08 00:00:00     106  99  99 100  99  99  99  99  99  99  99   -  99  99  99  99  99  99  99  98 100  97   -  98 100  99  99  99   -  99 100  99  99   -   -   -   -
=GPSLEP 2022-01-08 00:00:00     106  99  99 100  99  99  99  99  99  99  99   -  99  99  99  99  99  99  99  98 100  97   -  98 100  99  99  99   -  99 100  99  99   -   -   -   -
=GLOCEP 2022-01-08 00:00:00    4420  99  81  94 100  99   0  69 100  75   0   -  70 100  98  60   -  99  99   -   -  75  88   0  99   -   -   -   -   -   -   -   -   -   -   -   -
=GLOLEP 2022-01-08 00:00:00    4422  99  81  94 100  99   0  69 100  75   0   -  70 100  98  60   -  99  99   -   -  75  88   0  99   -   -   -   -   -   -   -   -   -   -   -   -

#====== Gaps & Pieces (v.1)
#GAPLST 2022-01-08 begTime    endTime   >600s

#PCSLST 2022-01-08 begTime    endTime  <1800s

#SMPLST 2022-01-08 00:00:00  sampling   count
 SMPLST 2022-01-08 00:00:00        30    2879

#====== Preprocessing results (v.1)
#GNSPRP 2022-01-08 00:00:00      CS_Total       CS_Slip      CS_Epoch     CS_Satell     CS_Signal
=GPSPRP 2022-01-08 00:00:00           855           530             0           242            83
=GLOPRP 2022-01-08 00:00:00           966             0             0           240           726

#GNSxxx 2022-01-08 00:00:00      CS_Total       CS_Slip      CS_Epoch     CS_Satell     CS_Signal
=GPSL1  2022-01-08 00:00:00           428           265             0           121            42
=GPSL2  2022-01-08 00:00:00           427           265             0           121            41
=GLOL1  2022-01-08 00:00:00           483             0             0           120           363
=GLOL2  2022-01-08 00:00:00           483             0             0           120           363


#GNSSLP 2022-01-08 00:00:00  PRN           L1           L2

#====== Code multipath (v.1)
#GNSMxx 2022-01-08 00:00:00    mean x01 x02 x03 x04 x05 x06 x07 x08 x09 x10 x11 x12 x13 x14 x15 x16 x17 x18 x19 x20 x21 x22 x23 x24 x25 x26 x27 x28 x29 x30 x31 x32 x33 x34 x35 x36
=GPSMP1 2022-01-08 00:00:00   35.07  29  37  29  44  33  36  31  33  32  23   -  33  50  39  29  54  33  42  34  53  39   -  33  29  29  34  29   -  34  30  33  31   -   -   -   -
=GPSMP2 2022-01-08 00:00:00   35.22  28  39  30  46  27  38  29  34  36  22   -  30  55  42  29  55  25  44  31  54  46   -  38  27  29  33  28   -  34  31  31  27   -   -   -   -
=GPSMC1 2022-01-08 00:00:00   65.00  67  69  64  64  63  65  60  63  71  56   -  68  64  61  69  65  67  64  60  63  63   -  64  67  63  72  67   -  71  71  67  55   -   -   -   -


#====== Signal to noise ratio (v.1)
#GNSSxx 2022-01-08 00:00:00    mean x01 x02 x03 x04 x05 x06 x07 x08 x09 x10 x11 x12 x13 x14 x15 x16 x17 x18 x19 x20 x21 x22 x23 x24 x25 x26 x27 x28 x29 x30 x31 x32 x33 x34 x35 x36
=GPSSS1 2022-01-08 00:00:00   30.99  34  28  33  25  32  34  35  33  33  38   -  32  22  27  33  22  35  27  29  23  23   -  28  33  34  33  33   -  34  34  33  39   -   -   -   -
=GPSSS2 2022-01-08 00:00:00   31.14  34  28  33  25  32  34  35  33  34  39   -  32  22  27  33  22  36  27  29  23  23   -  27  33  35  33  34   -  34  34  33  39   -   -   -   -
=GLOSS1 2022-01-08 00:00:00   37.85  36  41  38  38  39   -  38  38  39   -   -  40  31  42  39   -  38  40   -   -  38  30   -  39   -   -   -   -   -   -   -   -   -   -   -   -
=GLOSS2 2022-01-08 00:00:00   36.10  36  26  39  40  40   -  41  39  37   -   -  29  38  40  21   -  40  40   -   -  39  28   -  40   -   -   -   -   -   -   -   -   -   -   -   -

"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)

            result = self.anubis._parsing_xtr(temp_file.name)

            self.assertEqual({'date': '2022-01-08 00:00:00',
                              'total_time': 24.0,
                              'expt_obs': 45706,
                              'exis_obs': 41328,
                              'ratio': 90.42,
                              'expt_obs10': 36283,
                              'exis_obs10': 36000,
                              'ratio10': 99.22,
                              'miss_epoch': {'GPS': 0, 'GLO': 0},
                              'code_multi': {'GPSMP1': 50.0, 'GPSMP2': 35.2, 'GLOMP1': '-', 'GLOMP2': '-'},
                              'n_slip': {'GPS': 530, 'GLO': 0},
                              'sat_healthy': {'GPS': 29, 'GLO': 17},
                              'sig2noise': {'GPSSS1': 30.99, 'GPSSS2': 31.14, 'GLOSS1': 37.85, 'GLOSS2': 36.1}}, result)


if __name__ == "__main__":
    main()
