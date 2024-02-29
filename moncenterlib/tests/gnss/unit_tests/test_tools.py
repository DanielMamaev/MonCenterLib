from pathlib import Path
import tempfile
from unittest import TestCase, main
from unittest.mock import MagicMock, patch, call
import moncenterlib.gnss.tools as mcl_tools


class TestTools(TestCase):
    def test_files_check(self):
        with patch("moncenterlib.gnss.tools.Path.exists") as mock_exists:
            mock_exists.return_value = True
            files = ["/file1", "/file2", "/file3"]
            result = mcl_tools.files_check(files)
            self.assertEqual({"done": ["/file1", "/file2", "/file3"], "error": []}, result)

            mock_exists.return_value = False
            files = ["/file1", "/file2", "/file3"]
            result = mcl_tools.files_check(files)
            self.assertEqual({"error": ["/file1", "/file2", "/file3"], "done": []}, result)

            mock_exists.side_effect = [False, True, False]
            files = ["/file1", "/file2", "/file3"]
            result = mcl_tools.files_check(files)
            self.assertEqual({"error": ["/file1", "/file3"], "done": ["/file2"]}, result)

        result = mcl_tools.files_check([])
        self.assertEqual({'done': [], 'error': []}, result)

    def test_get_path2bin(self):
        with patch("moncenterlib.gnss.tools.platform") as mock_platform:
            # Linux and x86_64
            mock_platform.system.return_value = "Linux"
            mock_platform.machine.return_value = "x86_64"
            path2bin = mcl_tools.get_path2bin("anubis")
            exp = str(Path(__file__).resolve().parent.parent.parent.parent.joinpath(
                "gnss/bin/x86_64/anubis_2.3_x86_64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("str2str")
            exp = str(Path(__file__).resolve().parent.parent.parent.parent.joinpath(
                "gnss/bin/x86_64/str2str_2.4.3-34_x86_64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("convbin")
            exp = str(Path(__file__).resolve().parent.parent.parent.parent.joinpath(
                "gnss/bin/x86_64/convbin_2.4.3-34_x86_64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("rnx2rtkp")
            exp = str(Path(__file__).resolve().parent.parent.parent.parent.joinpath(
                "gnss/bin/x86_64/rnx2rtkp_2.4.3-34_x86_64_linux"))
            self.assertEqual(exp, path2bin)

            # Linux and aarch64
            mock_platform.system.return_value = "Linux"
            mock_platform.machine.return_value = "aarch64"
            path2bin = mcl_tools.get_path2bin("anubis")
            exp = str(Path(__file__).resolve().parent.parent.parent.parent.joinpath(
                "gnss/bin/aarch64/anubis_2.3_aarch64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("str2str")
            exp = str(Path(__file__).resolve().parent.parent.parent.parent.joinpath(
                "gnss/bin/aarch64/str2str_2.4.3-34_aarch64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("convbin")
            exp = str(Path(__file__).resolve().parent.parent.parent.parent.joinpath(
                "gnss/bin/aarch64/convbin_2.4.3-34_aarch64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("rnx2rtkp")
            exp = str(Path(__file__).resolve().parent.parent.parent.parent.joinpath(
                "gnss/bin/aarch64/rnx2rtkp_2.4.3-34_aarch64_linux"))
            self.assertEqual(exp, path2bin)

            # errors
            mock_platform.system.return_value = "bla"
            mock_platform.machine.return_value = "x86_64"
            with self.assertRaises(OSError) as msg:
                path2bin = mcl_tools.get_path2bin("anubis")
            self.assertEqual(str(msg.exception), "bla doesn't support")

            mock_platform.system.return_value = "Linux"
            mock_platform.machine.return_value = "bla bla"
            with self.assertRaises(OSError) as msg:
                path2bin = mcl_tools.get_path2bin("anubis")
            self.assertEqual(str(msg.exception), "bla bla doesn't support")

            mock_platform.system.return_value = "Linux"
            mock_platform.machine.return_value = "x86_64"
            with self.assertRaises(KeyError) as msg:
                path2bin = mcl_tools.get_path2bin("bla bla")

    def test_get_files_from_dir(self):
        with (patch("moncenterlib.gnss.tools.os.path.isdir") as mock_isdir,
              patch("moncenterlib.gnss.tools.os.path.isfile") as mock_isfile,
              patch("moncenterlib.gnss.tools.os.walk") as mock_walk,
              patch("moncenterlib.gnss.tools.os.listdir") as mock_listdir):
            mock_isdir.return_value = False
            with self.assertRaises(ValueError) as msg:
                result = mcl_tools.get_files_from_dir("/", False)
            self.assertEqual(str(msg.exception), "Path to dir is strange.")

            mock_isdir.return_value = True
            # with recursion
            mock_walk.return_value = [("/home/", None, ["file1.txt", "file2.txt"]),
                                      ("/home/dir1/", None, ["file3.txt", "file4.txt"])]
            result = mcl_tools.get_files_from_dir("/", True)
            self.assertEqual(['/home/file1.txt',
                              '/home/file2.txt',
                              '/home/dir1/file3.txt',
                              '/home/dir1/file4.txt'], result)

            # without recursion
            mock_listdir.return_value = ["/file1", "/file2", "/file3", "/file4"]
            mock_isfile.side_effect = [True, False, True, False]
            result = mcl_tools.get_files_from_dir("/", False)
            self.assertEqual(["/file1", "/file3"], result)

            mock_listdir.return_value = []
            result = mcl_tools.get_files_from_dir("/", False)
            self.assertEqual([], result)

    def test_get_start_date_from_nav(self):
        text = """
     2.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
teqc  2019Feb25     RGS-CENTRE          20220111 11:14:32UTCPGM / RUN BY / DATE
Linux 2.4.21-27.ELsmp|Opteron|gcc -static|Linux 64|=+       COMMENT
    1.1176D-08 -7.4506D-09 -5.9605D-08  1.1921D-07          ION ALPHA
    1.1674D+05 -2.2938D+05 -1.3107D+05  1.0486D+06          ION BETA
   -9.313225746155D-10-2.664535259100D-15   233472     2191 DELTA-UTC: A0,A1,T,W
                                                            END OF HEADER
 5 22  1  3  0  0  0.0-6.656209006906D-05-1.364242052659D-12 0.000000000000D+00
    6.900000000000D+01-1.697812500000D+02 4.081955744127D-09 2.089773613493D+00
   -8.817762136459D-06 5.895146168768D-03 1.028552651405D-05 5.153653125763D+03"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("2022-01-03", result)

        text = """
     2.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
teqc  2019Feb25     RGS-CENTRE          20220111 11:14:32UTCPGM / RUN BY / DATE
Linux 2.4.21-27.ELsmp|Opteron|gcc -static|Linux 64|=+       COMMENT
    1.1176D-08 -7.4506D-09 -5.9605D-08  1.1921D-07          ION ALPHA
    1.1674D+05 -2.2938D+05 -1.3107D+05  1.0486D+06          ION BETA
   -9.313225746155D-10-2.664535259100D-15   233472     2191 DELTA-UTC: A0,A1,T,W
                                                            END OF HEADER
 5 98  1  3  0  0  0.0-6.656209006906D-05-1.364242052659D-12 0.000000000000D+00
    6.900000000000D+01-1.697812500000D+02 4.081955744127D-09 2.089773613493D+00
   -8.817762136459D-06 5.895146168768D-03 1.028552651405D-05 5.153653125763D+03"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("1998-01-03", result)

        text = """bla bla"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("", result)

    def test_get_start_date_from_obs(self):
        text = """
CCRINEXO V2.4.1 LH  imvp                02-JAN-22 08:52     PGM / RUN BY / DATE
    30                                                      INTERVAL
  2022     1     1     0     0    0.000000      GPS         TIME OF FIRST OBS
                                                            END OF HEADER
 22  1  1  0  0  0.0000000  1 16G08G10G13G15G18G23G24G27R01R07R08R09
                                R15R22R23R24
  23474857.135    23474856.975   123361204.758 6      1068.561          36.000
  2347485"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_tools.get_start_date_from_obs(temp_file.name)
            self.assertEqual("2022-01-01", result)

        text = """bla bla"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_tools.get_start_date_from_obs(temp_file.name)
            self.assertEqual("", result)

    def test_get_marker_name(self):
        text = """
     2              OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE
NOVM                                                        MARKER NAME
12367M002                                                   MARKER NUMBER
                    SNIIM, NOVOSIBIRSK                      OBSERVER / AGENCY
00202               JPS LEGACY          2.6.0 OCT,24,2007   REC # / TYPE / VERS"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_tools.get_marker_name(temp_file.name)
            self.assertEqual("NOVM", result)
        
        text = """
     2              OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE
                                                            MARKER NAME
12367M002                                                   MARKER NUMBER
                    SNIIM, NOVOSIBIRSK                      OBSERVER / AGENCY
00202               JPS LEGACY          2.6.0 OCT,24,2007   REC # / TYPE / VERS"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_tools.get_marker_name(temp_file.name)
            self.assertEqual(Path(temp_file.name).name, result)


if __name__ == "__main__":
    main()
