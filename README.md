# mipt-network-project
Проект по курсу "Архитектура компьютерных сетей"

## Содержимое репозитория
1. DTE_Demo.py - реализация проекта в виде py-файла.
2. DTE_Demo.ipynb - jupyter-notebook, являющийся копией DTE_Demo.py . В данном jupyter-notebook с наглядным оформлением представлен код из DTE_Demo.py
3. DTE.ipynb - jupyter-notebook, являющийся реализацией автоматизированной системы обновления баз данных информационно-справочной системы. В этом jupyter-notebook содержится как модуль из DTE_Demo, так и остальные модули, необходимые для реализации. Вся необходимая информация о модулях, терминологии, сути проекта и других вопросах содержится в разделе "Описание проекта".
4. requirements.txt - текстовый файл, необходимый для установки библиотек.
5. Config.ini - конфигурационный файл, в котором хранятся настройки программы. Информация о настраиваемых параметрах в Config.ini описана в разделе "Настройка файла Config.ini". 

## Описание проекта
Описание проекта: https://drive.google.com/file/d/1IVQ27oTLzBtlOrLSrPucAEnxdWFIKRR7/view?usp=sharing

## Установка

### Python
Для работы проекта требуется наличие python. Тестирование проводилось на версии 3.8.5.

### Установка виртуального окружения

#### Используемое обозначение
path_to_py_folder - это полный путь к папке mipt-network-project, в которой находится DTE_Demo.py

#### Windows
1. python -m venv path_to_py_folder - создаем виртуальное окружение в папке path_to_py_folder
2. path_to_py_folder\Scripts\activate - активируем созданное виртуальное окружение
3. pip install -r path_to_py_folder\requirements.txt - устаналвиваем в виртуальное окружение необходимые библиотеки для работы скрипта
4. path_to_py_folder\Scripts\deactivate.bat - деактивируем созданное виртуальное окружение

#### Linux
1. python -m venv path_to_py_folder - создаем виртуальное окружение в папке path_to_py_folder
2. source path_to_py_folder/bin/activate -       активируем созданное виртуальное окружение
3. pip install -r  path_to_py_folder/requirements.txt - устаналвиваем в виртуальное окружение необходимые библиотеки для работы скрипта
4. deactivate - деактивируем созданное виртуальное окружение

## Использование

### Настройка файла Config.ini
В конфигурационном файле Config.ini нужно указать следующий параметр: 

path_to_download_files_from_server - полный путь к существующей папке, куда будут скачиваться базы данных. 

Остальные параметры уже указаны и их изменять не нужно.

### Запуск файла DTE_Demo.py в виртуальном окружении

#### Windows
1. path_to_py_folder\Scripts\activate.bat
2. python path_to_py_folder\DTE_Demo.py
3. path_to_py_folder\Scripts\deactivate.bat

#### Linux
1. source path_to_py_folder/bin/activate
2. python path_to_py_folder/DTE_Demo.py
3. deactivate







  



