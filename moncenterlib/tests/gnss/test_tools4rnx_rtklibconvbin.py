from pathlib import Path
import sys
import unittest
from moncenterlib.gnss.tools4rnx import RtkLibConvbin


class TestRtkLibConvbin(unittest.TestCase):
    input_test_files = str(Path(__file__).resolve().parent) + "/data/Raw/"
    output_files = str(Path(__file__).resolve().parent) + "/output/"
    
    def test_one_file(self):
        conv = RtkLibConvbin()
        config = conv.DEFAULT_CONFIG
        config['format'] = 'ubx'

        result = conv.start(self.input_test_files + "nskv3620.ubx", self.output_files, config)
        
        self.assertEqual(len(result['done']), 2, "Should be 2 files")
    
    def test_dir_norecursion(self):
        conv = RtkLibConvbin()
        config = conv.DEFAULT_CONFIG
        config['format'] = 'ubx'

        list_files = conv.scan_dir(self.input_test_files)
        result = conv.start(list_files, self.output_files, config)
        
        self.assertEqual(len(result['done']), 4, "Should be 4 files")
    
    def test_dir_recursion(self):
        conv = RtkLibConvbin()
        config = conv.DEFAULT_CONFIG
        config['format'] = 'ubx'

        list_files = conv.scan_dir(self.input_test_files, True)
        result = conv.start(list_files, self.output_files, config)
        
        self.assertEqual(len(result['done']), 8, "Should be 8 files")


if __name__ == '__main__':
    unittest.main()