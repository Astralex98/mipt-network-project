#!/usr/bin/env python
# coding: utf-8

# # Демо-версия автоматизированного и гарантированного обновления пользователя

# ## Подключаем небходимые библиотеки и задаем параметры конфигурации

# In[1]:


import sys
import configparser
import os
import logging
import datetime
from dateutil import parser
import psutil
import time
import xml.etree.ElementTree as ET
from lxml import etree
import hashlib
from datetime import datetime, timedelta
import paramiko
from stat import S_ISDIR, S_ISREG
import shutil
import subprocess
import requests


# In[2]:


# Отключаем лишние логи, которые возникают из-за использования paramiko.
logging.getLogger("paramiko").setLevel(logging.WARNING)


# In[3]:


# Путь к файлу с конфигами
# Те переменные, которые часто используются в коде и не должны изменять своего значения, я назвал, используя
# заглавные буквы. Например, CUR_DIR

abspath = os.path.abspath(__file__)
CUR_DIR = os.path.dirname(abspath)
os.chdir(CUR_DIR)

PATH_TO_CONFIG = 'Config.ini'

# Считываем конфигурации из файла Config_lin.ini
read_config = configparser.ConfigParser()
read_config.read(PATH_TO_CONFIG)

# Имя клиента
CLIENT_NAME = read_config.get('Information', 'client')

# Внешний ip-адрес ftp-сервера, с которого производится скачивание файлов
HOST = '62.183.112.196'

# Порт, по которому подключаемся по sftp
PORT = 17523

# Логин и пароль для пользователя
USER = read_config.get('Information', 'user')
PASSWD = read_config.get('Information', 'passwd')

# Папка на сервере, где хранятся списки скачиваемых файлов и их характеристики
SERVER_BASE_FOLDER = read_config.get('Information', 'server_base_folder')

# Путь к папке на локальном компьютере пользователя, куда нужно скачивать файлы
PATH_TO_DOWNLOAD = read_config.get('Information', 'path_to_download_files_from_server')

# Название скачиваемого xml файла
XML_NAME = read_config.get('Information', 'xml_name')

# Путь к скачиваемому xml файлу на сервере
XML_PATH = '/' + CLIENT_NAME.upper() + '/FILESLISTS/'

# Путь к папке FlagsList
PATH_TO_FLAG = '/' + CLIENT_NAME.upper() + '/FLAGS'

# Путь к файлу с логами. Тут же проверяем, создана ли папка с именем PATH_TO_LOG
PATH_TO_LOG = read_config.get('Information', 'logs')
if (os.path.isdir(PATH_TO_LOG) == False):
    os.mkdir(PATH_TO_LOG)

# Путь к папке на серверной части, куда нужно отправлять логи
PATH_TO_SERVER_LOGS = '/' + CLIENT_NAME.upper() + '/LOGS/'


# In[4]:


# Функция, находящая hash файла
def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# In[5]:


# Если соединения с ftp-сервером нет, то при инициализации соединения выпадет исключение и исполнение программы
# прервется. Поэтому, чтобы исполнение программы не прервалось, сделан цикл while пока соединение с сервером не 
# восстановится
retry = True
while (retry):
    
    try:
        transport = paramiko.Transport((HOST,PORT))
        
        # Авторизуемся в созданном канале 
        transport.connect(None,USER,PASSWD)

        # Инициализируем sftp
        sftp = paramiko.SFTPClient.from_transport(transport)

        retry = False
    
    except paramiko.ssh_exception.SSHException as e:
        retry = True


# ### 1. Проверка

# В случае, если скрипт был запущен заново (было отключение света или еще что-то), то нужно понять - что нужно сейчас делать? Для этого используется класс **Checker**, который проверяет текущее состояние дел. Например, нужно ли скачивать стандартные обновления?

# Введем понятие **модуль**. Под **модулем** стоит понимать:
# 
# - Обновление баз данных (стандартное обновление)
# 
# - Обновление регистрационного файла
# 
# - Оперативные обновления
# 
# - Очистка кеша
# 
# - Отправка отчета

