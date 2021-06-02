def create_new_file(name, base_big_object):
    from .models import FileAndImageCategoryForBigObject, FileForBigObject
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
            'simple_object__inventory_number',
            'simple_object__directory_code',
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

    category, created = FileAndImageCategoryForBigObject.objects.get_or_create(
        big_object_id=base_big_object.id, name='Сформированные файлы'
    )
    new_file = FileForBigObject(
        big_object_id=base_big_object.id,
        category=category,
        file=f'results_files/{file_name}'
    )
    new_file.save()
