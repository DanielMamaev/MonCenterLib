import os
from progress.bar import IncrementalBar
from pathlib import Path
import string
import random
from pprint import pprint


class RtkLibPost:
    def __init__(self):
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

    @property
    def DEFAULT_CONFIG(self):
        return self.__default_config.copy()

    def __check_type(self, arg: object, type_check: object, name: str) -> None:
        if not type(arg) is type_check:
            raise TypeError(
                f"The type of the '{name}' variable should be {type_check}")

    def __check_files(self, files: list) -> dict:
        output_check = {
            'done': [],
            'error': []
        }

        for file in files:
            direct = Path(file)
            if direct.exists():
                output_check['done'].append(file)
            else:
                output_check['error'].append(file)

        return output_check

    def scan_dir(self, input: dict, recursion: bool = False) -> list:
        type_files = ['rover', 'base', 'nav', 'sp3', 'clk']
        for k, v in input.items():
            if k not in type_files:
                raise Exception(f"Unidentified key {k}")
            self.__check_type(v, str, v)

        scan_dirs = dict()
        for key, dir in input.items():
            if recursion:
                for root, _, files in os.walk(dir):
                    for file in files:
                        path = os.path.join(root, file)
                        if key in scan_dirs:
                            scan_dirs[key].append(path)
                        else:
                            scan_dirs[key] = [path]
            else:
                temp_lst = []
                for file in os.listdir(dir):
                    if os.path.isfile(os.path.join(dir, file)):
                        temp_lst.append(os.path.join(dir, file))
                scan_dirs[key] = temp_lst
        return scan_dirs
                    

    def start(self, inputs: dict, output: str, config: dict, timeint: int = 0):

        # check type
        self.__check_type(inputs, dict, 'inputs')
        self.__check_type(config, dict, 'config')
        self.__check_type(output, str, 'output')
        self.__check_type(timeint, int, 'timeint')
        for k, v in config.items():
            self.__check_type(v, str, k)

        for k, v in inputs.items():
            if type(v) == str and os.path.isfile(v):
                inputs[k] = [v]
            elif type(v) == list:
                pass
            else:
                raise TypeError("You must first use the scan_dirs function and then pass the result to the start function. Or specify the paths to a specific file.")

        match_list = dict()
        for file in inputs.get('rover', []):
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'TIME OF FIRST OBS' in line:
                        date = line.split()[:3]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date = '/'.join(date)

                        if date in match_list:
                            match_list[date] += [file]
                        else:
                            match_list[date] = [file]
                        break
                    elif 'END OF HEADER' in line:
                        break

        for file in inputs.get('base', []):
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'TIME OF FIRST OBS' in line:
                        date = line.split()[:3]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date = '/'.join(date)

                        if date in match_list:
                            match_list[date] += [file]
                        else:
                            match_list[date] = [file]
                        break
                    elif 'END OF HEADER' in line:
                        break

        for file in inputs.get('nav', []):
            flag_end = False
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'END OF HEADER' in line:
                        flag_end = True
                    elif flag_end:
                        date = line.split()[1:4]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date[0] = '20' + \
                            date[0] if not len(date[0]) == 4 else date[0]
                        date = '/'.join(date)

                        if date in match_list:
                            match_list[date] += [file]
                        else:
                            match_list[date] = [file]
                        break

        for file in inputs.get('sp3', []):
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if line[0] == "*":
                        date = line.split()[1:4]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date[0] = '20' + \
                            date[0] if not len(date[0]) == 4 else date[0]
                        date = '/'.join(date)

                        if date in match_list:
                            match_list[date] += [file]
                        else:
                            match_list[date] = [file]
                        break

        for file in inputs.get('clk', []):
            flag_end = False
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'END OF HEADER' in line:
                        flag_end = True
                    elif flag_end:
                        date = line.split()[2:5]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date[0] = '20' + \
                            date[0] if not len(date[0]) == 4 else date[0]
                        date = '/'.join(date)

                        if date in match_list:
                            match_list[date] += [file]
                        else:
                            match_list[date] = [file]
                        break
        # sbas_fcb_ionex

        # создание временного файла конфига
        path_conf = ''
        while True:
            folder_conf = os.path.join(
                Path(__file__).resolve().parent.parent.parent, 'conf')
            alphabet = string.ascii_letters + string.digits
            name_conf = ''.join(random.choice(alphabet) for i in range(6))
            path_conf = os.path.join(folder_conf, name_conf) + '.conf'
            direct = Path(path_conf)
            if not direct.exists():
                break

        f = open(path_conf, 'w')
        for key, val in config.items():
            f.write(key + '=' + val + '\n')
        f.close()

        pos_paths = []
        bar = IncrementalBar('Progress', max=len(
            match_list), suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
        bar.start()
        print('')

        for _, value in match_list.items():
            command = f'-ti {timeint} ' if timeint != '' else ''
            command += f"-k '{path_conf}' "

            for path_file in value:
                command += f"'{path_file}'" + ' '

            path_end = os.path.join(output, os.path.basename(value[0]))
            command += f"-o '{path_end}.pos'"

            pos_paths.append(
                f"{os.path.join(output, os.path.basename(value[0]))}.pos")

            cmd = str(Path(__file__).resolve().parent.parent.parent)
            cmd += "/bin/RTKLIB-2.4.3-b34/app/consapp/rnx2rtkp/gcc/rnx2rtkp "
            cmd += command
            os.system(cmd)
            #print(cmd)

            bar.next()
            print('')

        bar.finish()
        print('')
        os.remove(path_conf)
        return self.__check_files(pos_paths)
