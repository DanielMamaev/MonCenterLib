from datetime import datetime
from logging import Logger
import os
from pathlib import Path
import subprocess
import tempfile
import moncenterlib.tools as mcl_tools
from typeguard import typechecked


class Stream2File:
    """
    This class is used to convert a stream to a file.
    You can choose type of connections: serial, tcpcli and NTRIP.
    You can manage connections. Add and remove connections, start and stop connections.
    Also you can get status of connections.

    This class use binary file of RTKLib library [https://rtklib.com/]. The name of file is str2str. 
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
    def add_connection(self, name: str, param: dict[str, str], output_dir: str) -> None:
        """
        This method is used to add a connection. Data of connection stored in variable 'connections'.

        The parameters that you can use are listed below in the example.


        Args:
            name (str): Name of the connection.
            param (dict[str, str]): Dictionary of parameters.
            output_dir (str): Path to the output directory where the file will be saved.

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
            >>> s2f.add_connection("test_connect", your_param, "/some_output_dir")

        """
        self.logger.info("Adding connection %s.", name)
        parameters = param.copy()

        self._check_param(parameters)

        if not os.path.isdir(output_dir):
            msg = f"Path '{output_dir}' to dir is strange."
            self.logger.error(msg)
            raise ValueError(msg)

        self.connections[name] = {"param": None, "temp_file": None, "process": None}
        self.connections[name]["param"] = parameters
        self.connections[name]["param"]["output_dir"] = output_dir

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
    def start(self, name: str):
        """
        This method is used to start a connection.
        Importantly!!!
        1. You should use a context manager to start a connection.
        The context manager will allow you to close the connection and write to the file automatically.
        If this is not done, there is a high risk that the process will not be killed, It will run until the computer is restarted.

        2. Every connection have have key 'process'. Value of this key is the subprocess object. if something goes wrong,
        you will have access to this object, which started the process of connecting and writing to the file.

        3. When your program finished, all processes will be stopped.

        4. It follows from the 3rd point that if you want connections to be constantly active, you need the program to work constantly.
        For example, you can use an infinite loop or something else.

        See code usage examples in the examples folder.

        Args:
            name (str): Name of the connection.

        Examples:
            >>> from moncenterlib.gnss.stream2file import Stream2File
            >>> import time
            >>> with Stream2File() as s2f:
            ...    s2f.add_connection("TEST",...)
            ...    s2f.start("TEST")
            ...    while True:
            ...        s2f.get_status("TEST")
            ...        time.sleep(2)
        """
        self.logger.info("Starting connection %s.", name)

        self._check_name_in_connections(name)

        self._stop_process(name)

        temp_file = tempfile.NamedTemporaryFile()

        cmd = [mcl_tools.get_path2bin("str2str"), "-outstat", temp_file.name]

        param = self.connections[name]["param"]
        if param["type"] == "serial":
            cmd += ["-in",
                    f'serial://{param["port"]}:{param["brate"]}:{param["bsize"]}:{param["parity"]}:{param["stopb"]}:{param["fctr"]}']
        elif param["type"] == "tcpcli":
            cmd += ["-in", f'tcpcli://{param["addr"]}:{param["port"]}']
        elif param["type"] == "ntrip":
            cmd += ["-in",
                    f'ntrip://{param["user"]}:{param["passwd"]}@{param["addr"]}:{param["port"]}/{param["mntpnt"]}']

        date = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = Path(param["output_dir"]).joinpath(f"{name}_{date}.log")
        cmd += ["-out", f'file://{output_file}']

        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.connections[name]["temp_file"] = temp_file
        self.connections[name]["process"] = process

    @typechecked
    def stop(self, name: str):
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
    def _stop_process(self, name: str):
        self._check_name_in_connections(name)

        if self.connections[name]["process"] is not None:
            self.connections[name]["process"].kill()
        if self.connections[name]["temp_file"] is not None:
            self.connections[name]["temp_file"].close()

    def start_all(self):
        """
        This method is used to start all connections.

        Examples:
            >>> from moncenterlib.gnss.stream2file import Stream2File
            >>> s2f = Stream2File()
            >>> s2f.add_connection("TEST",...)
            >>> s2f.add_connection("TEST2",...)
            >>> s2f.start_all()
        """
        self.logger.info("Starting all connections.")
        for name in self.connections.keys():
            self.start(name)

    def stop_all(self):
        """
        This method is used to stop all connections.

        Examples:
            >>> from moncenterlib.gnss.stream2file import Stream2File
            >>> s2f = Stream2File()
            >>> s2f.add_connection("TEST",...)
            >>> s2f.add_connection("TEST2",...)
            >>> s2f.stop_all()
        """
        self.logger.info("Stopping all connections.")
        for name in self.connections.keys():
            self.stop(name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_all()

    def __del__(self):
        self.stop_all()
