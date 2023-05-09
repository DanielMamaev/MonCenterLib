import gzip
import random
import string
from urllib.request import urlopen
import json
import os


class RGSClient:
    def __init__(self, api_token):
        """
        :param api_token: Ваш API Token
        """
        self.path = 'https://rgs-centre.ru/api'
        self.api_token = api_token

    def get_file_list(self, filter={}):
        """
        Получить список файлов по фильтру

        :param filter:
        :return:
        """
        if self.api_token:
            return self._query(method='files', filter=filter)
        return None

    def download_files(self, filter={}, output_file=''):
        """
        Скачать файлы по фильтру

        :param filter:
        :param output_file:
        :return:
        """
        if self.api_token:
            if output_file == '':
                output_file = 'out_' + \
                    ''.join(random.choice(string.ascii_lowercase + string.digits)
                            for i in range(0, 12)) + '.gz'

            data = self._query(method='files/download',
                               filter=filter, json_mode=False)
            with open(output_file, 'wb') as out:
                out.write(data)
        else:
            return None

    def get_file(self, filename, unpack=False):
        """
        Получить содержимое файла по его имени

        :param filename:
        :param unpack:
        :return:
        """
        if self.api_token:
            if unpack:
                return gzip.decompress(self._query(method=f'file/{filename}', json_mode=False)).decode()
            else:
                return self._query(method=f'file/{filename}', json_mode=False)
        return None

    def _download_file(self, filename, output_file=None, unpack=False):
        """
        Скачать файл по его имени

        :param filename:
        :param output_file:
        :param unpack:
        :return:
        """
        if self.api_token:
            data = self.get_file(filename=filename, unpack=unpack)

            if unpack:
                with open((output_file or filename).replace('.gz', ''), 'w' if unpack else 'wb') as out:
                    out.write(data)
            else:
                with open((output_file or filename), 'w' if unpack else 'wb') as out:
                    out.write(data)
        else:
            return None

    def fags_info(self, fags_name):
        """
        Получить информацию по пункту ФАГС

        :param fags_name:
        :return:
        """
        if self.api_token:
            return self._query(method=f'fags/{fags_name}')
        else:
            return None

    def get_fags_list(self, filter={}):
        """
        Получить список пунктов ФАГС по фильтру

        :param filter:
        :return:
        """
        if self.api_token:
            return self._query(method='fags', filter=filter)
        return None

    def _query(self, method, filter={}, json_mode=True):
        """
        Метод запроса на сайт

        :param method:
        :param filter:
        :param json_mode:
        :return:
        """
        filter['api_token'] = self.api_token

        method += '?' + \
            '&'.join([f'{key}={value}' for key, value in filter.items()])

        url = '/'.join((self.path, method))

        with urlopen(url) as host_data:
            data = host_data.read()

            if json_mode:
                return json.loads(data)
            else:
                return data
    
    def download_files(self, path_output, request, unpack=True):
        try:
            files_list = self.get_file_list(request)
        except Exception as e:
            print(f'Проблема с получением списка файлов {e}')
            return False
        
        if files_list == [] or files_list == None:
            print(f"Список полученных файлов пуст. Ничего не найдено")
            return False
        
        for file in files_list:
            try:
                self._download_file(file['name'], os.path.join(path_output, file['name']), unpack)
            except Exception as e:
                print(f'Проблема со скачиванием файла {e}')
