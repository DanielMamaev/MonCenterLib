from collections import defaultdict
from datetime import datetime, timedelta
import os
from logging import Logger
import subprocess
import tempfile
from typeguard import typechecked
from gps_time import GPSTime
import moncenterlib.tools as mcl_tools
import moncenterlib.gnss.tools as mcl_gnss_tools


class RtkLibPost:

    @typechecked
    def __init__(self, logger: bool | Logger | None = None):
        self.logger = logger

        if self.logger in [None, False]:
            self.logger = mcl_tools.create_simple_logger("RtkLibPost", logger)

        self.__default_config = {
            'pos1-posmode': '0',
            'pos1-frequency':  '2',
            'pos1-soltype':  '0',
            'pos1-elmask':  '15',
            'pos1-snrmask_r':  'off',
            'pos1-snrmask_b':  'off',
            'pos1-snrmask_l1':  '0,0,0,0,0,0,0,0,0',
            'pos1-snrmask_l2':  '0,0,0,0,0,0,0,0,0',
            'pos1-snrmask_l5':  '0,0,0,0,0,0,0,0,0',
            'pos1-dynamics':  '0',
            'pos1-tidecorr':  '0',
            'pos1-ionoopt':  '1',
            'pos1-tropopt':  '1',
            'pos1-sateph':  '0',
            'pos1-posopt1':  '0',
            'pos1-posopt2':  '0',
            'pos1-posopt3':  '0',
            'pos1-posopt4':  '0',
            'pos1-posopt5':  '0',
            'pos1-posopt6':  '0',
            'pos1-exclsats':  '',
            'pos1-navsys':  '1',

            'pos2-armode':  '1',
            'pos2-gloarmode':  '1',
            'pos2-bdsarmode':  '1',
            'pos2-arthres':  '3',
            'pos2-arthres1':  '0.9999',
            'pos2-arthres2':  '0.25',
            'pos2-arthres3':  '0.1',
            'pos2-arthres4':  '0.05',
            'pos2-arlockcnt':  '0',
            'pos2-arelmask':  '0',
            'pos2-arminfix':  '10',
            'pos2-armaxiter':  '1',
            'pos2-elmaskhold':  '0',
            'pos2-aroutcnt':  '5',
            'pos2-maxage':  '30',
            'pos2-syncsol':  'off',
            'pos2-slipthres':  '0.05',
            'pos2-rejionno':  '30',
            'pos2-rejgdop':  '30',
            'pos2-niter':  '1',
            'pos2-baselen':  '0',
            'pos2-basesig':  '0',

            'out-solformat':  '0',
            'out-outhead':  '1',
            'out-outopt':  '1',
            'out-outvel':  '0',
            'out-timesys':  '0',
            'out-timeform':  '1',
            'out-timendec':  '3',
            'out-degform':  '0',
            'out-fieldsep':  '',
            'out-outsingle':  '0',
            'out-maxsolstd':  '0',
            'out-height':  '0',
            'out-geoid':  '0',
            'out-solstatic':  '0',
            'out-nmeaintv1':  '0',
            'out-nmeaintv2':  '0',
            'out-outstat':  '0',

            'stats-eratio1':  '100',
            'stats-eratio2':  '100',
            'stats-errphase':  '0.003',
            'stats-errphaseel':  '0.003',
            'stats-errphasebl':  '0',
            'stats-errdoppler':  '1',
            'stats-stdbias':  '30',
            'stats-stdiono':  '0.03',
            'stats-stdtrop':  '0.3',
            'stats-prnaccelh':  '10',
            'stats-prnaccelv':  '10',
            'stats-prnbias':  '0.0001',
            'stats-prniono':  '0.001',
            'stats-prntrop':  '0.0001',
            'stats-prnpos':  '0',
            'stats-clkstab':  '5E-12',

            'ant1-postype':  '0',
            'ant1-pos1':  '90',
            'ant1-pos2':  '0',
            'ant1-pos3':  '-6335367.62849036',
            'ant1-anttype':  '',
            'ant1-antdele':  '0',
            'ant1-antdeln':  '0',
            'ant1-antdelu':  '0',

            'ant2-postype':  '0',
            'ant2-pos1':  '90',
            'ant2-pos2':  '0',
            'ant2-pos3':  '-6335367.62849036',
            'ant2-anttype':  '',
            'ant2-antdele':  '0',
            'ant2-antdeln':  '0',
            'ant2-antdelu':  '0',
            'ant2-maxaveep':  '0',
            'ant2-initrst':  'off',

            'misc-timeinterp':  'off',
            'misc-sbasatsel':  '0',
            'misc-rnxopt1':  '',
            'misc-rnxopt2':  '',
            'misc-pppopt':  '',
            'file-satantfile':  '',
            'file-rcvantfile':  '',
            'file-staposfile':  '',
            'file-geoidfile':  '',
            'file-ionofile':  '',
            'file-dcbfile':  '',
            'file-eopfile':  '',
            'file-blqfile':  '',
            'file-tempdir':  '',
            'file-geexefile':  '',
            'file-solstatfile':  '',
            'file-tracefile':  ''
        }

    def get_default_config(self) -> dict:
        """
        Return variable __default_config. Default config isn't editable.
        In the future, you will manually configure this config and send it to the start method.
        See documentation RTKLIB, how to configuration.

        Returns:
            dict: default config for convbin of RTKLib
        """
        return self.__default_config.copy()

    @typechecked
    def scan_dirs(self, input_rnx: dict[str, str], recursion: bool = False) -> dict[str, list[str]]:
        self.logger.info("Scanning directories...")
        type_files = ['rover', 'base', 'nav', 'sp3', 'clk', 'erp']
        for k in input_rnx.keys():
            if k not in type_files:
                raise ValueError(f"Unidentified key {k}")

        scan_dirs = dict()
        for key, directory in input_rnx.items():
            list_files = mcl_tools.get_files_from_dir(directory, recursion)
            scan_dirs[key] = list_files
        return scan_dirs

    @typechecked
    def _get_start_date_from_sp3(self, file: str) -> str:
        date = ""
        with open(file, 'r', encoding="utf-8") as f:
            line = f.readline()
            sp3_version = line[:2]
            if sp3_version != '#c':
                raise Exception(f'Invalid sp3 version {sp3_version}')

            date = line[3:].split()[:3]
            date[1] = date[1].zfill(2)
            date[2] = date[2].zfill(2)
            date = '-'.join(date)
        return date

    @typechecked
    def _get_start_date_from_clk(self, file: str) -> str:
        date = ""
        with open(file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if 'RINEX VERSION' in line:
                    rinex_v = line.split()[0]
                    if not (rinex_v.startswith("2") or rinex_v.startswith("3")):
                        raise Exception(f"Unknown version rinex {rinex_v}")

                if 'GPS week' in line:
                    line = line.split()
                    gps_week = int(line[2])
                    day = int(line[4])
                    gps_time = GPSTime(gps_week, day * 24 * 60 * 60)
                    date = gps_time.to_datetime().strftime("%Y-%m-%d")
                    break
        return date

    @typechecked
    def _get_dates_from_erp(self, file: str) -> list:
        dates = []
        with open(file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            erp_version = lines[0].split()[1]
            if erp_version != "2":
                raise Exception(f"Unknown version erp {lines[0].split()[1]}")

            for line in lines[4:]:
                mjd = float(line.split()[0])
                # Offset between MJD 0 and Unix epoch (January 1, 1970)
                mjd_epoch_offset = 40587
                days_since_epoch = int(mjd) - mjd_epoch_offset
                date = datetime(1970, 1, 1) + timedelta(days=days_since_epoch)
                date = date.strftime("%Y-%m-%d")
                dates.append(date)
        return dates

    @typechecked
    def start(self, input_rnx: dict[str, str | list[str]], output: str, config: dict[str, str] | str,
              erp_from_config: bool = False, timeint: int = 0, recursion: bool = False,
              show_info_rtklib: bool = True) -> dict[str, list]:

        # - ionex https://cddis.nasa.gov/archive/gnss/products/ionex/ - все ок, добавляем, но не понятно работает или нет
        # - DСB https://cddis.nasa.gov/archive/gnss/products/bias/ - под вопросом, использовать полу допилинную версию или нет, хотя мб для обработки фагс пригодится
        # - fcb - в rtklib это не робит
        # - sbas - пока забываем про это

        if not os.path.isdir(output):
            self.logger.error("Output directory does not exist")
            raise ValueError("Output directory does not exist")

        if isinstance(config, str) and not os.path.isfile(config):
            self.logger.error("Config file does not exist")
            raise ValueError("Config file does not exist")

        inputs = dict()
        for k, v in input_rnx.items():
            if isinstance(v, str) and os.path.isfile(v):
                inputs[k] = [v]
            elif isinstance(v, str) and os.path.isdir(v):
                inputs = self.scan_dirs(input_rnx, recursion)
            elif isinstance(v, list):
                inputs = input_rnx

        self.logger.info("Starting match files")
        match_list = defaultdict(dict)
        for file in inputs.get('rover', []):
            try:
                date = mcl_gnss_tools.get_start_date_from_obs(file)
            except Exception as e:
                self.logger.error("Can't get date from rover file %s", file)
                self.logger.error(e)
                continue
            if "rovers" in match_list[date]:
                match_list[date]["rovers"] += [file]
            else:
                match_list[date]["rovers"] = [file]

        for file in inputs.get('base', []):
            try:
                date = mcl_gnss_tools.get_start_date_from_obs(file)
            except Exception as e:
                self.logger.error("Can't get date from base file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["base"] = file

        for file in inputs.get('nav', []):
            try:
                date = mcl_gnss_tools.get_start_date_from_nav(file)
            except Exception as e:
                self.logger.error("Can't get date from nav file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["nav"] = file

        for file in inputs.get('sp3', []):
            try:
                date = self._get_start_date_from_sp3(file)
            except Exception as e:
                self.logger.error("Can't get date from sp3 file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["sp3"] = file

        for file in inputs.get('clk', []):
            try:
                date = self._get_start_date_from_clk(file)
            except Exception as e:
                self.logger.error("Can't get date from clk file %s", file)
                self.logger.error(e)
                continue
            match_list[date]["clk"] = file

        for file in inputs.get('erp', []):
            try:
                dates = self._get_dates_from_erp(file)
            except Exception as e:
                self.logger.error("Can't get dates from erp file %s", file)
                self.logger.error(e)
                continue
            for date in dates:
                match_list[date]["erp"] = file

        pos_paths = []
        no_match = []
        with tempfile.NamedTemporaryFile() as temp_file:
            for path_files in match_list.values():
                if len(path_files) != len(input_rnx):
                    no_match.append(path_files)
                    continue

                # make configuration
                self.logger.info("Starting make configuration")
                with open(temp_file.name, 'w', encoding="utf-8") as config_temp_file:

                    if isinstance(config, str):
                        with open(config, "r", encoding="utf-8") as config_file:
                            if erp_from_config:
                                config_temp_file.write(config_file.read())
                            else:
                                text = config_file.readlines()
                                for i, line in enumerate(text):
                                    if "file-eopfile" in line:
                                        text[i] = f'file-eopfile={path_files.get("erp", "")}'
                                        config_temp_file.write(text[i] + '\n')
                                    else:
                                        config_temp_file.write(line + '\n')

                    elif isinstance(config, dict):
                        config["file-eopfile"] = path_files.get("erp", "")

                        for key, val in config.items():
                            config_temp_file.write(key + '=' + val + '\n')

                # make command
                for rvr in path_files.get("rovers", []):
                    cmd = [mcl_tools.get_path2bin("rnx2rtkp")]

                    cmd += ["-ti", str(timeint)]
                    cmd += ["-k", temp_file.name]

                    cmd += [rvr]
                    cmd += [path_files.get("base", "")]
                    cmd += [path_files.get("nav", "")]
                    cmd += [path_files.get("sp3", "")]
                    cmd += [path_files.get("clk", "")]

                    cmd = [i for i in cmd if i != ""]

                    path_end = os.path.join(output, os.path.basename(rvr)) + ".pos"
                    cmd += ["-o", path_end]

                    pos_paths.append(path_end)

                    self.logger.info("Run postprocessing %s", rvr)
                    if show_info_rtklib:
                        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL)
                    else:
                        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        output_dict = mcl_tools.files_check(pos_paths)
        output_dict["no_match"] = no_match
        return output_dict
