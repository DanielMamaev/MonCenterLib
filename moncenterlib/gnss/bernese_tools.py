import datetime
import itertools
import os
import re
import string
from pathlib import Path
import copy
from logging import Logger
import pandas as pd
from gps_time import GPSTime
from typeguard import typechecked
from moncenterlib.tools import create_simple_logger

class Bernese52:

    @typechecked
    def __init__(self, list_stations: dict[str, dict], logger: bool | Logger | None = None):
        """Initialize a Bernese 5.2 helper with station metadata.

        Args:
            list_stations (dict[str, dict]): Dictionary with station metadata.
                The `plate` field should use one of these 4-character plate
                codes: `PCFC`, `AFRC`, `ANTA`, `ARAB`, `AUST`, `CARB`,
                `COCO`, `EURA`, `INDI`, `NAZC`, `NOAM`, `SOAM`, `JUFU`,
                `PHIL`.
            logger (bool | Logger, optional): Logging configuration. If `None`,
                a default logger is created. If `False`, logging output is
                disabled. If a `Logger` instance is provided, that logger is
                used for all messages.
                Defaults to None.

        Examples:
            >>> list_stations = {
            ...     "BADG": {
            ...         "xyz": [-838281.8740, 3865775.9807, 4987625.1818],
            ...         "mark_num": "12338M002",
            ...         "plate": "EURA",
            ...         "rcv_type": "JAVAD TRE_3 DELTA",
            ...         "ant_type": "JAVRINGANT_DM   JVDM",
            ...         "ant_HEN": [0.0280, 0.0000, 0.0000],
            ...     },
            ...     "NOVM": {
            ...         "xyz": [452260.6946, 3635877.6761, 5203453.4274],
            ...         "mark_num": "12367M002",
            ...         "plate": "EURA",
            ...         "rcv_type": "JPS LEGACY",
            ...         "ant_type": "JPSREGANT_SD_E1 NONE",
            ...         "ant_HEN": [0.0800, 0.0000, 0.0000],
            ...     },
            ... }
            >>> bernese = Bernese52(list_stations)
        """

        self.logger = logger
        if self.logger in [None, False]:
            self.logger = create_simple_logger("Bernese_tools", logger)

        self.list_stations = copy.deepcopy(list_stations)

    @typechecked
    def make_bql_input(self) -> str:
        """Generate station coordinates for the ocean loading service.

        The returned text is formatted for direct insertion into:
        http://holt.oso.chalmers.se/loading/index-aside-2404271219.html

        Returns:
            str: Multiline string containing station names, marker numbers,
                and XYZ coordinates.

        Examples:
            >>> print(bernese.make_bql_input())
            ====== BQL ======
            BADG 12338M002               -838281.874     3865775.981     4987625.182
            NOVM 12367M002                452260.695     3635877.676     5203453.427
        """
        output = ''
        for name, val in self.list_stations.items():
            output += f"{name} {val['mark_num']:<19} {val["xyz"][0]:15.3f} {val["xyz"][1]:15.3f} {val["xyz"][2]:15.3f}\n"
        return output

    @typechecked
    def make_pld_info(self) -> str:
        """Generate station plate data for insertion into `EXAMPLE.PLD`.

        Returns:
            str: Multiline string containing station index, station name,
                marker number, and tectonic plate code in PLD table format.

        Examples:
            >>> print(bernese.make_PLD_info())
            ====== PLD ======
            1  BADG 12338M002                                              EURA
            2  NOVM 12367M002                                              EURA
        """
        output = ''
        count = 1
        for name, meta in self.list_stations.items():
            output += f"{count:3}  {name} {meta["mark_num"]:9s} \t {"":13}  {"":13}  {"":13} \t{"":6} {meta["plate"]}\n"
            count += 1
        return output

    @typechecked
    def make_sta_tab_001_info(self) -> str:
        """Generate records for table 001 in `EXAMPLE.STA`.

        Returns:
            str: Multiline string containing station names, marker numbers,
                fixed table code `001`, and wildcard station identifiers.

        Examples:
            >>> print(bernese.make_sta_tab_001_info())
            BADG 12338M002        001                                            BADG*
            NOVM 12367M002        001                                            NOVM*
        """
        output = ''
        for name, meta in self.list_stations.items():
            output += f"{name:4} {meta["mark_num"]:11}      {"001":3}  {"":40}  {name+"*":20}  {"":24}\n"
        return output

    @typechecked
    def make_sta_tab_002_info(self) -> str:
        """Generate records for table 002 in `EXAMPLE.STA`.

        Returns:
            str: Multiline string containing station name, marker number,
                receiver type, antenna type, placeholder dates, and antenna
                offsets formatted for table 002.

        Examples:
            >>> print(bernese.make_sta_tab_002_info())
            BADG 12338M002        001                                            JAVAD TRE_3 DELTA                           999999  JAVRINGANT_DM   JVDM                        999999    0.0000    0.0000    0.0280
            NOVM 12367M002        001                                            JPS LEGACY                                  999999  JPSREGANT_SD_E1 NONE                        999999    0.0000    0.0000    0.0800

        """
        output = ''
        for name, meta in self.list_stations.items():
            ant_neu = meta["ant_HEN"][::-1]
            output += f"{name:4} {meta["mark_num"]:11}      {"001":3}  {"":40}  {meta["rcv_type"]:20}  {"":20}  {"999999":6}  {meta['ant_type']:20}  {"":20}  {"999999":6}  {ant_neu[0]:8.4f}  {ant_neu[1]:8.4f}  {ant_neu[2]:8.4f}  {"":22}  {"":24}\n"
        return output

    @typechecked
    def make_clu_info(self) -> str:
        """Generate records for `EXAMPLE.CLU`.

        Returns:
            str: Multiline string containing station names, marker numbers,
                and the fixed cluster identifier `1`.

        Examples:
            >>> print(bernese.make_clu_info())
            BADG 12338M002      1
            NOVM 12367M002      1
        """
        output = ''
        for name, meta in self.list_stations.items():
            output += f"{name:4} {meta["mark_num"]:11}  {"1":>3}\n"
        return output

    @typechecked
    def make_abb_info(self) -> str:
        """Generate records for `EXAMPLE.ABB`.

        Returns:
            str: Multiline string containing station names, marker numbers,
                station abbreviations, and generated two-letter codes.

        Examples:
            >>> print(bernese.make_ABB_info())
            BADG 12338M002           BADG     AA
            NOVM 12367M002           NOVM     AB
        """
        output = ''
        alph = string.ascii_uppercase
        combinations = [''.join(pair) for pair in itertools.product(alph, repeat=2)]
        count = 0
        for name, meta in self.list_stations.items():
            output += f"{name:4} {meta["mark_num"]:11}         {name:4}     {combinations[count]:2}     {"":39}\n"
            count += 1
        return output

    @typechecked
    def make_receiver_info(self, file_receiver: str):
        """Check receiver definitions in a `RECEIVER.` file.

        If a receiver type from `self.list_stations` is missing in the input
        file, this method adds a formatted block that can be inserted into the
        `RECEIVER.` file.

        Args:
            file_receiver (str): Path to the Bernese `RECEIVER.` file.

        Returns:
            str: Formatted text for missing receiver entries. Returns an empty
                string if all receiver types are already present.

        Examples:
            >>> print(bernese.make_receiver_info("/path/to/RECEIVER."))
            U-BLOX ZED-F9P-01B-0   2     C1    L1:     1     GR
                                         X2    L2:     1
        """

        missing_receivers = set()
        with open(file_receiver, "r", encoding="utf-8") as f:
            text = f.read()
            for _, val in self.list_stations.items():
                if val['rcv_type'] in text:
                    self.logger.info("%s - OK", val['rcv_type'])
                else:
                    missing_receivers.add(val['rcv_type'])
                    self.logger.warning("%s - MISSING", val['rcv_type'])

        output = ""
        for rec in missing_receivers:
            output += f"{rec:20}   {2}     C1    L1:     1     GR\n"
            output += f"{'':20}   {" "}     X2    L2:     1     \n\n"
        return output

    @typechecked
    def apriopy_crd_for_atl(self, ref_system: str = "IGS20") -> str:
        """Generate coordinate records for creating an ATL file in Bernese 5.2.

        The returned text can be inserted into a coordinate file when creating
        an ATL file in the Bernese 5.2 GUI. As an alternative, an existing
        `EXAMPLE.CRD` file may be used.

        Args:
            ref_system (str, optional): Reference system name written to the
                header and station records. Defaults to "IGS20".

        Returns:
            str: Multiline coordinate table with header, station names, marker
                numbers, XYZ coordinates, and the selected reference system.
        """

        output = f"{ref_system}: coordinate list                                           23-AUG-22 08:30\n" \
                 "--------------------------------------------------------------------------------\n"\
                 f"LOCAL GEODETIC DATUM: {ref_system}           EPOCH: 2015-01-01 00:00:00\n\n" \
                 "NUM  STATION NAME           X (M)          Y (M)          Z (M)     FLAG     SYSTEM\n\n"
        count = 1
        for name, val in self.list_stations.items():
            output += f"{count:3}  {name} {val['mark_num']:9}   {val['xyz'][0]:14} {val['xyz'][1]:14} {val['xyz'][2]:14}    {ref_system}\n"
            count += 1
        return output

    @typechecked
    def rename_rnx3_to_rnx2(self, input_path: str, service: str):
        """Rename product files from RINEX 3 naming to Bernese/RINEX 2 style.

        The method accepts either a single file or a directory with files and
        renames supported product types (`SP3`, `ION`, `CLK`, `ERP`) according
        to GPS week and day. The renaming rules depend on the analysis center
        specified by `service`.

        Args:
            input_path (str): Path to a file or directory containing product
                files to rename.
            service (str): Analysis center code used for special renaming
                rules. Supported values in the current implementation are
                `"IGS"` and `"COD"`.

        Raises:
            FileNotFoundError: Raised if `input_path` does not exist.

        Examples:
            >>> bernese.rename_rnx3_to_rnx2("/path/to/products", "IGS")
        """
        products = ["SP3", "ION", "CLK", "ERP"]

        list_files = []
        if os.path.isdir(input_path):
            list_files = [os.path.join(input_path, f) for f in os.listdir(input_path)]
        elif os.path.isfile(input_path):
            list_files = [input_path]
        else:
            raise FileNotFoundError(f"Input path does not exist: {input_path}")

        for file in list_files:
            suffix = ""
            temp_suffix = Path(file).suffix[1:]

            if temp_suffix in products:
                suffix = f".{temp_suffix}"
            else:
                self.logger.warning("Unknown file type: %s", temp_suffix)
                continue

            name_file = os.path.basename(file)
            try:
                dt = datetime.datetime.strptime(name_file.split("_")[1][:7], "%Y%j")
            except Exception:
                self.logger.warning("Failed to parse date from file: %s", file)
                continue

            gps_week = GPSTime.from_datetime(dt).week_number
            gps_day = int(GPSTime.from_datetime(dt).time_of_week / (24 * 60 * 60))

            new_name = name_file[:3] + str(gps_week) + str(gps_day) + suffix

            if service == "IGS":
                if suffix == ".ERP":
                    new_name = name_file[:3] + str(gps_week) + "7" + suffix

                if suffix == ".CLK":
                    if name_file.split("_")[3] != "05M":
                        new_name += f"_{name_file.split("_")[3]}"

            elif service == "COD":
                if suffix == ".CLK" and name_file.split("_")[3] == "05S":
                    new_name += "_05S"

            new_file = os.path.join(os.path.dirname(file), new_name)
            self.logger.info("Rename %s to %s", file, new_file)
            os.rename(file, new_file)

    @typechecked
    def parse_rnx2snx_crd(self, input_path: str) -> pd.DataFrame:
        """Parse RNX2SNX coordinate output into a pandas DataFrame.

        Args:
            input_path (str): Path to a single RNX2SNX output file or to a
                directory containing such files.

        Raises:
            FileNotFoundError: Raised if `input_path` does not exist.

        Returns:
            pd.DataFrame: DataFrame with parsed coordinate records sorted by
                `Date` and `ID`.

        Examples:
            >>> df = bernese.parse_RNX2SNX_CRD("/path/to/rnx2snx_output")
            >>> df.head()
        """
        alph = {
            "A": datetime.time(0, 59, 59),
            "B": datetime.time(1, 59, 59),
            "C": datetime.time(2, 59, 59),
            "D": datetime.time(3, 59, 59),
            "E": datetime.time(4, 59, 59),
            "F": datetime.time(5, 59, 59),
            "G": datetime.time(6, 59, 59),
            "H": datetime.time(7, 59, 59),
            "I": datetime.time(8, 59, 59),
            "J": datetime.time(9, 59, 59),
            "K": datetime.time(10, 59, 59),
            "L": datetime.time(11, 59, 59),
            "M": datetime.time(12, 59, 59),
            "N": datetime.time(13, 59, 59),
            "O": datetime.time(14, 59, 59),
            "P": datetime.time(15, 59, 59),
            "Q": datetime.time(16, 59, 59),
            "R": datetime.time(17, 59, 59),
            "S": datetime.time(18, 59, 59),
            "T": datetime.time(19, 59, 59),
            "U": datetime.time(20, 59, 59),
            "V": datetime.time(21, 59, 59),
            "W": datetime.time(22, 59, 59),
            "X": datetime.time(23, 59, 59),
            "0": datetime.time(23, 59, 59),
        }

        list_files = []
        if os.path.isdir(input_path):
            list_files = [os.path.join(input_path, f) for f in os.listdir(input_path)]
        elif os.path.isfile(input_path):
            list_files = [input_path]
        else:
            raise FileNotFoundError(f"Input path does not exist: {input_path}")

        df = []
        for file in list_files:
            name_file = os.path.basename(file)
            dt = datetime.datetime.strptime(name_file.split("_")[1][:5], "%y%j")
            start_hour = name_file.split(".")[0][-1]
            dt = dt.replace(hour=alph[start_hour].hour, minute=alph[start_hour].minute, second=alph[start_hour].second)

            pattern = re.compile(r'^\s*\d+\s+\S+\s+\S+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+([A-Z]+)\s*$')
            ts: list[list[str]] = []

            with open(file, encoding='utf-8') as f:
                for line in f:
                    if pattern.match(line):
                        ts.append(line.strip())
            if not ts:
                self.logger.error("Error while parsing file: %s.", file)
                continue

            ts = [i.split() + [str(dt)] for i in ts]

            df+=ts

        df = pd.DataFrame(df, columns=["ID", "Station", "Marker", "X", "Y", "Z", "Flag", "Date"])
        df["ID"] = df["ID"].astype(int)
        df["Station"] = df["Station"].astype(str)
        df["Marker"] = df["Marker"].astype(str)
        df["X"] = df["X"].astype(float)
        df["Y"] = df["Y"].astype(float)
        df["Z"] = df["Z"].astype(float)
        df["Flag"] = df["Flag"].astype(str)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(by=["Date", "ID"], ascending=[True, True]).reset_index(drop=True)

        return df
