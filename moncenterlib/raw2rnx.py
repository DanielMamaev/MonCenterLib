import argparse
import os
from pprint import pprint
import configparser
import sys


class Raw2Rnx:
    """
    RINEX (Receiver Independent Exchange Format) is a standard GPS/GNSS data
    format supported by many receivers or GPS/GNSS post‐processing analysis
    software. CONVBIN translates receiver raw, RTCM and BINEX messages to
    RINEX OBS (observation data), RINEX NAV (GNSS navigation messages).
    CONVBIN can also extract SBAS messages from the receiver
    raw data and output the SBAS log file. The supported RINEX versions
    are 2.10, 2.11, 2.12, 3.00, 3.01, 3.02, 3.03, 3.04.

    This class allows you to convert one or more files by configuration file.
    """

    def read_dir(self, input_dir: str) -> list:
        """
        This method reads files from the specified folder and puts the file
        paths in the list.

        Args:
            input_dir: The path to the folder with the raw measurement files.

        Raises:
            TypeError: Occurs if an incorrect data type was passed in the argument.

        Returns:
            Returns a list containing the paths to the files.

        Examples:
            >>> raw2rnx = Raw2Rnx()
            >>> print(raw2rnx.read_dir('/home_dir/NSKV/'))
            ['/home_dir/NSKV/nskv3610.ubx', '/home_dir/NSKV/nskv3620.ubx',
            '/home_dir/NSKV/nskv3600.ubx', '/home_dir/NSKV/nskv3630.ubx']
        """
        if not type(input_dir) is str:
            raise TypeError(
                "The type of the 'input_dir' variable should be 'str'")

        input_files = list(
            map(lambda x: os.path.join(input_dir, x),
                os.listdir(input_dir))) if input_dir != '' else []

        return input_files

    def start(self, list_files: list, path_convbin: str, convbin_conf: str,
              output_dir: str) -> dict:
        """
        This method starts the converting process.
        RINEX files are generated at the output. And also the method returns a
        dictionary with the paths of the generated RINEX files.

        Args:
            list_files: The list is formed from the read_dir method.
            path_convbin: The path to the convbin executable.
            convbin_conf: The path to convbin config.
            output_dir: The path to the output folder.

        Raises:
            TypeError: Occurs if an incorrect data type was passed in the argument.

        Returns:
            Returns a dictionary with the paths of the generated RINEX files.

        Examples:
            >>> raw2rnx = Raw2Rnx()
            >>> lst = raw2rnx.read_dir('/home_dir/NSKV/')
            >>> print(raw2rnx.start(lst, '/home_dir/convbin', '/home_dir/convbin.conf', '/home_dir/output'))
            {
                '/home_dir/NSKV/nskv3600.ubx': ['/home_dir/output/nskv3600.ubx.o', '/home_dir/output/nskv3600.ubx.n'],
                '/home_dir/NSKV/nskv3610.ubx': ['/home_dir/output/nskv3610.ubx.o', '/home_dir/output/nskv3610.ubx.n'],
                '/home_dir/NSKV/nskv3620.ubx': ['/home_dir/output/nskv3620.ubx.o', '/home_dir/output/nskv3620.ubx.n'],
                '/home_dir/NSKV/nskv3630.ubx': ['/home_dir/output/nskv3630.ubx.o', '/home_dir/output/nskv3630.ubx.n']
            }
        """
        output_dict = dict()

        if not type(list_files) is list:
            raise TypeError(
                "The type of the 'list_files' variable should be 'list'")
        elif not type(path_convbin) is str:
            raise TypeError(
                "The type of the 'path_convbin' variable should be 'str'")
        elif not type(convbin_conf) is str:
            raise TypeError(
                "The type of the 'convbin_conf' variable should be 'str'")
        elif not type(output_dir) is str:
            raise TypeError(
                "The type of the 'output_dir' variable should be 'str'")

        config = configparser.ConfigParser()
        config.read(convbin_conf)
        config = dict(config['set'])
        for key, val in config.items():
            config[key] = val.split('#')[0].strip()

        for file in list_files:
            output_dict[file] = []

            command = path_convbin + ' '

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

            if config['output_o'] == '1':
                out = f"{os.path.join(output_dir, os.path.basename(file))}.o"
                command += f"-o '{out}' "
                output_dict[file].append(out)
            if config['output_n'] == '1':
                out = f"{os.path.join(output_dir, os.path.basename(file))}.n"
                command += f"-n '{out}' "
                output_dict[file].append(out)
            if config['output_g'] == '1':
                out = f"{os.path.join(output_dir, os.path.basename(file))}.g"
                command += f"-g '{out}' "
                output_dict[file].append(out)
            if config['output_h'] == '1':
                out = f"{os.path.join(output_dir, os.path.basename(file))}.h"
                command += f"-h '{out}' "
                output_dict[file].append(out)
            if config['output_q'] == '1':
                out = f"{os.path.join(output_dir, os.path.basename(file))}.q"
                command += f"-q '{out}' "
                output_dict[file].append(out)
            if config['output_l'] == '1':
                out = f"{os.path.join(output_dir, os.path.basename(file))}.l"
                command += f"-l '{out}' "
                output_dict[file].append(out)
            if config['output_b'] == '1':
                out = f"{os.path.join(output_dir, os.path.basename(file))}.b"
                command += f"-b '{out}' "
                output_dict[file].append(out)
            if config['output_i'] == '1':
                out = f"{os.path.join(output_dir, os.path.basename(file))}.i"
                command += f"-i '{out}' "
                output_dict[file].append(out)
            if config['output_s'] == '1':
                out = f"{os.path.join(output_dir, os.path.basename(file))}.s"
                command += f"-s '{out}' "
                output_dict[file].append(out)

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

            command += f"'{file}'"
            # print(command)
            os.system(command)

        return output_dict


