import gzip
import json
import os
import logging
import requests
from progress.bar import IncrementalBar


class RGSClient:
    def __init__(self, api_token, logger=None):
        """
        :param api_token: Ваш API Token
        """
        self.path = 'https://rgs-centre.ru/api'
        self.api_token = api_token

        self.logger = logger
        if not self.logger:
            self.logger = logging.getLogger('RGS CLient')
            self.logger.handlers.clear()
            self.logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def get_file_list(self, filter={}):
        """
        Получить список файлов по фильтру

        :param filter:
        :return:
        """
        if self.api_token:
            return self._query(method='files', filter=filter)
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

        with requests.Session() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
            }
            request = session.get(url, headers=headers)
            if json_mode:
                return json.loads(request.content.decode())
            else:
                return request.content

    def download_files(self, path_output, request, unpack=True):
        files_list = []
        self.logger.info('Получаем список файлов по указанному запросу')
        try:
            files_list = self.get_file_list(request)
        except Exception as e:
            self.logger.error(f'Проблема с получением списка файлов {e}')
            raise Exception(f'Проблема с получением списка файлов {e}')

        if files_list == [] or files_list == None:
            self.logger.error('Список полученных файлов пуст. Ничего не найдено')
            raise Exception('Список полученных файлов пуст. Ничего не найдено')

        self.logger.info('Начало загрузки файлов')
        bar = IncrementalBar(f'{request["working_center"]} - Progress', max=len(files_list),
                             suffix='%(percent).d%% - %(index)d/%(max)d - %(elapsed)ds')
        bar.start()
        for file in files_list:
            self.logger.info(f"File {file['name']} downloading")
            try:
                self._download_file(file['name'], os.path.join(path_output, file['name']), unpack)
            except Exception as e:
                self.logger.error(f"Проблема со скачиванием файла {file['name']} {e}")
            bar.next()
        bar.finish()

        return files_list
