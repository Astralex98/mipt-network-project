# mipt-network-project
Проект по курсу "Архитектура компьютерных сетей"

## Постановка задачи
Текущий проект - это демо-версия программы, осуществляющей автоматизированное и гарантированное обновление информационной справочной системы(ИСС). В демо-версии вынесена важная составляющая обновления ИСС - автоматизированное и гарантированное скачивание баз данных с ftp-сервера работодателя на компьютер пользователя. Скачивание происходит по sftp-протоколу. Сама же ИСС разбивается на следующие составляющие:

1. Скачивание баз данных
2. Проведение оперативных обновлений
3. Обновление регистрационных файлов

Для реализации приведенных составляющих необходимо было реализовать следующие возможности:

1. Очистка кеша ИСС
2. Запуск/остановка службы ИСС
3. Формирование файла-отчета и отправка его на ftp-сервер

Поскольку для тестирования программы (не демо-версии) нужно дополнительно устанавливать ИСС, то я решил сделать демо-версию. При этом для ясности выложил jupyter-notebook как для программы (DTE.ipynb), так и для ее демо-версии (DTE_Demo.ipynb).

## Краткое описание проекта

**Входные данные:**
1. Файл FlagBase.txt, сигнализирующий о необходимости начать скачивание баз данных с ftp-сервера. Этот файл должен быть размещен на ftp-сервере. Если этот файл есть, то программа активируется и начинает свою работу. 
2. Файл BaseList.xml, который содержит список скачиваемых файлов с их характеристиками (название, объем и md5). В демонстрационных целях объем BaseList.xml был сильно сокращен (всего 4 файла), и файлы специально подобраны (суммарный объем чуть меньше 1Гб). При нормальной скорости скачивания (50Мбит/секунду) базы данных должны скачаться за 3 минуты. Файл BaseList.xml так же, как и FlagBase.txt, должен быть размещен на ftp-сервере. 

**Выходные данные:**
Скачанные базы данных

Подробное описание проекта см. DTE_Demo.ipynb

## Установка

### Python
Для работы проекта требуется наличие python. Тестирование проводилось на версии 3.8.5.

### Установка виртуального окружения

#### Обозначение
path_to_py_folder - это полный путь к папке mipt-network-project, в которой находится DTE_Demo.py

#### Windows
1. python -m venv path_to_py_folder - создаем виртуальное окружение в папке path_to_py_folder
2. path_to_py_folder\Scripts\activate.bat - активируем созданное виртуальное окружение
3. pip install -r path_to_py_folder\requirements.txt - устаналвиваем в виртуальное окружение необходимые библиотеки для работы скрипта
4. path_to_py_folder\Scripts\deactivate.bat - деактивируем созданное виртуальное окружение

#### Linux
1. python -m venv path_to_py_folder - создаем виртуальное окружение в папке path_to_py_folder
2. source path_to_py_folder/bin/activate -       активируем созданное виртуальное окружение
3. pip install -r  path_to_py_folder/requirements.txt - устаналвиваем в виртуальное окружение необходимые библиотеки для работы скрипта
4. deactivate - деактивируем созданное виртуальное окружение

## Использование

В конфигурационном файле Config.ini нужно указать следующие параметры:
1. path_to_download_files_from_server - путь к папке, куда будут скачиваться базы данных.
2. logs - путь к папке, где будут сохраняться логи

Далее нужно активировать виртуальное окружение и запустить файл DTE_Demo.py

### Windows
1. path_to_py_folder\Scripts\activate.bat
2. python path_to_py_folder\DTE_Demo.py
3. path_to_py_folder\Scripts\deactivate.bat

### Linux
1. source path_to_py_folder/bin/activate
2. python path_to_py_folder/DTE_Demo.py
3. deactivate
    





  