# Каждый модуль характеризуется своим флагом, который выложен на ftp-сервере. Если этот флаг есть - значит, соответствующий модуль нужно сделать. Иначе - модуль делать не нужно. По окончании каждого модуля соответствующий флаг удаляется. 
# 
# В демо-версии только один модуль - обновление баз данных.

# In[6]:


class Checker:
    
    def __init__(self):
        
        # Нужно ли начинать обновление?
        self.do_we_need_update_data_base = False
    
    # Проверяем наличие флага в соответствующей папке FLAGS.
    # Если флаг есть, то соответствующий модуль еще не выполнен
    def check_flag(self, sftp):

        # Проходимся по содержимому папки FLAGS
        for entry in sftp.listdir_attr(PATH_TO_FLAG):
            mode = entry.st_mode
            
            # Если флага FlagBase.txt найден, то базы данных еще не установлены
            if (S_ISREG(mode) and entry.filename=='FlagBase.txt'):
                self.do_we_need_update_data_base = True
    
    # Совместили все проверки внутри одной, что позволяет сократить код
    def check_all(self, sftp):
        self.check_flag(sftp)


# In[7]:


# Функция по удалению файлов из некоторой папки
def delete_files_from_directory(path_to_directory):
    
    # Находим список файлов в заданной папке
    dir_files = [f for f in os.listdir(path_to_directory) if os.path.isfile(os.path.join(path_to_directory, f))]
    
    # Удаляем файлы из папки 
    for f in dir_files:
        os.remove(os.path.join(path_to_directory,f))


# ### 2. Скачивание баз данных

# #### 2.1. Функция скачивания одного файла с сервера

# In[18]:


# Функция закачки файла
#
# На вход подается название скачиваемого файла и папка на сервере, куда нужно перейти
# 
# На выходе получаем скачанный файл. 

def download_one_file(download_file, folder_in_server):

    # Локальный путь для загруженного с сервера файла
    local_file_name = os.path.join(PATH_TO_DOWNLOAD,download_file)

    # Путь к файлу на ftp-сервере
    remote_path = folder_in_server + '/' + download_file
    
    # Скачиваем файл
    sftp.get(remote_path, local_file_name)

    # Поскольку при скачивании файла изменяется его дата модификации, то нужно 
    # заменить новую дату модификации на старую дату.
    utime = sftp.stat(remote_path).st_mtime
    mtime = (datetime.fromtimestamp(utime))
    os.utime(local_file_name, (float(mtime.timestamp()), float(mtime.timestamp())))


# #### 2.2. Функция проверки наличия свободного места перед скачиванием

# In[19]:


