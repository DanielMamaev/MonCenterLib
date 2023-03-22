import docker
import os
from pathlib import Path
import string
import random
from progress.bar import IncrementalBar
from collections import Counter


class SoftwareDocker:
    """
    This class is designed to interact with various Linux programs
    using Docker technology. Thanks to this implementation, it becomes
    possible to work with programs that were written under Linux
    the system, both in Windows OS and Linux OS. The following programs
    are currently present in the Docker image: RTKLib, CATS.
    """

    def __init__(self) -> None:
        self.client = docker.from_env()

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

    def __check_type(self, arg: object, type_check: object, name: str) -> None:
        if not type(arg) is type_check:
            raise TypeError(f"The type of the '{name}' variable should be {type_check}")

    def _run_container(self, name: str, paths: dict, daemon: bool = False,
                       command: str = '') -> None:

        # check type
        self.__check_type(name, str, 'name')
        self.__check_type(paths, dict, 'paths')
        self.__check_type(daemon, bool, 'daemon')
        self.__check_type(command, str, 'command')

        volumes = [f"{os.path.join(Path(__file__).resolve().parent.parent, 'conf')}:/app/conf/"]

        for key, val in paths.items():
            if name == 'str2str':
                volumes.append(f'{val}:/app/output_str2str')
            
            elif name == 'convbin':
                if key == 'output':
                    volumes.append(f'{val}:/app/output_convbin')
                else:
                    volumes.append(f'{val}:/app/input_convbin')
            
            elif name == 'rnx2rtkp':
                if key == 'output':
                    volumes.append(f'{val}:/app/output_rnx2rtkp')
                else:
                    volumes.append(f'{val}:/app/input_rnx2rtkp_{key}')

        name_container = ''
        while True:
            name_container = f'moncenterlib_{name}_{random.randint(0, 10000)}'
            try:
                self.client.containers.get(name_container)
            except Exception:
                break

        restart_policy = {}
        auto_remove = True
        detach = False
        if daemon:
            restart_policy = {'Name': 'always'}
            auto_remove = False
            command = "tail -F /dev/null"
            detach = True
            name_container = f'moncenterlib_{name}_daemon'
        try:
            self.client.containers.run(f"danielmamaev/moncenterlib_{name}",
                                       name=name_container,
                                       command=command,
                                       volumes=volumes,
                                       restart_policy=restart_policy,
                                       auto_remove=auto_remove,
                                       detach=detach
                                       )
        except docker.errors.APIError as e:
            print(e)

        return name_container

    def _stop_container(self):
        pass

    def convbin(self, paths: dict, config: dict, recursion: bool = False,
                todaemon: bool = False) -> dict:

        # check type
        self.__check_type(paths, dict, 'paths')
        self.__check_type(config, dict, 'config')
        self.__check_type(recursion, bool, 'recursion')
        self.__check_type(todaemon, bool, 'todaemon')

        keys = ['input', 'output']
        for k, v in paths.items():
            if k not in keys:
                raise Exception(f"Неопознанный ключ '{k}'")
            self.__check_type(v, str, v)
        
        for k, v in config.items():
            self.__check_type(v, str, k)

        # составляем список файлов из папки
        input_files = []
        if recursion:
            for root, _, files in os.walk(paths['input']):
                for file in files:
                    path = os.path.join(root, file)
                    input_files.append(path)
        else:
            input_files = [os.path.join(paths['input'], file) for file in os.listdir(paths['input'])]

        # запуск конвертации
        output_files = []
        bar = IncrementalBar('Progress', max=len(input_files), suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')

        for file in input_files:
            command = ''

            command += f"-r {config['format']} "
            command += f"-v {config['rinex_v']} "

            if not config['start_time'] == '':
                command += f"-ts {config['start_time']} "

            if not config['end_time'] == '':
                command += f"-te {config['end_time']} "

            command += f"-ti {config['interval']} "

            command += f"-f {config['freq']} "

            full_sys = {'G', 'R', 'E', 'J', 'S', 'C', 'I'}
            sys = set(config['system'].split(','))
            for i in full_sys - sys:
                command += f"-y {i} "

            namef = os.path.basename(file)
            if not Path(namef).suffix == '':
                namef = namef.rsplit(Path(namef).suffix, 1)[0]

            if config['output_o'] == '1':
                out = f"/app/output_convbin/{namef}.o"
                command += f"-o '{out}' "
                output_files.append(os.path.join(paths['output'],
                                    f"{namef}.o"))
            if config['output_n'] == '1':
                out = f"/app/output_convbin/{namef}.n"
                command += f"-n '{out}' "
                output_files.append(os.path.join(paths['output'],
                                    f"{namef}.n"))
            if config['output_g'] == '1':
                out = f"/app/output_convbin/{namef}.g"
                command += f"-g '{out}' "
                output_files.append(os.path.join(paths['output'],
                                    f"{namef}.g"))
            if config['output_h'] == '1':
                out = f"/app/output_convbin/{namef}.h"
                command += f"-h '{out}' "
                output_files.append(os.path.join(paths['output'],
                                    f"{namef}.h"))
            if config['output_q'] == '1':
                out = f"/app/output_convbin/{namef}.q"
                command += f"-q '{out}' "
                output_files.append(os.path.join(paths['output'],
                                    f"{namef}.q"))
            if config['output_l'] == '1':
                out = f"/app/output_convbin/{namef}.l"
                command += f"-l '{out}' "
                output_files.append(os.path.join(paths['output'],
                                    f"{namef}.l"))
            if config['output_b'] == '1':
                out = f"/app/output_convbin/{namef}.b"
                command += f"-b '{out}' "
                output_files.append(os.path.join(paths['output'],
                                    f"{namef}.b"))
            if config['output_i'] == '1':
                out = f"/app/output_convbin/{namef}.i"
                command += f"-i '{out}' "
                output_files.append(os.path.join(paths['output'],
                                    f"{namef}.i"))
            if config['output_s'] == '1':
                out = f"/app/output_convbin/{namef}.s"
                command += f"-s '{out}' "
                output_files.append(os.path.join(paths['output'],
                                    f"{namef}.s"))

            if config['other_od'] == '1':
                command += f"-od "
            if config['other_os'] == '1':
                command += f"-os "
            if config['other_oi'] == '1':
                command += f"-oi "
            if config['other_ot'] == '1':
                command += f"-ot "
            if config['other_ol'] == '1':
                command += f"-ol "
            if config['other_halfc'] == '1':
                command += f"-halfc "

            command += f"-hc '{config['comment']}' "

            command += f"-hm '{config['marker_name']}' "
            command += f"-hn '{config['marker_number']}' "
            command += f"-ht '{config['marker_type']}' "

            command += f"-ho '{config['about_name']}/{config['about_agency']}' "
            command += f"-hr '{config['receiver_number']}/{config['receiver_type']}/{config['receiver_version']}' "
            command += f"-ha '{config['antenna_number']}/{config['antenna_type']}' "
            command += f"-hp '{config['approx_position_x']}/{config['approx_position_y']}/{config['approx_position_z']}' "
            command += f"-hd '{config['antenna_delta_h']}/{config['antenna_delta_e']}/{config['antenna_delta_n']}' "

            path_docker = file.replace(paths['input'], '')
            path_docker = '/app/input_convbin/' + path_docker
            command += f"'{path_docker}'"

            cmd = f'/bin/bash -c "exec -a convbin ./convbin {command}"'
            if not todaemon:
                self._run_container('convbin', paths, command=cmd)
            else:
                cont = self.client.containers.get('moncenterlib_convbin_daemon')
                cont.exec_run(cmd, detach=False)
            bar.next()
            # переименование файлов по стандарту ринекса, впланах

        bar.finish()
        return self.__check_files(output_files)

    def rnx2rtkp(self, paths: dict, config: dict,
                 timeint: int = 0, todaemon: bool = False):

        # check type
        self.__check_type(paths, dict, 'paths')
        self.__check_type(config, dict, 'config')
        self.__check_type(timeint, int, 'timeint')
        self.__check_type(todaemon, bool, 'todaemon')

        keys = ['rover', 'base', 'nav', 'sp3', 'clk', 'output']
        for k, v in paths.items():
            if k not in keys:
                raise Exception(f"Неопознанный ключ {k}")
            self.__check_type(v, str, v)

        for k, v in config.items():
            self.__check_type(v, str, k)
        
        # start match
        rover_files = []
        base_files = []
        nav_files = []
        sp3_files = []
        clk_files = []

        for key, value in paths.items():
            for root, _, files in os.walk(value):
                for file in files:
                    path = os.path.join(root, file)
                    if key == 'rover':
                        rover_files.append(path)
                    elif key == 'base':
                        base_files.append(path)
                    elif key == 'nav':
                        nav_files.append(path)
                    elif key == 'sp3':
                        sp3_files.append(path)
                    elif key == 'clk':
                        clk_files.append(path)

        match_list = dict()
        
        for file in rover_files:
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'TIME OF FIRST OBS' in line:
                        date = line.split()[:3]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date = '/'.join(date)

                        path_docker = file.replace(paths['rover'], '')
                        path_docker = '/app/input_rnx2rtkp_rover/' + path_docker
                        if date in match_list:
                            match_list[date] += [path_docker]
                        else:
                            match_list[date] = [path_docker]
                        break
                    elif 'END OF HEADER' in line:
                        break
        
        for file in base_files:
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'TIME OF FIRST OBS' in line:
                        date = line.split()[:3]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date = '/'.join(date)

                        path_docker = file.replace(paths['base'], '')
                        path_docker = '/app/input_rnx2rtkp_base/' + path_docker
                        if date in match_list:
                            match_list[date] += [path_docker]
                        else:
                            match_list[date] = [path_docker]
                        break
                    elif 'END OF HEADER' in line:
                        break

        for file in nav_files:
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

                        path_docker = file.replace(paths['nav'], '')
                        path_docker = '/app/input_rnx2rtkp_nav/' + path_docker
                        if date in match_list:
                            match_list[date] += [path_docker]
                        else:
                            match_list[date] = [path_docker]
                        break

        for file in sp3_files:
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if line[0] == "*":
                        date = line.split()[1:4]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date[0] = '20' + \
                            date[0] if not len(date[0]) == 4 else date[0]
                        date = '/'.join(date)
                        path_docker = file.replace(paths['sp3'], '')
                        path_docker = '/app/input_rnx2rtkp_sp3/' + path_docker
                        if date in match_list:
                            match_list[date] += [path_docker]
                        else:
                            match_list[date] = [path_docker]
                        break

        for file in clk_files:
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

                        path_docker = file.replace(paths['clk'], '')
                        path_docker = '/app/input_rnx2rtkp_clk/' + path_docker
                        if date in match_list:
                            match_list[date] += [path_docker]
                        else:
                            match_list[date] = [path_docker]
                        break
        # sbas_fcb_ionex

        # создание временного файла конфига
        folder_conf = os.path.join(Path(__file__).resolve().parent.parent, 'conf')
        alphabet = string.ascii_letters + string.digits
        name_conf = ''.join(random.choice(alphabet) for i in range(6))
        path_conf = os.path.join(folder_conf, name_conf) + '.conf'

        f = open(path_conf, 'w')
        for key, val in config.items():
            f.write(key + '=' + val + '\n')
        f.close()

        pos_paths = []
        bar = IncrementalBar('Progress', max=len(match_list), suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
        
        for _, value in match_list.items():
            command = f'-ti {timeint} ' if timeint != '' else ''
            command += f"-k '/app/conf/{os.path.basename(path_conf)}' "
            for path_file in value:
                command += f"'{path_file}'" + ' '
            command += f"-o '/app/output_rnx2rtkp/{os.path.basename(value[0])}.pos'"
            pos_paths.append(
                f"{os.path.join(paths['output'], os.path.basename(value[0]))}.pos")

            cmd = f'/bin/bash -c "exec -a rnx2rtkp ./rnx2rtkp {command}"'
            #print(cmd)
            if not todaemon:
                self._run_container('rnx2rtkp', paths, command=cmd)
            else:
                cont = self.client.containers.get('moncenterlib_rnx2rtkp_daemon')
                cont.exec_run(cmd, detach=False)
            bar.next()

        bar.finish()
        os.remove(path_conf)
        return self.__check_files(pos_paths)

    def cats(self):
        pass
