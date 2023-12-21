import os
import subprocess
from unittest import TestCase
from unittest.mock import MagicMock, patch
from pathlib import Path
from moncenterlib.gnss.tools4rnx import RtkLibConvbin


class TestTools4Rnx(TestCase):
    def setUp(self) -> None:
        self.t4r = RtkLibConvbin()

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
        self.assertEqual(str(ms.exception), "Path to dir is strange.")

    def test_func_scan_dir(self):
        with patch("moncenterlib.gnss.tools4rnx.os.walk") as mock_walk:
            mock_walk.return_value = (("/home/", None, ["file1", "file2"]), ("/home/2/", None, ["file3", "file4"]))
            res = self.t4r.scan_dir("/", True)
            self.assertEqual(len(res), 4)
            self.assertEqual(['/home/file1', '/home/file2', '/home/2/file3', '/home/2/file4'], res)

            mock_walk.return_value = (("/home/", None, []), ("/home/2/", None, ["file3", "file4"]))
            res = self.t4r.scan_dir("/", True)
            self.assertEqual(len(res), 2)
            self.assertEqual(['/home/2/file3', '/home/2/file4'], res)

            mock_walk.return_value = (("/home/", None, []), ("/home/2/", None, []))
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
            self.t4r.start(123, 'path', self.t4r.get_default_config(), False, False)

        with self.assertRaises(Exception) as ms:
            self.t4r.start('path', 123, self.t4r.get_default_config(), False, False)

        with self.assertRaises(Exception) as ms:
            self.t4r.start('path', 'path', 'dict()', False, False)

        with self.assertRaises(Exception) as ms:
            self.t4r.start('path', 'path', self.t4r.get_default_config(), 'False', False)

        with self.assertRaises(Exception) as ms:
            self.t4r.start('path', 'path', self.t4r.get_default_config(), False, 'False')

        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', self.t4r.get_default_config(), False, False)
        self.assertEqual(str(ms.exception), "Path to file or dir is strange.")

        with self.assertRaises(ValueError) as ms:
            self.t4r.start(os.curdir, 'path', self.t4r.get_default_config(), False, False)
        self.assertEqual(str(ms.exception), "Path to output dir is strange.")

        with self.assertRaises(ValueError) as ms:
            self.t4r.start(os.curdir, 'path', self.t4r.get_default_config(), False, False)
        self.assertEqual(str(ms.exception), "Path to output dir is strange.")

    @patch('moncenterlib.gnss.tools4rnx.subprocess')
    def test_start_with_input_list(self, mock_subprocess):
        mock_subprocess.run = MagicMock()

        list_files = ['/home/file1', '/home/file2', '/home/2/file3', '/home/2/file4']
        self.t4r.start(list_files, "/", self.t4r.get_default_config(), False, False)

        exis_list = []
        for i in mock_subprocess.run.call_args_list:
            exis_list += i[0][0]
        for i in list_files:
            self.assertIn(i, exis_list)

    def test_start_with_input_dir(self):
        with (patch("moncenterlib.gnss.tools4rnx.subprocess") as mock_subprocess,
              patch("moncenterlib.gnss.tools4rnx.RtkLibConvbin.scan_dir") as mock_scan_dir):

            list_files = ['/home/file1', '/home/file2', '/home/2/file3', '/home/2/file4']

            mock_subprocess.run = MagicMock()
            mock_scan_dir.return_value = list_files

            self.t4r.start("/", "/", self.t4r.get_default_config(), False, False)
            exis_list = []
            for i in mock_subprocess.run.call_args_list:
                exis_list += i[0][0]
            for i in list_files:
                self.assertIn(i, exis_list)

    def test_start_with_input_file(self):
        with (patch("moncenterlib.gnss.tools4rnx.subprocess") as mock_subprocess,
              patch("moncenterlib.gnss.tools4rnx.os.path.isfile") as mock_isfile):
            mock_isfile.return_value = True
            mock_subprocess.run = MagicMock()

            self.t4r.start('/home/file1', "/", self.t4r.get_default_config(), False, False)
            exis_list = mock_subprocess.run.call_args_list[0][0][0]
            self.assertIn('/home/file1', exis_list)

    @patch('moncenterlib.gnss.tools4rnx.subprocess')
    def test_raises_config(self, mock_subprocess):
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', dict(), False, False)
        self.assertEqual(str(ms.exception), "Config is empty.")

        with self.assertRaises(TypeError) as ms:
            self.t4r.start('path', 'path', {'k': 1}, False, False)
        self.assertEqual(str(ms.exception), "Config. Value '1' of key 'k' must be str.")

        with self.assertRaises(TypeError) as ms:
            self.t4r.start('path', 'path', {111: 1}, False, False)
        self.assertEqual(str(ms.exception), "Config. Key '111' must be str.")

        with self.assertRaises(Exception) as ms:
            self.t4r.start('path', 'path', {'111': '1'}, False, False)
        self.assertEqual(str(ms.exception), "Config. Not found key 'format'.")

        config = self.t4r.get_default_config()
        config['format'] = 'uuu'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: format. Unknown format 'uuu'.")
        config['format'] = 'ubx'

        config['rinex_v'] = '1.0'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: rinex_v. Unknown rinex version '1.0'.")
        config['rinex_v'] = '3.04'

        config['start_time'] = '01.01.1900'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception),
                         "Config. Key: start_time. Incorrect data format 01.01.1900, should be YYYY/MM/DD HH:MM:SS.")
        config['start_time'] = ''

        config['end_time'] = '01.01.1900'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception),
                         "Config. Key: end_time. Incorrect data format 01.01.1900, should be YYYY/MM/DD HH:MM:SS.")
        config['end_time'] = ''

        config['interval'] = '-1'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: interval. Interval -1 must be >= 0.")
        config['interval'] = '0'

        config['freq'] = '-1'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: freq. Freq -1 must be 0 <= freq <= 127.")
        config['freq'] = '3'

        config['freq'] = '128'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: freq. Freq 128 must be 0 <= freq <= 127.")
        config['freq'] = '3'

        config['system'] = 'A'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: system. Unknown system 'A'.")
        config['system'] = 'G,R'

        config['system'] = 'G,R,A,B'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: system. Unknown system 'A'.")
        config['system'] = 'G,R'

        config['output_o'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_o. Unknown value 'nothing'.")
        config['output_o'] = '1'

        config['output_n'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_n. Unknown value 'nothing'.")
        config['output_n'] = '1'

        config['output_g'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_g. Unknown value 'nothing'.")
        config['output_g'] = '1'

        config['output_h'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_h. Unknown value 'nothing'.")
        config['output_h'] = '1'

        config['output_q'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_q. Unknown value 'nothing'.")
        config['output_q'] = '1'

        config['output_l'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_l. Unknown value 'nothing'.")
        config['output_l'] = '1'

        config['output_b'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_b. Unknown value 'nothing'.")
        config['output_b'] = '1'

        config['output_i'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_i. Unknown value 'nothing'.")
        config['output_i'] = '1'

        config['output_s'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: output_s. Unknown value 'nothing'.")
        config['output_s'] = '1'

        config['other_od'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_od. Unknown value 'nothing'.")
        config['other_od'] = '1'

        config['other_os'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_os. Unknown value 'nothing'.")
        config['other_os'] = '1'

        config['other_oi'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_oi. Unknown value 'nothing'.")
        config['other_oi'] = '1'

        config['other_ot'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_ot. Unknown value 'nothing'.")
        config['other_ot'] = '1'

        config['other_ol'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_ol. Unknown value 'nothing'.")
        config['other_ol'] = '1'

        config['other_halfc'] = 'nothing'
        with self.assertRaises(ValueError) as ms:
            self.t4r.start('path', 'path', config, False, False)
        self.assertEqual(str(ms.exception), "Config. Key: other_halfc. Unknown value 'nothing'.")
        config['other_halfc'] = '1'

    def test_config(self):
        with (patch("moncenterlib.gnss.tools4rnx.subprocess.run") as mock_subprocess,
              patch("moncenterlib.gnss.tools4rnx.os.path.isfile") as mock_isfile):

            mock_isfile.return_value = True

            config = self.t4r.get_default_config()
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

            self.t4r.start('/home/file1', "/", config, False, False)

            exp_cmd = [str(Path(__file__).resolve().parent.parent.parent.joinpath("gnss", "bin", "convbin")),
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

            self.assertEqual(mock_subprocess.call_args_list[0][0][0], exp_cmd)

    def test_show_process(self):
        with (patch('moncenterlib.gnss.tools4rnx.subprocess'),
              patch('moncenterlib.gnss.tools4rnx.IncrementalBar') as mock_incrementalbar):
            self.t4r.start("/", "/", self.t4r.get_default_config(), False, True)
            self.assertGreater(len(mock_incrementalbar.mock_calls), 1)

            mock_incrementalbar.mock_calls = []
            self.t4r.start("/", "/", self.t4r.get_default_config(), False, False)
            self.assertEqual(len(mock_incrementalbar.mock_calls), 1)

    def test_chech_make_convbin(self):
        path = str(Path(__file__).resolve().parent.parent.parent.joinpath("gnss", "bin", "convbin"))
        res = subprocess.run([path, "-h"], stderr=subprocess.DEVNULL, check=False)
        self.assertEqual(0, res.returncode)

    def test_output_result(self):
        with (patch('moncenterlib.gnss.tools4rnx.subprocess')):
            list_files = ['/home/file1', '/home/file2']
            res = self.t4r.start(list_files, "/", self.t4r.get_default_config(), False, False)
            self.assertEqual({"done": [],
                              "error": ['/file1.o', '/file1.n',
                                        '/file2.o', '/file2.n', ]}, res)