def check_space(files_to_download):
    
    # Задача функции - узнать объем файлов, который нужно докачать для обновления. 
    # Идея алгоритма функции - пройтись по списку скачиваемых файлов и узнать, сколько файлов уже корректно скачаны.
    # Функция, узнав, какие файлы скачаны корректно, а какие - нет, определяет какой объем файлов еще нужно
    # докачать.
    
    logger.info("Началась проверка свободного места на диске")
    disk_free_space_needed = 0
    current_disk_space = psutil.disk_usage(PATH_TO_DOWNLOAD).free

    # Заводим массив для хранения данных о корректности файлов
    # Если в i-ом элементе хранится True, то i-ый файл скачан и корректен.
    # Иначе - в i-ом элементе хранится False.
    are_files_correct = []

    for download_file in files_to_download:

        # Локальный путь для загруженного с сервера файла
        local_file_name = os.path.join(PATH_TO_DOWNLOAD, download_file.attrib['Name'])

        # Вначале проверяем - скачан ли уже файл или нет
        if ((os.path.isfile(local_file_name) == True)):

            # Если файл скачан полностью, то заносим его в массив как корректно скачанный файл
            if (md5(local_file_name).upper() == download_file.attrib['md5']):
                are_files_correct.append(True)

            # Если файл скачан, но не полностью
            else:
                are_files_correct.append(False)

                # Находим, сколько уже скачано
                already_downloaded = os.path.getsize(local_file_name)

                # Находим сколько нужно скачать, т.е. размер файла из xml
                need_to_download = int(download_file.attrib['Size'])

                # Сколько осталось скачать
                rest_part_of_file = need_to_download - already_downloaded

                # Поскольку файл скачан частично, то нужно прибавлять размер
                # оставшейся части файла для скачивания
                disk_free_space_needed += rest_part_of_file

        # Если скачивание файла еще не началось
        else:
            are_files_correct.append(False)

            # Поскольку файл еще не начал скачиваться, то прибавляем весь его размер
            disk_free_space_needed += int(download_file.attrib['Size'])
    
    # Делаем зазор в размере 100 байт между необходимой для обновления баз данных памятью (disk_free_space_needed)
    # и текущим свободным пространством (current_disk_space)
    if (disk_free_space_needed > (current_disk_space + 100)):
        mes1 = "Не хватает места на диске!"
        mes2 = "Необходимо {:.2f}Гб, но доступно только {:.2f}Гб".format((disk_free_space_needed / 10**9), 
                                                                     (current_disk_space / 10**9))
        mes = mes1 + '\n' + mes2
        logger.error(mes)
        
        # Отправляем лог-файл на сервер
        old_logs_path = os.path.join(PATH_TO_LOG, LOG_NAME)
        new_logs_path = PATH_TO_SERVER_LOGS + LOG_NAME
        sftp.put(old_logs_path, new_logs_path)
        sys.exit(1)
    
    else:
        mes1 = "На диске достаточно свободного места (Необходимо - {:.1f}Гб, Доступно - {:.1f}Гб)".format((disk_free_space_needed / 10**9), (current_disk_space / 10**9))
        
        mes2 = "Начинается скачивание файлов..."
        mes = mes1 + ' ' + mes2
        logger.info(mes)
        
        return are_files_correct


# #### 2.3. Заключительная функция проверки, сверяющая хеши скачанных файлов с хешами из xml

# In[20]:


def check_md5(path_to_files, files_to_download):
    
    logger.info("Началась заключительная проверка файлов по md5")
    
    # Проходимся в цикле по списку скачиваемых файлов и проверяем их md5
    for pos, download_file in enumerate(files_to_download):

        # Извлекаем имя файла
        download_file_name = download_file.attrib['Name']
        
        full_name = os.path.join(path_to_files, download_file_name)

        # Если файл корректный, то идем дальше
        # Иначе - записываем ошибку в лог-файл и завершаем работу программы
        if (md5(full_name).upper() == download_file.attrib['md5']):
            pass
        else:
            mes = "Md5 файла {} не совпадает с md5 в xml-файле!".format(download_file_name)
            logger.error(mes)
            
            old_logs_path = os.path.join(PATH_TO_LOG, LOG_NAME)
            new_logs_path = PATH_TO_SERVER_LOGS + LOG_NAME
            sftp.put(old_logs_path, new_logs_path)
            sys.exit(1)
    
    logger.info("Заключительная проверка файлов по md5 успешно завершена!")


# #### 2.4. Функция загрузки всех файлов (баз данных) с сервера

# In[21]:


