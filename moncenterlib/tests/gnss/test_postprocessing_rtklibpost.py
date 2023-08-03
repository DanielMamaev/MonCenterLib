from pathlib import Path
import sys
import unittest
from moncenterlib.gnss.postprocessing import RtkLibPost
from pprint import pprint


class TestRtkLibPost(unittest.TestCase):
    input_test_files = str(Path(__file__).resolve().parent) + "/data/Post/"
    output_files = str(Path(__file__).resolve().parent) + "/output/"
    
    def test_scans_dirs_no_recursion(self):
        paths = {
            'rover': f'{self.input_test_files}obs/NSK1',
            'base': f'{self.input_test_files}obs/NOVM',
            'nav': f'{self.input_test_files}nav',
        }

        postproc = RtkLibPost()
        list_files = postproc.scan_dir(paths)
        pprint(list_files)
        self.assertEqual(len(list_files['rover']), 4, "Should be 10 files")
        self.assertEqual(len(list_files['base']), 4, "Should be 10 files")
        self.assertEqual(len(list_files['nav']), 4, "Should be 10 files")
    
    def test_scans_dirs_recursion(self):
        paths = {
            'rover': f'{self.input_test_files}obs/NSK1',
            'base': f'{self.input_test_files}obs/NOVM',
            'nav': f'{self.input_test_files}nav',
        }

        postproc = RtkLibPost()
        list_files = postproc.scan_dir(paths, True)
        pprint(list_files)
        self.assertEqual(len(list_files['rover']), 5, "Should be 10 files")
        self.assertEqual(len(list_files['base']), 5, "Should be 10 files")
        self.assertEqual(len(list_files['nav']), 5, "Should be 10 files")

    def test_kinematic_5out(self):
        paths = {
            'rover': f'{self.input_test_files}obs/NSK1',
            'base': f'{self.input_test_files}obs/NOVM',
            'nav': f'{self.input_test_files}nav'
        }

        postproc = RtkLibPost()

        config = postproc.DEFAULT_CONFIG
        config['pos1-posmode'] = '2'
        config['ant2-postype'] = '1'
        config['ant2-pos1'] = '452260.4656'
        config['ant2-pos2'] = '3635878.4702'
        config['ant2-pos3'] = '5203454.4147'
        config['out-solformat'] = '1'
        
        list_files = postproc.scan_dir(paths, True)
        result = postproc.start(list_files, self.output_files, config)
        pprint(result)
        
        self.assertEqual(len(result['done']), 5, "Should be 10 files")
    
    def test_kinematic_1out(self):
        paths = {
            'rover': f'{self.input_test_files}obs/NSK1/nsk10060.22o',
            'base': f'{self.input_test_files}obs/NOVM/novm0060.22o',
            'nav': f'{self.input_test_files}nav/nsk10060.22n',
        }

        postproc = RtkLibPost()

        config = postproc.DEFAULT_CONFIG
        config['pos1-posmode'] = '2'
        config['ant2-postype'] = '1'
        config['ant2-pos1'] = '452260.4656'
        config['ant2-pos2'] = '3635878.4702'
        config['ant2-pos3'] = '5203454.4147'
        config['out-solformat'] = '1'
        
        result = postproc.start(paths, self.output_files, config)
        pprint(result)
        
        self.assertEqual(len(result['done']), 1, "Should be 1 files")
    


if __name__ == '__main__':
    unittest.main()