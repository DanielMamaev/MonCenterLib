import logging
from ftplib import FTP_TLS
import os
import gzip
import shutil


class CDDISClient:
    def get_daily_multi_gnss_brd_eph(self, path_dir, year, day, input_logger=None, delete_gz=True):
        year = str(year)
        day = str(day).zfill(3)

        logger = input_logger

        if not input_logger:
            logger = logging.getLogger('get_daily_multi_gnss_brdc_eph')
            logger.handlers.clear()
            logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)
        print('')

        logger.info(f'Ищем эфемериды в архиве CDDIS')
        try:
            ftps = FTP_TLS(host='gdc.cddis.eosdis.nasa.gov')
            ftps.login(user='anonymous', passwd='anonymous')
            ftps.prot_p()
            ftps.cwd(f'gnss/data/daily/{year}/brdc')
            file_lst = ftps.nlst()
        except Exception as e:
            logger.error(f'Что то с доступом к архиву CDDIS. {e}')
            return False

        nav_gzip = ''
        for i in file_lst:
            # из имени файла вытаскивается дата
            if 'BRDM' in i and year+day == i.split('_')[2][:7]:
                nav_gzip = i
        if nav_gzip == '':
            logger.warning(f'Не найден файл BRDM в архиве  CDDIS {year}{day}.')
            logger.info(f'Начинаем искать другой файл BRDC')
            for i in file_lst:
                if 'BRDC' in i and year+day == i.split('_')[2][:7]:
                    nav_gzip = i
        if nav_gzip == '':
            logger.error(f'Не нашел эфемериды в архиве CDDIS {year}{day}.')
            return False

        logger.info(f'Начинаем скачивать файл с архива CDDIS {nav_gzip}')
        try:
            ftps.retrbinary("RETR " + nav_gzip,
                            open(os.path.join(path_dir, nav_gzip), 'wb').write)
        except Exception as e:
            logger.error(
                f'Что то случилось со скачиванием файла {nav_gzip} с CDDIS. {e}')
            return False

        try:
            ftps.quit()
        except Exception as e:
            logger.error(e)

        logger.info(f'Начинаем разархивировать файл {nav_gzip} с архива CDDIS')
        try:
            with gzip.open(os.path.join(path_dir, nav_gzip), 'rb') as f_in:
                with open(os.path.join(path_dir, nav_gzip[:nav_gzip.rfind('.')]), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        except Exception as e:
            logger.error(
                f'Что то случилось с разархвивацией файла {nav_gzip} CDDIS. {e}')
            return False

        if delete_gz:
            try:
                os.remove(os.path.join(path_dir, nav_gzip))
            except Exception as e:
                logger.error(
                    f'Что то случилось с удалением файла nav.gzip {os.path.join(path_dir, nav_gzip)}. {e}')

        return os.path.join(path_dir, nav_gzip[:nav_gzip.rfind('.')])

    def get_daily_obs(self, path_dir, point, year, day, input_logger=None, delete_gz=True):

        """
        TODO
        Доделать поиск ринекс 3 версии, пока только 2
        Добавить возможность выбора не только файлов измерений но и эфемерид
        """

        year = str(year)
        day = str(day).zfill(3)

        logger = input_logger
        if not input_logger:
            logger = logging.getLogger('get_daily_obs')
            logger.handlers.clear()
            logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)
        print('')

        logger.info(f'Ищем измерения в архиве CDDIS')
        try:
            ftps = FTP_TLS(host='gdc.cddis.eosdis.nasa.gov')
            ftps.login(user='anonymous', passwd='anonymous')
            ftps.prot_p()
            ftps.cwd(f'gnss/data/daily/{year}/{day}/{year[2:]}o/')
            file_lst = ftps.nlst()
        except Exception as e:
            logger.error(f'Что то с доступом к архиву CDDIS. {e}')
            return False

        obs_gzip = ''
        for i in file_lst:
            if point+day in i:
                obs_gzip = i
        if obs_gzip == '':
            logger.error(f'Не нашел измерения в архиве CDDIS {point}-{year}-{day}.')
            return False

        logger.info(f'Начинаем скачивать файл с архива CDDIS {obs_gzip}')
        try:
            ftps.retrbinary("RETR " + obs_gzip, open(os.path.join(path_dir, obs_gzip), 'wb').write)
        except Exception as e:
            logger.error(f'Что то случилось со скачиванием файла {obs_gzip} с CDDIS. {e}')
            return False

        try:
            ftps.quit()
        except Exception as e:
            logger.error(e)

        logger.info(f'Начинаем разархивировать файл {obs_gzip} с архива CDDIS')
        try:
            with gzip.open(os.path.join(path_dir, obs_gzip), 'rb') as f_in:
                with open(os.path.join(path_dir, obs_gzip[:obs_gzip.rfind('.')]), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        except Exception as e:
            logger.error(f'Что то случилось с разархвивацией файла {obs_gzip} CDDIS. {e}')
            return False

        if delete_gz:
            try:
                os.remove(os.path.join(path_dir, obs_gzip))
            except Exception as e:
                logger.error(f'Что то случилось с удалением файла nav.gzip {os.path.join(path_dir, obs_gzip)}. {e}')

        logger.handlers.clear()
        return os.path.join(path_dir, obs_gzip[:obs_gzip.rfind('.')])
