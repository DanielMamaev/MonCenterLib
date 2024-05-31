from datetime import datetime
from logging import Logger
import os
from pathlib import Path
import subprocess
import tempfile
import time
import moncenterlib.tools as mcl_tools
from typeguard import typechecked


class Stream2File:
    """
    This class is used to convert a stream to a file.
    You can choose type of connections: serial, tcpcli and NTRIP.
    You can manage connections. Add and remove connections, start and stop connections.
    Also you can get status of connections.

    This class use binary file of RTKLib library https://rtklib.com/. The name of file is str2str.
    This bin file was modified for this class.

    See example code in example folder.
    """
    @typechecked
    def __init__(self, logger: bool | Logger | None = None) -> None:
        """
        Args:
            logger (bool | Logger, optional): if the logger is None, a logger will be created inside the default class.
                If the logger is False, then no information will be output.
                If you pass an instance of your logger, the information output will be implemented according to your logger.
                Defaults to None.
        """
        self.logger = logger

        if self.logger in [None, False]:
            self.logger = mcl_tools.create_simple_logger("Stream2File", logger)

        self.connections = {}

    @typechecked
    def _check_name_in_connections(self, name: str) -> None:
        if name not in self.connections:
            msg = f"Unknown name of connection '{name}'."
            self.logger.error(msg)
            raise ValueError(msg)

    @typechecked
    def _check_param(self, param: dict[str, str]) -> None:
        self.logger.info("Check input parameters.")
        types = ["serial", "tcpcli", "ntrip"]
        serial_param = ["port", "brate", "bsize", "parity", "stopb", "fctr"]
        tcp_param = ["addr", "port"]
        ntrip_param = ["user", "passwd", "addr", "port", "mntpnt"]

        if param.get("type", None) is None:
            msg = "Not found key 'type' in param."
            self.logger.error(msg)
            raise KeyError(msg)

        if param["type"] not in types:
            msg = f"Unknown type \'{param['type']}\' in param."
            self.logger.error(msg)
            raise ValueError(msg)

        if param["type"] == "serial":
            for i in serial_param:
                if i not in param:
                    msg = f"Missing key '{i}' in param."
                    self.logger.error(msg)
                    raise KeyError(msg)

        elif param["type"] == "tcpcli":
            for i in tcp_param:
                if i not in param:
                    msg = f"Missing key '{i}' in param."
                    self.logger.error(msg)
                    raise KeyError(msg)

        elif param["type"] == "ntrip":
            for i in ntrip_param:
                if i not in param:
                    msg = f"Missing key '{i}' in param."
                    self.logger.error(msg)
                    raise KeyError(msg)

    @typechecked
    def add_connection(self, name: str, param: dict[str, str], on_start: str = "") -> None:
        """
        This method is used to add a connection. Data of connection stored in variable 'connections'.

        The parameters that you can use are listed below in the example.


        Args:
            name (str): Name of the connection.
            param (dict[str, str]): Dictionary of parameters.
            on_start (str, optional): Command that will be send to host when the connection starts.

        Raises:
            ValueError: Path 'output_dir' to dir is strange.

        Examples:
            >>> # example parameters
            >>> {"type": "serial", "port": "COM1", "brate": "9600", "bsize": "8", "parity": "None", "stopb": "1", "fctr": "None"}
            >>> {"type": "tcpcli", "addr": "1.2.3.4", "port": "123"}
            >>> {"type": "ntrip", "user": "anonymous", "passwd": "anonymous", "addr": "1.2.3.4", "port": "123", "mntpnt": "AAAA"}
            >>> # example code
            >>> from moncenterlib.gnss.stream2file import Stream2File
            >>> s2f = Stream2File()
            >>> your_param = {"type": "..."}
            >>> s2f.add_connection("test_connect", your_param, on_start="some_cmd")

        """
        self.logger.info("Adding connection %s.", name)

        self._check_param(param)

        conf = {
            "param": param.copy(),
            "temp_file": None,
            "temp_file_on_start": None,
            "process": False
        }
        conf["param"]["on_start"] = on_start

        self.connections[name] = conf

        return None

    @typechecked
    def remove_connection(self, name: str) -> None:
        """
        This method is used to remove a connection. Data of connection remove from variable 'connections'.
        When you remove a connection, the process will be stopped.

        Args:
            name (str): Name of the connection.

        Examples:
            >>> from moncenterlib.gnss.stream2file import Stream2File
            >>> s2f = Stream2File()
            >>> s2f.remove_connection("TEST")
        """
        self.logger.info("Removing connection %s.", name)
        self._check_name_in_connections(name)

        self._stop_process(name)
        self.connections.pop(name, None)

    @typechecked
    def get_status(self, name: str) -> dict[str, str]:
        """
        This method is used to get the status of a connection.
        This method returns a dict. Where keys are the names of the metric, and values are the metric.
        If the metric doesn't exist, the value will be empty str.

        Args:
            name (str): Name of the connection.

        Raises:
            FileNotFoundError: File to get status doesn't exist.

        Returns:
            dict[str, str]: The keys of the dict are:
                - time (str): Time when the data was collected.
                - byte (str): Number of bytes received.
                - bps (str): Bit per second.
                - connect (str): Status of connection.

        Examples:
            >>> from moncenterlib.gnss.stream2file import Stream2File
            >>> s2f = Stream2File()
            >>> s2f.add_connection("TEST", ...)
            >>> s2f.start("TEST")
            >>> s2f.get_status("TEST")
        """
        self.logger.info("Getting status of connection %s.", name)
        self._check_name_in_connections(name)

        if not os.path.isfile(self.connections[name]["temp_file"].name):
            raise FileNotFoundError("File to get status doesn't exist.")

        status = {
            "time": "",
            "byte": "",
            "bps": "",
            "connect": ""
        }

        with open(self.connections[name]["temp_file"].name, "r", encoding="utf-8") as f:
            line = f.read().split()
            if line != []:
                status["time"] = f"{line[0]} {line[1]}"
                status["byte"] = line[2]
                status["bps"] = line[3]
                status["connect"] = line[4:]
        return status

    @typechecked
    def get_connection_names(self) -> list[str]:
        """Get name of connections

        Returns:
            list[str]: List name of connections
        """
        return list(self.connections.keys())

    @typechecked
    def create_output_file_name(self, name_conn: str, output_dir: str) -> str:
        """Create path to the output file. Format is 'nameConnection_YYYYMMDD_HHMMSS.log'

        Args:
            name_conn (str): Name of the connection.
            output_dir (str): Path to a directory where file will be save.

        Returns:
            str: Return path to the output file. Format is 'nameConnection_YYYYMMDD_HHMMSS.log'
        """

        date = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = Path(output_dir).joinpath(f"{name_conn}_{date}.log")

        return str(output_file)

    @typechecked
    def start(self, name_con: str, name_file: str) -> None:
        """
        This method is used to start a connection.
        This method is blocking. It uses an infinite loop internally.
        Use the threading module to solve this problem or other tools.
        The connection can be stopped using the 'stop' method.
        See example codes how to use module threading with this method.

        Args:
            name_con (str): Name of the connection.
            name_file (str): Path to the output file.

        Returns:
            str: Path to output file.

        Examples:
            >>> from moncenterlib.gnss.stream2file import Stream2File
            >>> s2f = Stream2File()
            >>> s2f.add_connection("TEST",...)
            >>> s2f.start("TEST", "path_to_output_file")
        """

        self.logger.info("Starting connection %s.", name_con)

        # check directory
        path_dir = os.path.dirname(name_file)
        if not os.path.isdir(path_dir):
            msg = f"Path '{path_dir}' to dir is strange."
            self.logger.error(msg)
            raise ValueError(msg)

        self._check_name_in_connections(name_con)

        self._stop_process(name_con)

        temp_file = tempfile.NamedTemporaryFile()

        cmd = [mcl_tools.get_path2bin("str2str"), "-outstat", temp_file.name]

        param = self.connections[name_con]["param"]
        if param["type"] == "serial":
            cmd += ["-in",
                    f'serial://{param["port"]}:{param["brate"]}:{param["bsize"]}:{param["parity"]}:{param["stopb"]}:{param["fctr"]}']
        elif param["type"] == "tcpcli":
            cmd += ["-in", f'tcpcli://{param["addr"]}:{param["port"]}']
        elif param["type"] == "ntrip":
            cmd += ["-in",
                    f'ntrip://{param["user"]}:{param["passwd"]}@{param["addr"]}:{param["port"]}/{param["mntpnt"]}']

        cmd += ["-out", f'file://{name_file}']

        if param.get("on_start", "") != "":
            temp_file_on_start = tempfile.NamedTemporaryFile()
            temp_file_on_start.write(param["on_start"].encode("utf-8"))
            temp_file_on_start.seek(0)
            cmd += ["-c", temp_file_on_start.name]
            self.connections[name_con]["temp_file_on_start"] = temp_file_on_start

        self.connections[name_con]["process"] = True
        self.connections[name_con]["temp_file"] = temp_file

        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        while self.connections[name_con]["process"]:
            time.sleep(0.1)
        process.kill()

        return None

    @typechecked
    def stop(self, name: str) -> None:
        """
        This method is used to stop a connection. After you can start a connection again.

        Args:
            name (str): Name of the connection.

        Examples:
            >>> from moncenterlib.gnss.stream2file import Stream2File
            >>> s2f = Stream2File()
            >>> s2f.stop("TEST")
        """
        self.logger.info("Stopping connection %s.", name)
        self._check_name_in_connections(name)
        self._stop_process(name)

    @typechecked
    def _stop_process(self, name: str) -> None:
        self._check_name_in_connections(name)

        if self.connections[name]["process"] is not None:
            self.connections[name]["process"] = False
        if self.connections[name]["temp_file"] is not None:
            self.connections[name]["temp_file"].close()
        if self.connections[name]["temp_file_on_start"] is not None:
            self.connections[name]["temp_file_on_start"].close()
