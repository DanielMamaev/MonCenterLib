from pathlib import Path
import tempfile
from unittest import TestCase, main
from unittest.mock import patch
import moncenterlib.gnss.tools as mcl_gnss_tools


class TestTools(TestCase):

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
            result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("2022-01-03", result)

        # check date between 0 and 79
        text = """
     2.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
                                                            END OF HEADER
 5 00  1  3  0  0  0.0-6.656209006906D-05-1.364242052659D-12 0.000000000000D+00"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("2000-01-03", result)

        text = """
     2.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
                                                            END OF HEADER
 5 79  1  3  0  0  0.0-6.656209006906D-05-1.364242052659D-12 0.000000000000D+00"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("2079-01-03", result)

        text = """
     2.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
                                                            END OF HEADER
 5 30  1  3  0  0  0.0-6.656209006906D-05-1.364242052659D-12 0.000000000000D+00"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("2030-01-03", result)

        # check date between 80 and 99
        text = """
     2.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
                                                            END OF HEADER
 5 80  1  3  0  0  0.0-6.656209006906D-05-1.364242052659D-12 0.000000000000D+00"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("1980-01-03", result)

        text = """
     2.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
                                                            END OF HEADER
 5 99  1  3  0  0  0.0-6.656209006906D-05-1.364242052659D-12 0.000000000000D+00"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("1999-01-03", result)

        text = """
     2.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
                                                            END OF HEADER
 5 90  1  3  0  0  0.0-6.656209006906D-05-1.364242052659D-12 0.000000000000D+00"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("1990-01-03", result)

        # check some_text
        text = """bla bla"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("", result)

        # check rinex_version
        text = """
     2.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
teqc  2019Feb25     RGS-CENTRE          20220111 11:14:32UTCPGM / RUN BY / DATE
"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("", result)

        text = """
     3.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
teqc  2019Feb25     RGS-CENTRE          20220111 11:14:32UTCPGM / RUN BY / DATE
"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("", result)

        text = """
     4.11           N: GPS NAV DATA                         RINEX VERSION / TYPE
teqc  2019Feb25     RGS-CENTRE          20220111 11:14:32UTCPGM / RUN BY / DATE
"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            with self.assertRaises(Exception) as msg:
                result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual(str(msg.exception), "Unknown version rinex 4.11")

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
            result = mcl_gnss_tools.get_start_date_from_obs(temp_file.name)
            self.assertEqual("2022-01-01", result)

        text = """bla bla"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_obs(temp_file.name)
            self.assertEqual("", result)

        # check rinex_version
        text = """
     2              OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE
teqc  2019Feb25     RGS-CENTRE          20220111 11:14:32UTCPGM / RUN BY / DATE
"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_obs(temp_file.name)
            self.assertEqual("", result)

        text = """
     3              OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE
teqc  2019Feb25     RGS-CENTRE          20220111 11:14:32UTCPGM / RUN BY / DATE
"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_start_date_from_nav(temp_file.name)
            self.assertEqual("", result)

        text = """
     4              OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE
teqc  2019Feb25     RGS-CENTRE          20220111 11:14:32UTCPGM / RUN BY / DATE
"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            with self.assertRaises(Exception) as msg:
                result = mcl_gnss_tools.get_start_date_from_obs(temp_file.name)
            self.assertEqual(str(msg.exception), "Unknown version rinex 4")

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
            result = mcl_gnss_tools.get_marker_name(temp_file.name)
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
            result = mcl_gnss_tools.get_marker_name(temp_file.name)
            self.assertEqual(Path(temp_file.name).name, result)

        # check rinex_version
        text = """
     2              OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE
NOVM                                                        MARKER NAME
12367M002                                                   MARKER NUMBER
"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_marker_name(temp_file.name)
            self.assertEqual("NOVM", result)

        text = """
     3              OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE
NOVM                                                        MARKER NAME
12367M002                                                   MARKER NUMBER
"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            result = mcl_gnss_tools.get_marker_name(temp_file.name)
            self.assertEqual("NOVM", result)

        text = """
     4              OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE
NOVM                                                        MARKER NAME
12367M002                                                   MARKER NUMBER
"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, "w", encoding="utf-8") as f:
                f.write(text)
            with self.assertRaises(Exception) as msg:
                result = mcl_gnss_tools.get_marker_name(temp_file.name)
            self.assertEqual(str(msg.exception), "Unknown version rinex 4")


if __name__ == "__main__":
    main()