def download_all_files(files_to_download, are_files_correct):
    # Проходимся в цикле по списку скачиваемых файлов и скачиваем их
    for pos, download_file in enumerate(files_to_download):
        
        # Извлекаем имя скачиваемого файла
        download_file_name = download_file.attrib['Name']
        
        mes = "Начинаем скачивать файл {}!".format(download_file_name)
        logger.info(mes)

        # Проверяем, скачан ли файл. Если файл скачан успешно, то просто переходим к следующему файлу
        if (are_files_correct[pos] == True):
            mes = "Файл {} скачан успешно!".format(download_file_name)
            logger.info(mes)
            continue
        else:
            pass

        # Скачиваем файл
        download_one_file(download_file_name, SERVER_BASE_FOLDER)

        # Заводим переменную "состояния" для каджого файла.
        # По умолчанию считаем, что текущий файл некорректен.
        # Если после проверки файл окажется корректным, то изменим значение переменной "состояния"
        is_file_correct = False


        # Будем перезакачивать файл до тех пор, пока он не станет корректным. 
        while (is_file_correct == False):
            
            full_name = os.path.join(PATH_TO_DOWNLOAD, download_file_name)

            # Если файл корректный, то изменяем переменную "состояния"
            if (md5(full_name).upper() == download_file.attrib['md5']):
                is_file_correct = True

            # Если файл некорректный, то закачиваем файл заново
            else:

                # Докачиваем файл
                download_one_file(download_file_name, SERVER_BASE_FOLDER)

        mes = "Файл {} скачан успешно!".format(download_file_name)
        logger.info(mes)
    
    logger.info("Скачивание файлов завершено! Начинаем заключительную проверку файлов по md5 ...")       


# ### Основной код

# In[ ]:


############################################### Формируем лог-файл ###############################################

# Формируем имя для лога
dt = datetime.today()
year = str(dt.year)
month = '{:02d}'.format(dt.month)
day = '{:02d}'.format(dt.day)
hour = '{:02d}'.format(dt.hour)
minute = '{:02d}'.format(dt.minute)

LOG_NAME = "Logs_{}_{}_{}_{}_{}.txt".format(year, month, day, hour, minute)

# Задаем конфигурации для формирования файла логов
logging.basicConfig(filename=os.path.join(PATH_TO_LOG,LOG_NAME),
                    filemode = 'a',
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s', 
                    datefmt='%d/%m/%Y %H:%M:%S')

logger = logging.getLogger("Logs")


# In[ ]:


logger.info("Начало работы программы")


# In[ ]:


def main():
    # Создаем объект класса Checker
    checker = Checker()

    # Проверяем, установлены ли базы данных
    checker.check_all(sftp)

    # Если нужно скачать базы данных, то скачиваем их
    if (checker.do_we_need_update_data_base == True):

        logger.info("Начинается скачивание и установка баз данных")

        # Скачиваем xml-файл со списком закачиваемых томов и их характеристиками
        download_one_file(XML_NAME, XML_PATH)

        # Формируем путь к xml-файлу
        xml = os.path.join(PATH_TO_DOWNLOAD, XML_NAME)

        tree = ET.parse(xml)
        files_to_download = tree.getroot()

        # Проверяем наличие свободного пространства для закачки
        are_files_correct = check_space(files_to_download)

        # Начинаем закачку/докачку файлов с сервера
        download_all_files(files_to_download, are_files_correct)

        # Заключительная проверка уже скачанных файлов
        check_md5(PATH_TO_DOWNLOAD, files_to_download)

        # Удаляем флаг обновлений баз данных
        base_flag = PATH_TO_FLAG + '/FlagBase.txt'
        sftp.remove(base_flag)

        logger.info("Скачивание и установка баз данных завершены успешно!")

    # Записываем в лог информацию о конце работы программы
    logger.info("Конец работы программы")

    # Закрываем файл с логами
    logging.shutdown()
    
    # Отправляем файл с логами в соответствующую папку на сервере
    old_logs_path = os.path.join(PATH_TO_LOG, LOG_NAME)
    new_logs_path = PATH_TO_SERVER_LOGS + LOG_NAME
    sftp.put(old_logs_path, new_logs_path)

    # Закрываем канал связи
    transport.close()


# In[ ]:


try:
    main()
except Exception as e:
    
    logging.exception(e)
    
    # Формируем лог и отправляем его на сервер
    old_logs_path = os.path.join(PATH_TO_LOG, LOG_NAME)
    new_logs_path = PATH_TO_SERVER_LOGS + LOG_NAME
    sftp.put(old_logs_path, new_logs_path)

