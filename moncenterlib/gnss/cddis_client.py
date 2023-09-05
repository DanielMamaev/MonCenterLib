import logging
from ftplib import FTP_TLS
import os
import gzip
import shutil


class CDDISClient:
    def __init__(self, logger=None):
        self.logger = logger

        if not self.logger:
            self.logger = logging.getLogger('CDDIS CLient')
            self.logger.handlers.clear()
            self.logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def get_daily_multi_gnss_brd_eph(self, path_dir, year, day, delete_gz=True):
        year = str(year)
        day = str(day).zfill(3)

        print('')

        self.logger.info(f'Ищем эфемериды в архиве CDDIS')
        try:
            ftps = FTP_TLS(host='gdc.cddis.eosdis.nasa.gov')
            ftps.login(user='anonymous', passwd='anonymous')
            ftps.prot_p()
            ftps.cwd(f'gnss/data/daily/{year}/brdc')
            file_lst = ftps.nlst()
        except Exception as e:
            self.logger.error(f'Что то с доступом к архиву CDDIS. {e}')
            raise Exception(f'Что то с доступом к архиву CDDIS. {e}')

        nav_gzip = ''
        for i in file_lst:
            # из имени файла вытаскивается дата
            if 'BRDM' in i and year+day == i.split('_')[2][:7]:
                nav_gzip = i
        if nav_gzip == '':
            self.logger.warning(f'Не найден файл BRDM в архиве  CDDIS {year}{day}.')
            self.logger.info(f'Начинаем искать другой файл BRDC')
            for i in file_lst:
                if 'BRDC' in i and year+day == i.split('_')[2][:7]:
                    nav_gzip = i
        if nav_gzip == '':
            self.logger.error(f'Не нашел эфемериды в архиве CDDIS {year}{day}.')
            raise Exception(f'Не нашел эфемериды в архиве CDDIS {year}{day}.')

        self.logger.info(f'File {nav_gzip} downloading')
        try:
            ftps.retrbinary("RETR " + nav_gzip,
                            open(os.path.join(path_dir, nav_gzip), 'wb').write)
        except Exception as e:
            self.logger.error(f'Что то случилось со скачиванием файла {nav_gzip} с CDDIS. {e}')
            raise Exception(f'Что то случилось со скачиванием файла {nav_gzip} с CDDIS. {e}')

        try:
            ftps.quit()
        except Exception as e:
            self.logger.error(e)

        self.logger.info(f'Начинаем разархивировать файл {nav_gzip} с архива CDDIS')
        try:
            with gzip.open(os.path.join(path_dir, nav_gzip), 'rb') as f_in:
                with open(os.path.join(path_dir, nav_gzip[:nav_gzip.rfind('.')]), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        except Exception as e:
            self.logger.error(f'Что то случилось с разархвивацией файла {nav_gzip} CDDIS. {e}')
            raise Exception(f'Что то случилось с разархвивацией файла {nav_gzip} CDDIS. {e}')

        if delete_gz:
            try:
                os.remove(os.path.join(path_dir, nav_gzip))
            except Exception as e:
                self.logger.error(f'Что то случилось с удалением файла nav.gzip {os.path.join(path_dir, nav_gzip)}. {e}')
                raise Exception(f'Что то случилось с удалением файла nav.gzip {os.path.join(path_dir, nav_gzip)}. {e}')

        return os.path.join(path_dir, nav_gzip[:nav_gzip.rfind('.')])

    def get_daily_obs(self, path_dir, point, year, day, delete_gz=True):

        """
        TODO
        Доделать поиск ринекс 3 версии, пока только 2
        Добавить возможность выбора не только файлов измерений но и эфемерид
        """

        year = str(year)
        day = str(day).zfill(3)
        print('')

        self.logger.info(f'Ищем измерения в архиве CDDIS')
        try:
            ftps = FTP_TLS(host='gdc.cddis.eosdis.nasa.gov')
            ftps.login(user='anonymous', passwd='anonymous')
            ftps.prot_p()
            ftps.cwd(f'gnss/data/daily/{year}/{day}/{year[2:]}o/')
            file_lst = ftps.nlst()
        except Exception as e:
            self.logger.error(f'Что то с доступом к архиву CDDIS. {e}')
            raise Exception(f'Что то с доступом к архиву CDDIS. {e}')

        obs_gzip = ''
        for i in file_lst:
            if point+day in i:
                obs_gzip = i
        if obs_gzip == '':
            self.logger.error(f'Не нашел измерения в архиве CDDIS {point}-{year}-{day}.')
            raise Exception(f'Не нашел измерения в архиве CDDIS {point}-{year}-{day}.')

        self.logger.info(f'Начинаем скачивать файл с архива CDDIS {obs_gzip}')
        try:
            ftps.retrbinary("RETR " + obs_gzip, open(os.path.join(path_dir, obs_gzip), 'wb').write)
        except Exception as e:
            self.logger.error(f'Что то случилось со скачиванием файла {obs_gzip} с CDDIS. {e}')
            raise Exception(f'Что то случилось со скачиванием файла {obs_gzip} с CDDIS. {e}')

        try:
            ftps.quit()
        except Exception as e:
            self.logger.error(e)

        self.logger.info(f'Начинаем разархивировать файл {obs_gzip} с архива CDDIS')
        try:
            with gzip.open(os.path.join(path_dir, obs_gzip), 'rb') as f_in:
                with open(os.path.join(path_dir, obs_gzip[:obs_gzip.rfind('.')]), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        except Exception as e:
            self.logger.error(f'Что то случилось с разархвивацией файла {obs_gzip} CDDIS. {e}')
            raise Exception(f'Что то случилось с разархвивацией файла {obs_gzip} CDDIS. {e}')

        if delete_gz:
            try:
                os.remove(os.path.join(path_dir, obs_gzip))
            except Exception as e:
                self.logger.error(f'Что то случилось с удалением файла nav.gzip {os.path.join(path_dir, obs_gzip)}. {e}')

        self.logger.handlers.clear()
        return os.path.join(path_dir, obs_gzip[:obs_gzip.rfind('.')])
