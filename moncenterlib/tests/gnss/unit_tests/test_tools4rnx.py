from collections import defaultdict
from logging import Logger
import logging
import os
import subprocess
import tempfile
import time
from unittest import TestCase, main
from unittest.mock import MagicMock, patch, call
from pathlib import Path
from moncenterlib.gnss.tools4rnx import RtkLibConvbin
from moncenterlib.tools import get_path2bin


class TestTools4Rnx(TestCase):
    def setUp(self) -> None:
        self.t4r = RtkLibConvbin(logger=False)

    def test_init(self):
        t4r = RtkLibConvbin(logger=False)

        self.assertIsInstance(t4r, RtkLibConvbin)
        self.assertEqual(t4r.workers, 1)

        def def_dict(): return {
            'stdout': [],
            'stderr': []
        }
        exis_std_log = defaultdict(def_dict)

        self.assertEqual(t4r.output_files, defaultdict(list))
        self.assertEqual(t4r.std_log, exis_std_log)
        self.assertTrue(hasattr(t4r, "_RtkLibConvbin__process"))
        self.assertIsInstance(t4r.logger, Logger)

        t4r_2 = RtkLibConvbin(10, False)
        self.assertEqual(t4r_2.workers, 10)

    def test_init_raises(self):
        with self.assertRaises(Exception):
            convbin = RtkLibConvbin("None")

    def test_init_with_enable_logger(self):
        convbin = RtkLibConvbin()
        self.assertEqual(Logger, type(convbin.logger))
        self.assertEqual("RtkLibConvbin", convbin.logger.name)

    def test_init_with_disable_logger(self):
        convbin = RtkLibConvbin(False)
        self.assertEqual(Logger, type(convbin.logger))
        self.assertEqual("RtkLibConvbin", convbin.logger.name)

    def test_init_with_my_logger(self):
        logger = logging.getLogger()
        convbin = RtkLibConvbin(logger=logger)
        self.assertEqual(logger, convbin.logger)
        self.assertEqual("root", convbin.logger.name)

    def test_init_check_dublicate_handlers(self):
        convbin = RtkLibConvbin()
        convbin = RtkLibConvbin()
        self.assertEqual(1, len(convbin.logger.handlers))

    def test_different_id_default_config(self):
        config = self.t4r.get_default_config()
        self.assertNotEqual(id(config), id(self.t4r._RtkLibConvbin__default_config))

    def test_scan_dir_raises(self):
        with self.assertRaises(Exception) as ms:
            self.t4r.scan_dir(123, False)

        with self.assertRaises(Exception) as ms:
            self.t4r.scan_dir('test', 123)

        with self.assertRaises(Exception) as ms:
            self.t4r.scan_dir(123, 123)

        with self.assertRaises(ValueError) as ms:
            self.t4r.scan_dir('test', False)
        self.assertEqual(str(ms.exception), "Path 'test' to dir is strange.")

    def test_func_scan_dir(self):
        with patch("moncenterlib.gnss.tools4rnx.get_files_from_dir") as mock_get_files_from_dir:
            mock_get_files_from_dir.return_value = ['/home/file1', '/home/file2', '/home/2/file3', '/home/2/file4']
            res = self.t4r.scan_dir("/", True)
            self.assertEqual(len(res), 4)
            self.assertEqual(['/home/file1', '/home/file2', '/home/2/file3', '/home/2/file4'], res)

            mock_get_files_from_dir.return_value = []
            res = self.t4r.scan_dir("/", True)
            self.assertEqual(len(res), 0)
            self.assertEqual([], res)

        with (patch("moncenterlib.gnss.tools4rnx.os.listdir") as mock_listdir,
              patch("moncenterlib.gnss.tools4rnx.os.path.isfile") as mock_isfile):
            mock_isfile.side_effect = [True, True, False, False, True]
            mock_listdir.return_value = ['/home/file1', '/home/file2', '/home/2/', '/home/2/', '/home/file3']

            res = self.t4r.scan_dir("/", False)
            self.assertEqual(len(res), 3)
            self.assertEqual(['/home/file1', '/home/file2', '/home/file3'], res)

    def test_start_raises(self):
        with self.assertRaises(Exception) as ms:
            self.t4r.start(123, 'path', self.t4r.get_default_config(), False)

        with self.assertRaises(Exception) as ms:
            self.t4r.start('path', 123, self.t4r.get_default_config(), False)

        with self.assertRaises(Exception) as ms:
            self.t4r.start('path', 'path', 'dict()', False)

        with self.assertRaises(Exception) as ms:
            self.t4r.start('path', 'path', self.t4r.get_default_config(), 'False')

        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', self.t4r.get_default_config(), False)
        self.assertEqual(str(ms.exception), "Path to file or dir is strange.")

        with self.assertRaises(ValueError) as ms:
            self.t4r.start(os.curdir, 'path', self.t4r.get_default_config(), False)
        self.assertEqual(str(ms.exception), "Path to output dir is strange.")

        with self.assertRaises(ValueError) as ms:
            self.t4r.start(os.curdir, 'path', self.t4r.get_default_config(), False)
        self.assertEqual(str(ms.exception), "Path to output dir is strange.")

    @patch("os.path.isdir")
    @patch("threading.Thread")
    def test_start_with_input_list(self, mock_thread, mock_isdir):
        mock_isdir.return_value = True

        t4r = RtkLibConvbin(logger=False)
        make_config4convbin_mock = MagicMock()
        make_config4convbin_mock.return_value = ("CMD", {})
        t4r._RtkLibConvbin__make_config4convbin = make_config4convbin_mock

        list_files = ['/home/file1', '/home/file2', '/home/2/file3', '/home/2/file4']
        t4r.start(list_files, "/", self.t4r.get_default_config(), False)

        exis_list = []
        for i in make_config4convbin_mock.call_args_list:
            exis_list += [i.args[0]]
        for i in list_files:
            self.assertIn(i, exis_list)

    @patch("moncenterlib.gnss.tools4rnx.RtkLibConvbin.scan_dir")
    @patch("os.path.isdir")
    @patch("threading.Thread")
    def test_start_with_input_dir(self, mock_thread, mock_isdir, mock_scan_dir):
        list_files = ['/home/file1', '/home/file2', '/home/2/file3', '/home/2/file4']
        mock_scan_dir.return_value = list_files

        t4r = RtkLibConvbin(logger=False)
        make_config4convbin_mock = MagicMock()
        make_config4convbin_mock.return_value = ("CMD", {})
        t4r._RtkLibConvbin__make_config4convbin = make_config4convbin_mock
        t4r.start("/", "/", self.t4r.get_default_config())

        exis_list = []
        for i in make_config4convbin_mock.call_args_list:
            exis_list += [i.args[0]]
        for i in list_files:
            self.assertIn(i, exis_list)

    @patch("moncenterlib.gnss.tools4rnx.os.path.isfile")
    @patch("threading.Thread")
    def test_start_with_input_file(self, mock_thread, mock_isfile):

        mock_isfile.return_value = True

        t4r = RtkLibConvbin(logger=False)
        make_config4convbin_mock = MagicMock()
        make_config4convbin_mock.return_value = ("CMD", {})
        t4r._RtkLibConvbin__make_config4convbin = make_config4convbin_mock

        t4r.start('/home/file1', "/", self.t4r.get_default_config(), False)

        self.assertEqual(make_config4convbin_mock.call_args_list[0].args[0], '/home/file1')

    def test_raises_config(self):
        t4r = RtkLibConvbin(logger=False)
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', dict(), False)
        self.assertEqual(str(ms.exception), "Config is empty.")

        with self.assertRaises(TypeError) as ms:
            t4r.start('path', 'path', {'k': 1}, False)
        self.assertEqual(str(ms.exception), "Config. Value '1' of key 'k' must be str.")

        with self.assertRaises(TypeError) as ms:
            t4r.start('path', 'path', {111: 1}, False)
        self.assertEqual(str(ms.exception), "Config. Key '111' must be str.")

        with self.assertRaises(Exception) as ms:
            t4r.start('path', 'path', {'111': '1'}, False)
        self.assertEqual(str(ms.exception), "Config. Not found key 'format'.")

        config = t4r.get_default_config()
        config['format'] = 'uuu'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: format. Unknown format 'uuu'.")
        config['format'] = 'ubx'

        config['rinex_v'] = '1.0'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: rinex_v. Unknown rinex version '1.0'.")
        config['rinex_v'] = '3.04'

        config['start_time'] = '01.01.1900'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception),
                         "Config. Key: start_time. Incorrect data format 01.01.1900, should be YYYY/MM/DD HH:MM:SS.")
        config['start_time'] = ''

        config['end_time'] = '01.01.1900'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception),
                         "Config. Key: end_time. Incorrect data format 01.01.1900, should be YYYY/MM/DD HH:MM:SS.")
        config['end_time'] = ''

        config['interval'] = '-1'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: interval. Interval -1 must be >= 0.")
        config['interval'] = '0'

        config['freq'] = '-1'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: freq. Freq -1 must be 0 <= freq <= 127.")
        config['freq'] = '3'

        config['freq'] = '128'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: freq. Freq 128 must be 0 <= freq <= 127.")
        config['freq'] = '3'

        config['system'] = 'A'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: system. Unknown system 'A'.")
        config['system'] = 'G,R'

        config['system'] = 'G,R,A,B'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: system. Unknown system 'A'.")
        config['system'] = 'G,R'

        config['output_o'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_o. Unknown value 'nothing'.")
        config['output_o'] = '1'

        config['output_n'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_n. Unknown value 'nothing'.")
        config['output_n'] = '1'

        config['output_g'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_g. Unknown value 'nothing'.")
        config['output_g'] = '1'

        config['output_h'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_h. Unknown value 'nothing'.")
        config['output_h'] = '1'

        config['output_q'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_q. Unknown value 'nothing'.")
        config['output_q'] = '1'

        config['output_l'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_l. Unknown value 'nothing'.")
        config['output_l'] = '1'

        config['output_b'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_b. Unknown value 'nothing'.")
        config['output_b'] = '1'

        config['output_i'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_i. Unknown value 'nothing'.")
        config['output_i'] = '1'

        config['output_s'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_s. Unknown value 'nothing'.")
        config['output_s'] = '1'

        config['other_od'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_od. Unknown value 'nothing'.")
        config['other_od'] = '1'

        config['other_os'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_os. Unknown value 'nothing'.")
        config['other_os'] = '1'

        config['other_oi'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_oi. Unknown value 'nothing'.")
        config['other_oi'] = '1'

        config['other_ot'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_ot. Unknown value 'nothing'.")
        config['other_ot'] = '1'

        config['other_ol'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_ol. Unknown value 'nothing'.")
        config['other_ol'] = '1'

        config['other_halfc'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            t4r.start('path', 'path', config, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_halfc. Unknown value 'nothing'.")
        config['other_halfc'] = '1'

    @patch("queue.Queue")
    @patch("moncenterlib.gnss.tools4rnx.os.path.isfile")
    @patch("threading.Thread")
    def test_config(self, mock_thread, mock_isfile, mock_queue):
        t4r = RtkLibConvbin(logger=False)

        mock_isfile.return_value = True

        config = t4r.get_default_config()
        config['format'] = 'ubx'
        config['rinex_v'] = '3.03'
        config['start_time'] = '2023/10/27 00:00:00'
        config['end_time'] = '2023/12/27 00:00:00'
        config['interval'] = '5'
        config['freq'] = '1'
        config['system'] = 'G,R'
        config['output_o'] = '1'
        config['output_n'] = '1'
        config['output_g'] = '1'
        config['output_h'] = '1'
        config['output_q'] = '1'
        config['output_l'] = '1'
        config['output_b'] = '1'
        config['output_i'] = '1'
        config['output_s'] = '1'
        config['other_od'] = '1'
        config['other_os'] = '1'
        config['other_oi'] = '1'
        config['other_ot'] = '1'
        config['other_ol'] = '1'
        config['other_halfc'] = '1'
        config['comment'] = 'comment'
        config['marker_name'] = 'marker_name'
        config['marker_number'] = 'marker_number'
        config['marker_type'] = 'marker_type'
        config['about_name'] = 'about_name'
        config['about_agency'] = 'about_agency'
        config['receiver_number'] = 'receiver_number'
        config['receiver_type'] = 'receiver_type'
        config['receiver_version'] = 'receiver_version'
        config['antenna_number'] = 'antenna_number'
        config['antenna_type'] = 'antenna_type'
        config['approx_position_x'] = '1'
        config['approx_position_y'] = '2'
        config['approx_position_z'] = '3'
        config['antenna_delta_h'] = '4'
        config['antenna_delta_e'] = '5'
        config['antenna_delta_n'] = '6'

        t4r.start('/home/file1', "/", config, False)

        exp_cmd = [get_path2bin("convbin"),
                   '-r', 'ubx',
                   '-v', '3.03',
                   '-ts', '2023/10/27 00:00:00',
                   '-te', '2023/12/27 00:00:00',
                   '-ti', '5',
                   '-f', '1',
                   '-y', 'C',
                   '-y', 'E',
                   '-y', 'I',
                   '-y', 'J',
                   '-y', 'S',
                   '-o', '/file1.o',
                   '-n', '/file1.n',
                   '-g', '/file1.g',
                   '-h', '/file1.h',
                   '-q', '/file1.q',
                   '-l', '/file1.l',
                   '-b', '/file1.b',
                   '-i', '/file1.i',
                   '-s', '/file1.s',
                   '-od',
                   '-os',
                   '-oi',
                   '-ot',
                   '-ol',
                   '-halfc',
                   '-hc', 'comment',
                   '-hm', 'marker_name',
                   '-hn', 'marker_number',
                   '-ht', 'marker_type',
                   '-ho', 'about_name/about_agency',
                   '-hr', 'receiver_number/receiver_type/receiver_version',
                   '-ha', 'antenna_number/antenna_type',
                   '-hp', '1/2/3',
                   '-hd', '4/5/6',
                   '/home/file1']

        self.assertEqual(t4r.output_files, {'o': ['/file1.o'], 'n': ['/file1.n'], 'g': ['/file1.g'], 'h': ['/file1.h'], 'q': [
                         '/file1.q'], 'l': ['/file1.l'], 'b': ['/file1.b'], 'i': ['/file1.i'], 's': ['/file1.s']})
        self.assertEqual(mock_queue.mock_calls[1].args[0], exp_cmd)

    def test_check_make_convbin(self):
        res = subprocess.run([get_path2bin("convbin"), "-h"], stderr=subprocess.DEVNULL, check=False)
        self.assertEqual(0, res.returncode)

    def test_output_result(self):
        t4r = RtkLibConvbin(logger=False)
        list_files = ['/home/file1', '/home/file2']
        t4r.start(list_files, "/", self.t4r.get_default_config(), False)
        while True:
            time.sleep(1)
            status = t4r.get_last_status()
            states = [s['isStop'] for s in status.values()]
            if all(states):
                break
        self.assertEqual(t4r.output_files, {'o': ['/file1.o', '/file2.o'], 'n': ['/file1.n', '/file2.n']})

    def test_real_working(self):
        t4r = RtkLibConvbin(logger=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = str(Path(__file__).resolve().parent.parent.joinpath(
                "data", "tools4rnx", "RtkLibConvbin", "observation.ubx"))
            config = t4r.get_default_config()

            config['format'] = 'ubx'
            config['rinex_v'] = '3.03'
            config['interval'] = '5'
            config['freq'] = '1'
            config['system'] = 'G,R'
            config['output_o'] = '1'
            config['output_n'] = '1'
            config['output_g'] = '1'
            config['output_h'] = '1'
            config['output_q'] = '1'
            config['output_l'] = '1'
            config['output_b'] = '1'
            config['output_i'] = '1'
            config['output_s'] = '1'
            config['other_od'] = '1'
            config['other_os'] = '1'
            config['other_oi'] = '1'
            config['other_ot'] = '1'
            config['other_ol'] = '1'
            config['other_halfc'] = '1'
            config['comment'] = 'comment'
            config['marker_name'] = 'marker_name'
            config['marker_number'] = 'marker_number'
            config['marker_type'] = 'marker_type'
            config['about_name'] = 'about_name'
            config['about_agency'] = 'about_agency'
            config['receiver_number'] = 'receiver_number'
            config['receiver_type'] = 'receiver_type'
            config['receiver_version'] = 'receiver_version'
            config['antenna_number'] = 'antenna_number'
            config['antenna_type'] = 'antenna_type'
            config['approx_position_x'] = '1'
            config['approx_position_y'] = '2'
            config['approx_position_z'] = '3'
            config['antenna_delta_h'] = '4'
            config['antenna_delta_e'] = '5'
            config['antenna_delta_n'] = '6'

            t4r.start(input_file, temp_dir, config)

            while True:
                time.sleep(1)
                status = t4r.get_last_status()
                states = [s['isStop'] for s in status.values()]
                if all(states):
                    break

            with (open(input_file.replace(".ubx", ".o"), "r", encoding="utf-8") as file1,
                  open(t4r.output_files["o"][0], "r", encoding="utf-8") as file2):

                lines1 = file1.readlines()
                lines2 = file2.readlines()

                self.assertEqual(len(lines1), len(lines2))

                for i, _ in enumerate(lines1):
                    if i != 1 and "log:" not in lines1[i]:
                        self.assertEqual(lines1[i], lines2[i])

    @patch("moncenterlib.gnss.tools4rnx.get_path2bin")
    @patch("moncenterlib.gnss.tools4rnx.os.path.isfile")
    @patch("queue.Queue")
    @patch("threading.Thread")
    def test_architecture(self, mock_thread, mock_queue, mock_isfile, mock_get_path2bin):
        t4r = RtkLibConvbin(logger=False)

        mock_isfile.return_value = True
        path_convbin = str(Path(__file__).resolve().parent.parent.parent.parent.joinpath(
            "gnss", "bin", "x86_64", "convbin_2.4.3-34_x86_64_linux"))
        mock_get_path2bin.return_value = path_convbin

        config = t4r.get_default_config()
        t4r.start('/home/file1', "/", config, False)

        self.assertEqual(path_convbin, mock_queue.mock_calls[1].args[0][0])

        mock_queue.reset_mock()
        path_convbin = Path(__file__).resolve().parent.parent.parent.parent.joinpath(
            "gnss", "bin", "aarch64", "convbin_2.4.3-34_aarch64_linux")
        mock_get_path2bin.return_value = path_convbin

        config = t4r.get_default_config()
        t4r.start('/home/file1', "/", config, False)

        self.assertEqual(path_convbin, mock_queue.mock_calls[1].args[0][0])

    def test_create_vars(self):
        t4r = RtkLibConvbin(logger=False)

        def def_dict(): return {
            'stdout': [],
            'stderr': []
        }
        exis_std_log = defaultdict(def_dict)

        self.assertEqual(t4r.output_files, defaultdict(list))
        self.assertEqual(t4r.std_log, exis_std_log)
        self.assertTrue(hasattr(t4r, "_RtkLibConvbin__process"))

    @patch("subprocess.Popen")
    @patch("threading.Thread")
    def test_start_converting(self, mock_thread, mock_Popen):
        t4r = RtkLibConvbin(logger=False)

        cmd = ['path_convbin',
               '-r', 'ubx',
               '-v', '3.03',
               '-ts', '2023/10/27 00:00:00',
               '-te', '2023/12/27 00:00:00',
               '-ti', '5',
               '-f', '1',
               '-y', 'C',
               '-y', 'E',
               '-y', 'I',
               '-y', 'J',
               '-y', 'S',
               '-o', '/file1.o',
               '-n', '/file1.n',
               '-g', '/file1.g',
               '-h', '/file1.h',
               '-q', '/file1.q',
               '-l', '/file1.l',
               '-b', '/file1.b',
               '-i', '/file1.i',
               '-s', '/file1.s',
               '-od',
               '-os',
               '-oi',
               '-ot',
               '-ol',
               '-halfc',
               '-hc', 'comment',
               '-hm', 'marker_name',
               '-hn', 'marker_number',
               '-ht', 'marker_type',
               '-ho', 'about_name/about_agency',
               '-hr', 'receiver_number/receiver_type/receiver_version',
               '-ha', 'antenna_number/antenna_type',
               '-hp', '1/2/3',
               '-hd', '4/5/6',
               '/home/file1']
        t4r._RtkLibConvbin__start_converting(cmd, False)

        self.assertEqual(mock_Popen.call_args[0][0], cmd)
        self.assertEqual(mock_Popen.call_args[1], {'stderr': -1, 'stdout': -1,
                         'text': True, 'bufsize': 1, 'universal_newlines': True})

        mock_thread_start = mock_thread()
        self.assertEqual(mock_thread_start.mock_calls, [call.start(), call.start()])

        t4r._RtkLibConvbin__start_converting(cmd, True)
        self.assertEqual(t4r._RtkLibConvbin__process["/home/file1"].mock_calls[0], call.wait())

        # TODO: не все проверено, создание тредов

    def test_merge_rinex(self):
        t4r = RtkLibConvbin(logger=False)
        mock_check_config = MagicMock()
        mock_create_vars = MagicMock()

        mock_start_converting = MagicMock()
        mock_make_config4convbin = MagicMock()
        mock_make_config4convbin.return_value = (["cmd1", "cmd2"], {"o": "file1", 'n': "file2"})

        t4r._RtkLibConvbin__check_config = mock_check_config
        t4r._RtkLibConvbin__create_vars = mock_create_vars
        t4r._RtkLibConvbin__start_converting = mock_start_converting
        t4r._RtkLibConvbin__make_config4convbin = mock_make_config4convbin

        t4r.merge_rinex('/input_dir/*', '/output_dir', 'filename', {"a": "a"}, False)

        self.assertEqual(mock_check_config.mock_calls[0].args[0], {"a": "a"})
        self.assertTrue(mock_create_vars.called)
        self.assertEqual(mock_make_config4convbin.mock_calls[0].args,
                         ('/input_dir/*', '/output_dir', {'a': 'a'}, 'filename'))
        self.assertEqual(t4r.output_files, {"o": ["file1"], 'n': ["file2"]})
        self.assertEqual(mock_start_converting.mock_calls[0].args[0], ["cmd1", "cmd2"])
        self.assertEqual(mock_start_converting.mock_calls[0].args[1], False)

        mock_start_converting.reset_mock()
        t4r.merge_rinex('/input_dir/*', '/output_dir', 'filename', {"a": "a"}, True)
        self.assertTrue(mock_start_converting.mock_calls[0].args[1])

    @patch("moncenterlib.tools.get_path2bin")
    def test_make_config4convbin(self, mock_get_path2bin):
        t4r = RtkLibConvbin(logger=False)

        mock_get_path2bin.return_value = "path2convbin"
        config = t4r.get_default_config()

        # if merge
        cmd, output_files = t4r._RtkLibConvbin__make_config4convbin(
            "/input_dir/*", "/output_dir/", config, "output_filename")
        self.assertEqual(output_files, {'o': '/output_dir/output_filename.o', 'n': '/output_dir/output_filename.n'})
        self.assertEqual(cmd, ['/home/danisimo/MonCenter_Project/MonCenterLib/moncenterlib/gnss/bin/x86_64/convbin_2.4.3-34_x86_64_linux', '-r', 'rtcm2', '-v', '3.04', '-ti', '0', '-f', '3', '-o',
                         '/output_dir/output_filename.o', '-n', '/output_dir/output_filename.n', '-od', '-os', '-hc', '', '-hm', '', '-hn', '', '-ht', '', '-ho', '/', '-hr', '//', '-ha', '/', '-hp', '//', '-hd', '//', '/input_dir/*'])

        # if not merge
        cmd, output_files = t4r._RtkLibConvbin__make_config4convbin("/file.o", "/output_dir/", config)
        self.assertEqual(output_files, {'o': '/output_dir/file.o', 'n': '/output_dir/file.n'})
        self.assertEqual(cmd, ['/home/danisimo/MonCenter_Project/MonCenterLib/moncenterlib/gnss/bin/x86_64/convbin_2.4.3-34_x86_64_linux', '-r', 'rtcm2', '-v', '3.04', '-ti', '0', '-f', '3', '-o',
                         '/output_dir/file.o', '-n', '/output_dir/file.n', '-od', '-os', '-hc', '', '-hm', '', '-hn', '', '-ht', '', '-ho', '/', '-hr', '//', '-ha', '/', '-hp', '//', '-hd', '//', '/file.o'])

    def test_get_last_status(self):
        t4r = RtkLibConvbin(logger=False)
        self.assertEqual(t4r.get_last_status(), {})

        mock_process = MagicMock()
        t4r._RtkLibConvbin__process = {"/home/file1": mock_process}
        t4r.std_log = {
            "/home/file1": {
                "stdout": ["Status: Running"],
                "stderr": ["Error: File not found"]
            }
        }

        self.assertEqual(t4r.get_last_status(), {
                         '/home/file1': {'stdout': 'Status: Running', 'stderr': 'Error: File not found', 'isStop': True}})

        t4r._RtkLibConvbin__process = {"/home/file1": None}
        self.assertEqual(t4r.get_last_status(), {
                         '/home/file1': {'stdout': 'Status: Running', 'stderr': 'Error: File not found', 'isStop': False}})

        mock_process.pull.return_value = "Not None"
        self.assertEqual(t4r.get_last_status(), {
                         '/home/file1': {'stdout': 'Status: Running', 'stderr': 'Error: File not found', 'isStop': False}})

        mock_process = MagicMock()
        t4r._RtkLibConvbin__process = {"/home/file1": mock_process}
        t4r.std_log = {
            "/home/file1": {
                "stdout": ["Status: Running", "ddsdsds"],
                "stderr": ["Error: File not found", "dssdsdsd"]
            }
        }
        self.assertEqual(t4r.get_last_status(), {
                         '/home/file1': {'stdout': 'ddsdsds', 'stderr': 'dssdsdsd', 'isStop': True}})

    def test_get_full_status(self):
        t4r = RtkLibConvbin(logger=False)
        self.assertEqual(t4r.get_full_status(), {})

        t4r.std_log = {
            "/home/file1": {
                "stdout": ["Status: Running", "ddsdsds"],
                "stderr": ["Error: File not found", "dssdsdsd"]
            }
        }

        self.assertEqual(t4r.get_full_status(), {
            "/home/file1": {
                "stdout": ["Status: Running", "ddsdsds"],
                "stderr": ["Error: File not found", "dssdsdsd"]
            }
        })


if __name__ == "__main__":
    main()
