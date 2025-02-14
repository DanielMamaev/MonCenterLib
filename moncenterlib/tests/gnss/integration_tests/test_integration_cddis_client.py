import tempfile
from unittest import TestCase, main
from moncenterlib.gnss.cddis_client import CDDISClient


class TestCddisClient(TestCase):
    def setUp(self) -> None:
        self.cddis_cli = CDDISClient(False)

    def test_get_daily_multi_gnss_brd_eph(self):
        query = {
            "start": "2020-12-31",
            "end": "2021-01-01"
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.cddis_cli.get_daily_multi_gnss_brd_eph(temp_dir, query)

            expected = [f'{temp_dir}/BRDC00IGS_R_20203660000_01D_MN.rnx',
                        f'{temp_dir}/BRDC00IGS_R_20210010000_01D_MN.rnx']
            self.assertEqual(expected, result["done"])

    def test_get_daily_30s_data(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            query = {
                "start": "2020-12-31",
                "end": "2021-01-01",
                "station": "NOVM",
                "type": "O",
                "rinex_v": "auto"
            }

            result = self.cddis_cli.get_daily_30s_data(temp_dir, query)
            expected = [f'{temp_dir}/novm3660.20o',
                        f'{temp_dir}/novm0010.21o']
            self.assertEqual(expected, result["done"])

        with tempfile.TemporaryDirectory() as temp_dir:
            query = {
                "start": "2022-12-30",
                "end": "2022-12-30",
                "station": "GODN",
                "type": "N",
                "rinex_v": "3"
            }

            result = self.cddis_cli.get_daily_30s_data(temp_dir, query)

            self.assertEqual([f"{temp_dir}/GODN00USA_R_20223640000_01D_GN.rnx"], result["done"])

        with tempfile.TemporaryDirectory() as temp_dir:
            # rinex version 2
            query = {
                "dates": {"start": "2022-12-30", "end": "2022-12-30"},
                "station": "GODN",
                "type": "N",
                "rinex_v": "2"
            }

            result = self.cddis_cli.get_daily_30s_data(temp_dir, query)

            self.assertEqual([f"{temp_dir}/godn3640.22n"], result["done"])

    def test_get_precise_orbits(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            query = {
                "start": "2020-12-31",
                "end": "2021-01-01"
            }

            result = self.cddis_cli.get_precise_orbits(temp_dir, query)
            expected = [f'{temp_dir}/igs21384.sp3',
                        f'{temp_dir}/igs21385.sp3']
            self.assertEqual(expected, result["done"])

    def test_get_earth_orientation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            query = {
                "start": "2020-12-30",
                "end": "2021-01-10"
            }

            result = self.cddis_cli.get_earth_orientation(temp_dir, query)
            expected = [f'{temp_dir}/igs21387.erp',
                        f'{temp_dir}/igs21397.erp',
                        f'{temp_dir}/igs21407.erp',]
            self.assertEqual(expected, result["done"])

    def test_get_clock_30s(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            query = {
                "start": "2020-12-31",
                "end": "2021-01-01"
            }

            result = self.cddis_cli.get_clock_30s(temp_dir, query)
            expected = [f'{temp_dir}/igs21384.clk_30s',
                        f'{temp_dir}/igs21385.clk_30s']
            self.assertEqual(expected, result["done"])

    def test_get_clock_5m(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            query = {
                "start": "2020-12-31",
                "end": "2021-01-01"
            }

            result = self.cddis_cli.get_clock_5m(temp_dir, query)
            expected = [f'{temp_dir}/igs21384.clk',
                        f'{temp_dir}/igs21385.clk']
            self.assertEqual(expected, result["done"])

    def test_archives(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            query = {
                "start": "2020-12-30",
                "end": "2020-12-30"
            }
            result = []
            result.append(self.cddis_cli.get_clock_5m(temp_dir, query, unpack=False)["done"][0])
            result.append(self.cddis_cli.get_clock_30s(temp_dir, query, unpack=False)["done"][0])
            result.append(self.cddis_cli.get_precise_orbits(temp_dir, query, unpack=False)["done"][0])
            result.append(self.cddis_cli.get_earth_orientation(temp_dir, query, unpack=False)["done"][0])
            result.append(self.cddis_cli.get_daily_multi_gnss_brd_eph(temp_dir, query, unpack=False)["done"][0])

            query = {
                "dates": {"start": "2022-12-30", "end": "2022-12-30"},
                "station": "GODN",
                "type": "O",
                "rinex_v": "auto"
            }

            result.append(self.cddis_cli.get_daily_30s_data(temp_dir, query, unpack=False)["done"][0])

            expected = [f"{temp_dir}/igs21383.clk.Z",
                        f"{temp_dir}/igs21383.clk_30s.Z",
                        f"{temp_dir}/igs21383.sp3.Z",
                        f"{temp_dir}/igs21387.erp.Z",
                        f"{temp_dir}/BRDC00IGS_R_20203650000_01D_MN.rnx.gz",
                        f"{temp_dir}/godn3640.22o.gz"]
            self.assertEqual(expected, result)


if __name__ == "__main__":
    main()
