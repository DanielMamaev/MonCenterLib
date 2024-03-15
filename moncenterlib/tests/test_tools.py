from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch
import moncenterlib.tools as mcl_tools


class TestTools(TestCase):
    def test_get_path2bin(self):
        with patch("moncenterlib.tools.platform") as mock_platform:
            # Linux and x86_64
            mock_platform.system.return_value = "Linux"
            mock_platform.machine.return_value = "x86_64"
            path2bin = mcl_tools.get_path2bin("anubis")
            exp = str(Path(__file__).resolve().parent.parent.joinpath(
                "gnss/bin/x86_64/anubis_2.3_x86_64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("str2str")
            exp = str(Path(__file__).resolve().parent.parent.joinpath(
                "gnss/bin/x86_64/str2str_2.4.3-34_x86_64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("convbin")
            exp = str(Path(__file__).resolve().parent.parent.joinpath(
                "gnss/bin/x86_64/convbin_2.4.3-34_x86_64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("rnx2rtkp")
            exp = str(Path(__file__).resolve().parent.parent.joinpath(
                "gnss/bin/x86_64/rnx2rtkp_2.4.3-34_x86_64_linux"))
            self.assertEqual(exp, path2bin)

            # Linux and aarch64
            mock_platform.system.return_value = "Linux"
            mock_platform.machine.return_value = "aarch64"
            path2bin = mcl_tools.get_path2bin("anubis")
            exp = str(Path(__file__).resolve().parent.parent.joinpath(
                "gnss/bin/aarch64/anubis_2.3_aarch64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("str2str")
            exp = str(Path(__file__).resolve().parent.parent.joinpath(
                "gnss/bin/aarch64/str2str_2.4.3-34_aarch64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("convbin")
            exp = str(Path(__file__).resolve().parent.parent.joinpath(
                "gnss/bin/aarch64/convbin_2.4.3-34_aarch64_linux"))
            self.assertEqual(exp, path2bin)

            path2bin = mcl_tools.get_path2bin("rnx2rtkp")
            exp = str(Path(__file__).resolve().parent.parent.joinpath(
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

    def test_get_files_from_dir(self):
        with (patch("moncenterlib.tools.os.path.isdir") as mock_isdir,
              patch("moncenterlib.tools.os.path.isfile") as mock_isfile,
              patch("moncenterlib.tools.os.walk") as mock_walk,
              patch("moncenterlib.tools.os.listdir") as mock_listdir):
            mock_isdir.return_value = False
            with self.assertRaises(ValueError) as msg:
                result = mcl_tools.get_files_from_dir("/", False)
            self.assertEqual(str(msg.exception), "Path '/' to dir is strange.")

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


if __name__ == "__main__":
    main()
