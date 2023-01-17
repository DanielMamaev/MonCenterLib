import docker
import os
from pathlib import Path
import string
import random


class SoftDocker:
    def __init__(self) -> None:
        self.container = None

    def run_container(self,
                      paths_str2str=[],
                      paths_convbin=[],
                      paths_rnx2rtkp=[],
                      paths_cats=[],
                      restart_cont=True):

        client = docker.from_env()
        volumes = [f"{os.path.join(Path(__file__).resolve().parent.parent, 'conf')}:/app/conf/"]

        if not paths_str2str == []:
            volumes.append(f'{paths_str2str[0]}:/app/input_rtklib_str2str')
            volumes.append(f'{paths_str2str[1]}:/app/output_rtklib_str2str')
        if not paths_convbin == []:
            volumes.append(f'{paths_convbin[0]}:/app/input_rtklib_convbin')
            volumes.append(f'{paths_convbin[1]}:/app/output_rtklib_convbin')
        if not paths_rnx2rtkp == []:
            volumes.append(f'{paths_rnx2rtkp[0]}:/app/input_rtklib_rnx2rtkp')
            volumes.append(f'{paths_rnx2rtkp[1]}:/app/output_rtklib_rnx2rtkp')
        if not paths_cats == []:
            volumes.append(f'{paths_cats[0]}:/app/input_cats')
            volumes.append(f'{paths_cats[1]}:/app/output_cats')

        try:
            if restart_cont:
                self.container = client.containers.get('moncenterlib')
                self.container.stop()
                self.container.remove()
            self.container = client.containers.run("danielmamaev/moncenterlib",
                                                   name='moncenterlib',
                                                   command="tail -F /dev/null",
                                                   detach=True,
                                                   volumes=volumes
                                                   )
        except docker.errors.APIError as e:
            if e.response.status_code == 404:
                print('Не найден образ')
            elif e.response.status_code == 409:
                self.container = client.containers.get('moncenterlib')
                self.container.start()
            else:
                print(e)

    def __check_files(self, files):
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

    def str2str(self):
        pass

    def convbin(self, in_out_dir, config):
        # составляем список файлов из папки
        input_files = list(
            map(lambda x: os.path.join(in_out_dir[0], x),
                os.listdir(in_out_dir[0]))) if in_out_dir[0] != '' else []

        # запуск конвертации
        output_files = []

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
                out = f"/app/output_rtklib_convbin/{namef}.o"
                command += f"-o '{out}' "
                output_files.append(os.path.join(in_out_dir[1],
                                    f"{namef}.o"))
            if config['output_n'] == '1':
                out = f"/app/output_rtklib_convbin/{namef}.n"
                command += f"-n '{out}' "
                output_files.append(os.path.join(in_out_dir[1],
                                    f"{namef}.n"))
            if config['output_g'] == '1':
                out = f"/app/output_rtklib_convbin/{namef}.g"
                command += f"-g '{out}' "
                output_files.append(os.path.join(in_out_dir[1],
                                    f"{namef}.g"))
            if config['output_h'] == '1':
                out = f"/app/output_rtklib_convbin/{namef}.h"
                command += f"-h '{out}' "
                output_files.append(os.path.join(in_out_dir[1],
                                    f"{namef}.h"))
            if config['output_q'] == '1':
                out = f"/app/output_rtklib_convbin/{namef}.q"
                command += f"-q '{out}' "
                output_files.append(os.path.join(in_out_dir[1],
                                    f"{namef}.q"))
            if config['output_l'] == '1':
                out = f"/app/output_rtklib_convbin/{namef}.l"
                command += f"-l '{out}' "
                output_files.append(os.path.join(in_out_dir[1],
                                    f"{namef}.l"))
            if config['output_b'] == '1':
                out = f"/app/output_rtklib_convbin/{namef}.b"
                command += f"-b '{out}' "
                output_files.append(os.path.join(in_out_dir[1],
                                    f"{namef}.b"))
            if config['output_i'] == '1':
                out = f"/app/output_rtklib_convbin/{namef}.i"
                command += f"-i '{out}' "
                output_files.append(os.path.join(in_out_dir[1],
                                    f"{namef}.i"))
            if config['output_s'] == '1':
                out = f"/app/output_rtklib_convbin/{namef}.s"
                command += f"-s '{out}' "
                output_files.append(os.path.join(in_out_dir[1],
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

            command += f"'/app/input_rtklib_convbin/{os.path.basename(file)}'"
            #print(command)
            cmd = f'/bin/bash -c "exec -a convbin /app/RTKLIB/app/consapp/convbin/gcc/convbin {command}"'
            self.container.exec_run(cmd, detach=False)

            #переименование файлов по стандарту ринекса, впланах
            #output_done = self.__check_files(output_files)

        return self.__check_files(output_files)

    def rnx2rtkp(self, input_dir: str, output_dir: str, config: dict,
                 roles: dict, timeint: int = 0):

        rover_files = []
        base_files = []
        nav_files = []
        sp3_files = []
        clk_files = []

        for root, _, files in os.walk(input_dir):
            for file in files:
                path = os.path.join(root, file)
                if roles.get('rover', 'NotFound!') in path:
                    rover_files.append(path)
                elif roles.get('base', 'NotFound!') in path:
                    base_files.append(path)
                elif roles.get('nav', 'NotFound!') in path:
                    nav_files.append(path)
                elif roles.get('sp3', 'NotFound!') in path:
                    sp3_files.append(path)
                elif roles.get('clk', 'NotFound!') in path:
                    clk_files.append(path)

        match_list = dict()

        for file in rover_files + base_files:
            with open(file, 'r') as f:
                for n, line in enumerate(f, 1):
                    if 'TIME OF FIRST OBS' in line:
                        date = line.split()[:3]
                        date[1] = date[1].zfill(2)
                        date[2] = date[2].zfill(2)
                        date = '/'.join(date)

                        path_docker = file.replace(input_dir, '')
                        path_docker = '/app/input_rtklib_rnx2rtkp' + path_docker
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

                        path_docker = file.replace(input_dir, '')
                        path_docker = '/app/input_rtklib_rnx2rtkp' + path_docker
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
                        path_docker = file.replace(input_dir, '')
                        path_docker = '/app/input_rtklib_rnx2rtkp' + path_docker
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

                        path_docker = file.replace(input_dir, '')
                        path_docker = '/app/input_rtklib_rnx2rtkp' + path_docker
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
        for key, value in match_list.items():

            command = f'-ti {timeint} ' if timeint != '' else ''
            command += f"-k '/app/conf/{os.path.basename(path_conf)}' "
            for path_file in value:
                command += f"'{path_file}'" + ' '
            command += f"-o '/app/output_rtklib_rnx2rtkp/{os.path.basename(value[0])}.pos'"
            pos_paths.append(
                f"{os.path.join(output_dir, os.path.basename(value[0]))}.pos")

            cmd = f'/bin/bash -c "exec -a rnx2rtkp /app/RTKLIB/app/consapp/rnx2rtkp/gcc/rnx2rtkp {command}"'
            #print(cmd)
            self.container.exec_run(cmd, detach=False)

        os.remove(path_conf)
        return self.__check_files(pos_paths)

    def cats(self):
        pass