if __name__ == '__main__':
    des = """
    RINEX (Receiver Independent Exchange Format) is a standard GPS/GNSS data
    format supported by many receivers or GPS/GNSS post‐processing analysis
    software. CONVBIN translates receiver raw, RTCM and BINEX messages to
    RINEX OBS (observation data), RINEX NAV (GNSS navigation messages).
    CONVBIN can also extract SBAS messages from the receiver
    raw data and output the SBAS log file. The supported RINEX versions
    are 2.10, 2.11, 2.12, 3.00, 3.01, 3.02, 3.03, 3.04.

    This class allows you to convert one or more files by configuration file.
    """
    parser = argparse.ArgumentParser(description=des)
    parser.add_argument('-i', '--input', type=str, help='Specify the path to the folder with the raw files.')
    parser.add_argument('-e', '--convbin', type=str, help='Specify the path to executable convbin.')
    parser.add_argument('-c', '--conf', type=str, help='Specify the path to convbin config.')
    parser.add_argument('-o', '--output', type=str, help='Specify the path to the output folder.')
    parser.add_argument('-l', '--list', action='store_true', help='Show the found files in the folder.')
    parser.add_argument('-p', '--paths', action='store_true', help='Show the paths of the generated RINEX files.')

    arg = parser.parse_args()

    if arg.input is None:
        print('Error. Specify the path to the folder with the raw files.')
        sys.exit()
    if arg.convbin is None:
        print('Error. Specify the path to executable convbin.')
        sys.exit()
    if arg.conf is None:
        print('Error. Specify the path to convbin config.')
        sys.exit()
    if arg.output is None:
        print('Error. Specify the path to the output folder.')
        sys.exit()

    raw2rnx = Raw2Rnx()
    lst = raw2rnx.read_dir(arg.input)
    if arg.list:
        pprint('# Show list start #')
        pprint(lst)
        pprint('# Show list end #')
    
    paths = raw2rnx.start(lst, arg.convbin, arg.conf, arg.output)
    if arg.paths:
        pprint('# Show paths start #')
        pprint(paths)
        pprint('# Show paths end #')

