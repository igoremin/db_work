#!/home/yulia/www/db_work/v_server/bin/python3
def create_new_file(name, base_big_object):
    from .models import FileAndImageCategory, FileForObject
    from db_main.settings import BASE_DIR
    from openpyxl import Workbook
    from openpyxl.styles import NamedStyle, Font, Border, Side, Alignment, colors
    from openpyxl.utils.exceptions import IllegalCharacterError
    import datetime
    import os

    file_name = f'{name}_{datetime.datetime.today().strftime("%d-%m-%Y_%H-%M")}.xlsx'

    wb = Workbook()

    sheet = wb['Sheet']
    wb.remove(sheet)

    wb.create_sheet(name)
    sheet = wb[name]

    sheet.column_dimensions['A'].width = 60
    sheet.column_dimensions['B'].width = 15
    sheet.column_dimensions['C'].width = 20
    sheet.column_dimensions['D'].width = 35
    sheet.column_dimensions['E'].width = 40
    sheet.column_dimensions['F'].width = 35

    header = NamedStyle(name="header")
    header.font = Font(bold=True, color=colors.BLUE, size=15)
    header.border = Border(bottom=Side(border_style="thin"))
    header.alignment = Alignment(horizontal="center", vertical="center")

    sheet.append(['Название', 'Мера', 'Количество', 'Инв. номер', 'Код справочника'])

    header_row = sheet[1]
    for cell in header_row:
        cell.style = header

    part_row = NamedStyle(name='part_header')
    part_row.font = Font(bold=True, color='00FF0000', size=10)
    part_row.border = Border(bottom=Side(border_style="thin"))
    part_row.alignment = Alignment(horizontal="left", vertical='center')

    r = 0
    all_parts = base_big_object.get_unique_parts()

    for part in all_parts:
        part_data = part.base.simple_components.all().values_list(
            'simple_object__name',
            'simple_object__measure',
            'amount',
            'simple_object__base_object__inventory_number',
            'simple_object__base_object__directory_code',
        )
        if part_data:
            sheet.append([part.full_name, None, None, None, None])
            row = sheet[len(sheet['A'])]
            for cell in row:
                cell.style = part_row

            for data in part_data:
                try:
                    sheet.append(data)
                    r += 1

                except IllegalCharacterError:
                    pass

    path = os.path.join(BASE_DIR, f'media/results_files/')
    if os.path.isdir(path) is False:
        os.makedirs(path, mode=0o777)

    wb.save(f'{path}/{file_name}')

    category, created = FileAndImageCategory.objects.get_or_create(
        big_object=base_big_object, name='Сформированные файлы'
    )
    new_file = FileForObject(
        category=category,
        file=f'results_files/{file_name}'
    )
    new_file.save()


def data_base_backup(manual_start=False):
    import yadisk
    from datetime import datetime
    import os
    import shutil
    import zipfile
    from pathlib import Path

    base_dir = Path(__file__).resolve().parent.parent

    if os.path.isfile(base_dir / 'db_size.txt'):
        with open(base_dir / 'db_size.txt', 'r', encoding='utf-8') as old_db_size_file:
            old_size = int(old_db_size_file.read().strip())
    else:
        old_size = 0

    if old_size != os.path.getsize(base_dir / 'db.sqlite3') or manual_start is True:

        proxies = {
            'http': 'squid.sao.ru:8080',
            'https': 'squid.sao.ru:8080',
        }

        # Создаем в каталоге проекта новую папку для записи в нее сформированного zip файла
        path = base_dir / 'backup'
        if os.path.isdir(path) is False:
            os.makedirs(path, mode=0o777)

        status = {'status': True}

        date = datetime.strftime(datetime.now(), "%d.%m.%Y-%H.%M.%S")
        file_name = 'db_backup'

        try:
            with open(base_dir / 'db_main/files/token.txt', 'r') as token_file:
                token = token_file.readline().strip()

            y = yadisk.YaDisk(token=token)

            # Проверяем есть ли на диске необходимая папка для записи в нее бэкапа
            # Если папки нет то создаем ее
            dir_list = list(y.listdir("/", proxies=proxies))
            names = set()
            for d in dir_list:
                names.add(d['name'])

            if 'data_base' not in names:
                y.mkdir('/data_base', proxies=proxies)

            # В корневом каталоге создаем новую папку у сказанием текущей даты и времени
            y.mkdir(f'/data_base/{date}', proxies=proxies)

            # Формируем zip файл на основе каталога media
            shutil.make_archive(f'{path}/{file_name}', 'zip', base_dir / 'media')

            # Добавлем в созданый zip файл базу данных
            with zipfile.ZipFile(f'{path}/{file_name}.zip', 'a') as zip_file:
                zip_file.write(base_dir / 'db.sqlite3', arcname='db.sqlite3')

            # Загружаем итоговый zip файл на яндекс диск
            y.upload(path_or_file=f'{path}/{file_name}.zip', dst_path=f'/data_base/{date}/{file_name}.zip',
                     proxies=proxies)

            # Удаляем папку с zip файлом
            shutil.rmtree(path)
            print('DONE')
        except Exception as err:
            shutil.rmtree(path, ignore_errors=True)
            status['status'] = False
            status['err'] = err
        finally:
            with open(base_dir / 'db_size.txt', 'w', encoding='utf-8') as old_db_size_file:
                old_db_size_file.write(str(os.path.getsize(base_dir / 'db.sqlite3')))

            if status['status'] is True:
                return {'status': True}
            else:
                return {'status': False, 'err': status['err']}
    else:
        return {'status': False, 'err': 'База данных не изменилась, бэкап не сделан.'}


if __name__ == '__main__':
    backup = data_base_backup()
