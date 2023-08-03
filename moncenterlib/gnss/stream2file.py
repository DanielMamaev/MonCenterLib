import base64
import socket
import threading
import selectors

_SOURCETABLE_RESPONSES = [
  'SOURCETABLE 200 OK'
]
_SUCCESS_RESPONSES = [
  'ICY 200 OK',
  'HTTP/1.0 200 OK',
  'HTTP/1.1 200 OK'
]
_UNAUTHORIZED_RESPONSES = [
  '401'
]


class Stream2File():
    def __init__(self) -> None:
        self.clients = dict()
        self.selector = selectors.DefaultSelector()

    def new_serial(self):
        pass

    def new_tcp(self, host, port, name, output):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(5)

        try:
            server_socket.connect((host, port))
        except Exception as e:
            print(f'Unable to connect socket to server at http://{host}:{port}')
            print(f'Exception: {str(e)}')
            return False
        
        self.clients[server_socket] = {'type': 'tcp',
                                        'name': name,
                                        'output': output,
                                        'last_size_data': 0,
                                        'size_data': 0}
        self.selector.register(fileobj=server_socket, events=selectors.EVENT_READ, data=self.__read_data)

    def new_ntrip(self,
                  host,
                  port,
                  mountpoint,
                  username,
                  password,
                  output,
                  name,
                  ntrip_version=''):

        # проверки на то что файл существует, типы данных

        connected = False

        if username is not None and password is not None:
            basic_credentials = base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')
        else:
            basic_credentials = None

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(5)

        try:
            server_socket.connect((host, port))
        except Exception as e:
            print(f'Unable to connect socket to server at http://{host}:{port}')
            print(f'Exception: {str(e)}')
            return False

        try:
            if ntrip_version is not None and ntrip_version != '':
                request_str = f'GET /{mountpoint} HTTP/1.0\r\nHost: mgex.igs-ip.net:2101\r\nNtrip-Version: {ntrip_version}\r\nUser-Agent: NTRIP ntrip_client_ros\r\n'
            else:
                request_str = f'GET /{mountpoint} HTTP/1.1\r\nUser-Agent: NTRIP ntrip_client_ros\r\n'

            if basic_credentials is not None:
                request_str += f'Authorization: Basic {basic_credentials}\r\n'
            request_str += '\r\n'

            server_socket.send(request_str.encode('utf-8'))
        except Exception as e:
            print(f'Unable to send request to server at http://{host}:{port}')
            print(f'Exception: {str(e)}')
            return False

        response = ''
        try:
            response = server_socket.recv(1024)
            response = response.decode('utf-8')
            #print(response)
        except Exception as e:
            print(f'Unable to read response from server at http://{host}:{port}')
            print(f'Exception: {str(e)}')
            return False

        if any(success in response for success in _SUCCESS_RESPONSES):
            connected = True

        known_error = False
        if any(sourcetable in response for sourcetable in _SOURCETABLE_RESPONSES):
            print('Received sourcetable response from the server. This probably means the mountpoint specified is not valid') 
            known_error = True
        elif any(unauthorized in response for unauthorized in _UNAUTHORIZED_RESPONSES):
            print('Received unauthorized response from the server. Check your username, password, and mountpoint to make sure they are correct.')
            known_error = True
        elif not connected and (ntrip_version == None or ntrip_version == ''):
            print('Received unknown error from the server. Note that the NTRIP version was not specified in the launch file. This is not necesarilly the cause of this error, but it may be worth checking your NTRIP casters documentation to see if the NTRIP version needs to be specified.')
            known_error = True

        if known_error or not connected:
            print(f'Invalid response received from http://{host}:{port}/{mountpoint}')
            print(f'Response: {response}')
            return False
        else:
            print(f'Connected to http://{host}:{port}/{mountpoint}')

            self.clients[server_socket] = {'type': 'ntrip',
                                           'name': name,
                                           'output': output,
                                           'last_size_data': 0,
                                           'size_data': 0}
            self.selector.register(fileobj=server_socket, events=selectors.EVENT_READ, data=self.__read_data)

    def disconnect(self):
        pass

    def __reconnect(self):
        pass

    def __read_data(self, server_socket, output):
        data = server_socket.recv(1024)

        self.clients[server_socket]['last_size_data'] = len(data)
        self.clients[server_socket]['size_data'] += len(data)

        f = open(output, 'ab')
        f.write(data)
        f.close()

    def start(self):
        def event_loop():
            while True:
                events = self.selector.select()
                if list(self.clients.keys()) is not []:
                    for key, _ in events:
                        callback = key.data
                        callback(key.fileobj, self.clients[key.fileobj]['output'])
        t = threading.Thread(target=event_loop)
        t.start()

    def get_status(self, name):
        for _, val in self.clients.items():
            if val['name'] == name:
                return val


if __name__ == '__main__':
    s2f = Stream2File()
    s2f.start()
    s2f.new_ntrip('mgex.igs-ip.net', 2101, 'RTCM3EPH-MGEX-GLO', 'Danisimo', '96869686', '/home/danisimo/MonCenterLib/test aa/output_str2str/glo.txt', 'task3')
    s2f.new_ntrip('mgex.igs-ip.net', 2101, 'RTCM3EPH-MGEX', 'Danisimo', '96869686', '/home/danisimo/MonCenterLib/test aa/output_str2str/all.txt', 'task2')
    s2f.new_ntrip('mgex.igs-ip.net', 2101, 'RTCM3EPH-MGEX-GPS', 'Danisimo', '96869686', '/home/danisimo/MonCenterLib/test aa/output_str2str/gps.txt', 'task1')
    
    import time
    time.sleep(10)
    print(s2f.get_status('task1'))
    print(s2f.get_status('task2'))
    print(s2f.get_status('task3'))


