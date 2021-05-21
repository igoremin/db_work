def create_new_file(name, all_data, big_object=None):
    from .models import FileAndImageCategoryForBigObject, FileForBigObject
    from db_main.settings import BASE_DIR
    from openpyxl import Workbook
    from openpyxl.styles import NamedStyle, Font, Border, Side, Alignment, colors
    from openpyxl.utils.exceptions import IllegalCharacterError
    import datetime
    import os

    print('WRITE')

    file_name = f'{name}_{datetime.datetime.today().strftime("%d-%m-%Y_%H-%M")}.xlsx'

    wb = Workbook()

    sheet = wb['Sheet']
    wb.remove(sheet)

    wb.create_sheet(name)
    sheet = wb[name]

    sheet.column_dimensions['A'].width = 60
    sheet.column_dimensions['B'].width = 20
    sheet.column_dimensions['C'].width = 35
    sheet.column_dimensions['D'].width = 35
    sheet.column_dimensions['E'].width = 40
    sheet.column_dimensions['F'].width = 40

    header = NamedStyle(name="header")
    header.font = Font(bold=True, color=colors.BLUE, size=15)
    header.border = Border(bottom=Side(border_style="thin"))
    header.alignment = Alignment(horizontal="center", vertical="center")

    sheet.append(['Название', 'Мера', 'Инв. номер', 'Код справочника', 'Количество'])

    header_row = sheet[1]
    for cell in header_row:
        cell.style = header

    r = 0

    for data in all_data:
        try:
            sheet.append(data)
            r += 1

        except IllegalCharacterError:
            pass

    path = os.path.join(BASE_DIR, f'media/results_files/')
    if os.path.isdir(path) is False:
        os.makedirs(path, mode=0o777)

    wb.save(f'{path}/{file_name}')

    if big_object:
        category, created = FileAndImageCategoryForBigObject.objects.get_or_create(
            big_object_id=big_object.id, name='Сформированные файлы'
        )
        new_file = FileForBigObject(
            big_object_id=big_object.id,
            category=category,
            file=f'results_files/{file_name}'
        )
        new_file.save()
