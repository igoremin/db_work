from django.shortcuts import render, redirect
from .models import SimpleObject, LabName, Category, Profile, BigObject, BigObjectList, ImageForObject,\
    FileAndImageCategory, FileForObject, DataBaseDoc, BaseObject, WorkerEquipment, BaseBigObject, Room,\
    Order
from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotFound, JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q, F
from .forms import CategoryForm, SimpleObjectForm, SimpleObjectWriteOffForm, BaseBigObjectForm, \
    SimpleObjectForBigObjectForm, SearchForm, CopyBigObject, FileAndImageCategoryForm,\
    AddNewImagesForm, AddNewFilesForm, DataBaseDocForm, ChangeProfile, AddSimpleObjectToProfile, PartForBigObjectForm,\
    BigObjectForm, BaseObjectForm, CategoryListForm
from .scripts import create_new_file, data_base_backup
from .models import get_base_components


def custom_proc_user_categories_list(request):
    data = {
        'user_cat_list': 'none',
        'current_lab': 'none',
        'search_form': 'none',
        'user_info': 'none',
        'big_objects_cat': 'none',
        'rooms': 'none'
    }
    try:
        lab = request.build_absolute_uri().replace('//', '').split('/')[1]

        lab_categories_base = Category.objects.filter(lab__slug=lab, cat_type='BO')
        lab_categories_simple_equipment = Category.objects.filter(lab__slug=lab, cat_type='SO', obj_type='EQ')
        lab_categories_simple_materials = Category.objects.filter(lab__slug=lab, cat_type='SO', obj_type='MT')
        lab_categories_big = Category.objects.filter(lab__slug=lab, cat_type='BG')
        # base_categories = Category.objects.filter(lab__slug=lab, )
        search_form = SearchForm()
        workers = Profile.objects.filter(lab__slug=lab)
        user = Profile.objects.get(user_id=request.user.id)

        rooms = Room.objects.filter(lab__slug=lab)

        data = {'user_cat_list_base': lab_categories_base,
                'user_cat_list_simple_equipment': lab_categories_simple_equipment,
                'user_cat_list_simple_materials': lab_categories_simple_materials,
                'current_lab': LabName.objects.get(slug=lab),
                'search_form': search_form,
                'workers': workers,
                'user_info': user,
                'big_objects_cat': lab_categories_big,
                'rooms': rooms
                }
        if lab not in LabName.objects.values_list('slug', flat=True):
            data = {
                'user_cat_list': 'none',
                'current_lab': 'none',
                'search_form': 'none',
                'user_info': 'none',
                'big_objects_cat': 'none',
                'rooms': 'none'
            }
    except Exception:
        pass
    finally:
        return data


def paginator_module(request, objects):
    paginator = Paginator(objects, 40)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    is_paginator = page.has_other_pages()

    if page.has_previous():
        prev_url = '?page={}'.format(page.previous_page_number())
    else:
        prev_url = ''

    if page.has_next():
        next_url = '?page={}'.format(page.next_page_number())
    else:
        next_url = ''

    last_url = '?page={}'.format(paginator.num_pages)

    paginator_dict = {
        'page_object': page,
        'is_paginator': is_paginator,
        'next_url': next_url,
        'prev_url': prev_url,
        'last_url': last_url,
    }

    return page, is_paginator, next_url, prev_url, last_url, paginator_dict


def object_update_files_category(request, lab, slug, pk, object_type='big'):
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        if object_type == 'simple':
            target_object = get_object_or_404(SimpleObject, lab__slug=lab, slug=slug)
        else:
            target_object = get_object_or_404(BaseBigObject, lab__slug=lab, slug=slug)

        category = get_object_or_404(FileAndImageCategory, pk=pk)

        if request.method == 'GET':
            all_images = ImageForObject.objects.filter(category=category)
            files = FileForObject.objects.filter(category=category)
            add_new_images_form = AddNewImagesForm()
            add_new_files_form = AddNewFilesForm()
            context = {
                'images': all_images,
                'files': files,
                'object': target_object,
                'add_new_images_form': add_new_images_form,
                'add_new_files_form': add_new_files_form,
                'category': category,
            }
            return render(request, 'db_site/object_update_category_files_form.html', context=context)
        else:
            form_type = 'image'
            for key, value in request.FILES.items():
                if key == 'file':
                    form_type = key
                    break

            if form_type == 'image':
                form = AddNewImagesForm(request.POST, request.FILES)
                images = request.FILES.getlist('image')
                if form.is_valid():
                    for image in images:
                        new_image = ImageForObject(
                            category=category,
                            image=image
                        )
                        new_image.save()
            elif form_type == 'file':
                form = AddNewFilesForm(request.POST, request.FILES)
                files = request.FILES.getlist('file')
                if form.is_valid():
                    for file in files:
                        new_file = FileForObject(
                            category=category,
                            file=file
                        )
                        new_file.save()
            return redirect(object_update_files_category, lab, object_type, slug, pk)


def object_delete_image(request, lab, pk):
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        image = get_object_or_404(ImageForObject, pk=pk)
        if request.method == 'POST':
            form = request.POST
            if form['image_pk'] == str(image.pk):
                image.delete()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def object_delete_file(request, lab, pk):
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        file = get_object_or_404(FileForObject, pk=pk)
        if request.method == 'POST':
            form = request.POST
            if form['file_pk'] == str(file.pk):
                file.delete()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def home_page(request):
    context = {}
    if request.user.is_active:
        if request.user.is_superuser:
            labs = LabName.objects.all()
        else:
            labs = LabName.objects.filter(profile__user_id=request.user.id)
        context = {
            'labs': labs
        }

    return render(request, 'db_site/home_page.html', context=context)


@login_required(login_url='/login/')
def categories_list(request, lab):
    user = Profile.objects.get(user_id=request.user.id)
    if request.method == 'GET':
        if request.user.is_superuser or user.lab.slug == lab:
            categories = Category.objects.filter(lab__slug=lab, cat_type='SO')
            return render(request, 'db_site/categories_list.html', {'categories': categories, 'lab': lab})
        else:
            return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def category_add_form(request, lab):
    if request.method == 'GET':
        form = CategoryForm
        context = {
            'form': form,
            'status': 'add'
        }
        return render(request, 'db_site/category_form.html', context=context)
    else:
        form = CategoryForm(request.POST)
        if form.is_valid():
            new_category = form.save(commit=False)
            new_category.lab = get_object_or_404(LabName, slug=lab)
            form.save()
            return redirect(category_page, lab=lab, slug=new_category.slug)
        return redirect(categories_list, lab)


@login_required(login_url='/login/')
def category_update_form(request, lab, slug):
    cat = get_object_or_404(Category, slug=slug)
    if request.method == 'GET':
        form = CategoryForm(instance=cat)
        context = {
            'form': form,
            'cat_slug': slug,
            'status': 'update',
        }
        return render(request, 'db_site/category_form.html', context=context)
    else:
        form = CategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            return redirect(category_page, lab=lab, slug=cat.slug)
        return redirect(categories_list, lab)


@login_required(login_url='/login/')
def category_page(request, lab, slug):
    user = Profile.objects.get(user_id=request.user.id)
    get_object_or_404(Category, slug=slug)
    category = get_object_or_404(Category, slug=slug)
    if request.method == 'GET':
        if request.user.is_superuser or user.lab.slug == lab:
            sort = request.GET.getlist('sort')

            base_sorted = sort
            if sort:
                if 'price' in sort[0]:
                    base_sorted = [sort[0].replace('price', 'total_price')]
            else:
                sort = ['name_lower']
                base_sorted = ['name_lower']

            base_objects = BaseObject.objects.filter(category__slug=slug, lab__slug=lab).order_by(*base_sorted)
            simple_objects = SimpleObject.objects.filter(category__slug=slug, lab__slug=lab).order_by(*sort)
            big_objects = BigObject.objects.filter(
                base__category__slug=slug, base__lab__slug=lab, parent=None
            )

            if simple_objects:
                page, is_paginator, next_url, prev_url, last_url, paginator_dict = paginator_module(
                    request=request, objects=simple_objects
                )
            else:
                page, is_paginator, next_url, prev_url, last_url, paginator_dict = paginator_module(
                    request=request, objects=base_objects
                )

            prefix = ''
            if sort:
                prefix = '&sort=' + sort[0]

            context = {
                'base_objects': base_objects,
                'base_objects_count': base_objects.count(),
                'simple_objects': simple_objects,
                'simple_objects_count': simple_objects.count(),
                'big_objects': big_objects,
                'big_objects_count': big_objects.count(),
                'cat_slug': slug,
                'category': category,
                'type': 'category_page',
                'old_prefix': prefix,
            }

            context.update(paginator_dict)

            return render(request, 'db_site/objects_list.html', context=context)
        else:
            return HttpResponseNotFound("У вас нет доступа к этой странице!")


"""---------------------------------------------------------------------------------------------------------"""
"""------------------------------------------BASE OBJECTS-------------------------------------------------"""


@login_required(login_url='/login/')
def base_object_page(request, lab, slug):
    """Страница базового объекта. lab - текущая лаборатория"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        if request.method == 'GET':
            base_object = get_object_or_404(BaseObject, slug=slug)
            simple_objects = SimpleObject.objects.filter(base_object=base_object)
            cat_form = CategoryListForm(lab=lab)
            context = {
                'object': base_object,
                'simple_objects': simple_objects,
                'cat_form': cat_form,
            }
            return render(request, 'db_site/base_object_page.html', context=context)


@login_required(login_url='/login/')
def base_object_update_page(request, lab, slug):
    """Страница базового объекта. lab - текущая лаборатория"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        base_object = get_object_or_404(BaseObject, slug=slug)
        if request.method == 'GET':
            form = BaseObjectForm(instance=base_object)
            context = {
                'form': form,
                'base_object': base_object
            }
            return render(request, 'db_site/base_object_update_form.html', context=context)
        else:
            form = BaseObjectForm(request.POST, instance=base_object)
            if form.is_valid():
                form.save()
                if lab != base_object.lab.slug:
                    # Изменилась лаборатория. Необходимо найти все простые объекты связанные с данным базовым и
                    # переметить их в другую лабораторию
                    simple_objects = SimpleObject.objects.filter(base_object=base_object)
                    if simple_objects:
                        simple_objects.update(lab=base_object.lab)

            return redirect(base_object_page, lab=base_object.lab.slug, slug=base_object.slug)


@login_required(login_url='/login/')
def base_object_create_simple(request, lab, slug):
    """Страница базового объекта. lab - текущая лаборатория"""
    if request.user.is_superuser:
        base_object = get_object_or_404(BaseObject, slug=slug)
        cat_form = CategoryListForm(request.POST, lab=lab)
        if request.method == 'POST':
            if cat_form.is_valid():

                measure = '---'
                if base_object.measure:
                    base_measure = base_object.measure.lower().strip().replace('.', '')
                    if base_measure in SimpleObject.ChoicesMeasure.values:
                        measure = base_measure
                simple_object = SimpleObject(
                    base_object=base_object,
                    name=base_object.name,
                    lab=base_object.lab,
                    inventory_number=base_object.inventory_number,
                    directory_code=base_object.directory_code,
                    measure=measure,
                    price=round(base_object.total_price / base_object.amount, 2),
                    amount=base_object.amount,
                    category=cat_form.clean()['categories']
                )

                simple_object.save()
                form = SimpleObjectForm(instance=simple_object)
                context = {
                    'form': form,
                    'simple_object': simple_object,
                    'status': 'update',
                    'slug': simple_object.slug,
                }
                return render(request, 'db_site/simple_object_form.html', context=context)
        return redirect(base_object_page, lab, slug)


"""---------------------------------------------------------------------------------------------------------"""
"""------------------------------------------SIMPLE OBJECTS-------------------------------------------------"""


@login_required(login_url='/login/')
def simple_objects_list(request, lab, obj_type=None):
    """Список простых объектов. lab - текущая лаборатория"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        if request.method == 'GET':
            sort = request.GET.getlist('sort')
            if not sort:
                sort = ['name_lower']
            if obj_type:
                all_objects = SimpleObject.objects.filter(
                    lab__slug=lab, status__in=['IW', 'NW'], category__obj_type=obj_type
                ).order_by(*sort)
                all_name = Category.objects.filter(obj_type=obj_type)[0].get_obj_type_display()
            else:
                all_objects = SimpleObject.objects.filter(lab__slug=lab, status__in=['IW', 'NW']).order_by(*sort)
                all_name = 'Весь список'

            page, is_paginator, next_url, prev_url, last_url, paginator_dict = paginator_module(
                request=request, objects=all_objects
            )

            prefix = ''
            if sort:
                prefix = '&sort=' + sort[0]

            context = {
                'simple_objects': all_objects,
                'simple_objects_count': all_objects.count(),
                'old_prefix': prefix,
                'all_name': all_name,
                'category': 'all',              # Необходимо для определения текущей категории.
                                                # Если категория общая то нет доступа для ее редактирования
            }
            context.update(paginator_dict)

            return render(request, 'db_site/objects_list.html', context=context)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def simple_objects_write_off_list(request, lab, obj_type=None):
    """Список списаных простых объектов. lab - текущая лаборатория"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        if request.method == 'GET':
            sort = request.GET.getlist('sort')
            if not sort:
                sort = ['name_lower']
            if obj_type:
                all_objects = SimpleObject.objects.filter(
                    lab__slug=lab, status='WO', category__obj_type=obj_type
                ).order_by(*sort)
            else:
                all_objects = SimpleObject.objects.filter(lab__slug=lab, status='WO').order_by(*sort)
            page, is_paginator, next_url, prev_url, last_url, paginator_dict = paginator_module(
                request=request, objects=all_objects
            )
            context = {
                'simple_objects': all_objects,
                'category': 'all',      # Необходимо для определения текущей категории.
                                        # Если категория общая то нет доступа для ее редактирования
            }
            context.update(paginator_dict)

            return render(request, 'db_site/objects_list.html', context=context)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def simple_object_page(request, lab, slug):
    """Страница простого объекта. lab - текущая лаборатория, slug - url объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    simple_object = SimpleObject.objects.get(lab__slug=lab, slug=slug)
    if request.user.is_superuser or user.lab.slug == lab:
        if request.method == 'GET':
            users = WorkerEquipment.objects.filter(order__isnull=True, simple_object=simple_object)
            all_parts_list = []
            # simple_object.update_amount()
            # Список составляющих сложных объектов в которых присутствуют простые объекты
            big_objects_list = BigObjectList.objects.filter(simple_object__slug=slug)
            for obj in big_objects_list:
                for big_object in BigObject.objects.filter(base=obj.big_object, status='IW'):
                    for child in big_object.get_descendants(include_self=True):
                        component = child.base.simple_components.filter(simple_object__slug=slug)
                        if component:
                            part_set = dict()
                            part_set['part'] = child
                            part_set['amount'] = component[0].amount
                            all_parts_list.append(part_set)

            # Форма для списания
            write_off_form = SimpleObjectWriteOffForm(
                max_value=simple_object.amount, simple_object=simple_object
            )

            file_categories_form = FileAndImageCategoryForm()
            file_categories = FileAndImageCategory.objects.filter(simple_object=simple_object)

            # simple_object.update_amount()

            context = {
                'write_off_form': write_off_form,
                'object': simple_object,
                'users': users,
                'big_objects_list': all_parts_list,
                'file_categories_form': file_categories_form,
                'file_categories': file_categories,
            }
            return render(request, 'db_site/simple_object_page.html', context=context)
        else:
            form_type = 'files'
            for key, value in request.POST.items():
                if key == 'write_off_amount':
                    form_type = 'write_off_amount'
                    break

            if form_type == 'files':
                print('CREATE NEW FILE CATEGORY')
                form = FileAndImageCategoryForm(request.POST)
                if form.is_valid():
                    new_category = form.save(commit=False)
                    new_category.simple_object = simple_object
                    form.save()

            elif form_type == 'write_off_amount':
                write_off_form = SimpleObjectWriteOffForm(
                    request.POST, max_value=simple_object.amount, simple_object=simple_object
                )
                if write_off_form.is_valid():
                    clean_data = write_off_form.clean()
                    simple_object.amount = simple_object.amount - float(clean_data['write_off_amount'])
                    simple_object.save()

            return redirect(simple_object_page, lab=lab, slug=slug)

    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def simple_object_history(request, lab, slug):
    """Добавление нового составного объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        simple_object = SimpleObject.objects.get(lab__slug=lab, slug=slug)
        if request.method == 'GET':
            all_history = simple_object.history.all().values_list(
                'name', 'category__name', 'status', 'inventory_number', 'price_text',
                'amount', 'amount_in_work', 'history_date'
            )
            context = {
                'row_names': ['Название', 'Категория', 'Статус', 'Инв. номер', 'Стоимость',
                              'Количество', 'В работе', 'Дата'],
                'history': all_history,
                'object': simple_object,
            }
            return render(request, 'db_site/history.html', context=context)


@login_required(login_url='/login/')
def simple_object_add_form(request, lab):
    """Добавление нового простого объекта. lab - текущая лаборатория"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        if request.method == 'GET' and request.is_ajax():
            """Поиск простых объектов по введенным буквам"""
            q = request.GET.dict()['q']
            find_simple_objects = SimpleObject.objects.filter(name_lower__icontains=q).values_list('name', flat=True)
            return JsonResponse({"rez": str(list(find_simple_objects))}, status=200)
        if request.method == 'GET':
            form = SimpleObjectForm()
            context = {
                'form': form,
                'status': 'add',
            }
            return render(request, 'db_site/simple_object_form.html', context=context)
        else:
            form = SimpleObjectForm(request.POST)
            if form.is_valid():
                new_simple_object = form.save(commit=False)
                new_simple_object.lab = get_object_or_404(LabName, slug=lab)
                form.save()
                return redirect(simple_object_page, lab=lab, slug=new_simple_object.slug)
                # return render(request, 'db_site/simple_object_page.html', {'object': new_simple_object})
            else:
                context = {
                    'form': form,
                    'status': 'add',
                }
                return render(request, 'db_site/simple_object_form.html', context=context)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def simple_object_update_form(request, lab, slug):
    """Обновление существуюущего простого объекта. lab - текущая лаборатория, slug - url объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        simple_object = get_object_or_404(SimpleObject, slug=slug)
        if request.method == 'GET':
            form = SimpleObjectForm(instance=simple_object)    # Создаем новую форму
            context = {
                'form': form,
                'status': 'update',
                'slug': simple_object.slug,
            }
            return render(request, 'db_site/simple_object_form.html', context=context)
        else:
            form = SimpleObjectForm(request.POST, instance=simple_object)
            if form.is_valid():
                form.save()
                if simple_object.lab.slug != lab:
                    return redirect(simple_object_page, slug=simple_object.slug, lab=simple_object.lab.slug)
                return redirect(simple_object_page, slug=simple_object.slug, lab=lab)
            context = {
                'form': form,
                'status': 'update',
                'slug': simple_object.slug,
            }
            return render(request, 'db_site/simple_object_form.html', context=context)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def simple_object_delete_form(request, lab, slug):
    """Удаление существуюущего простого объекта. lab - текущая лаборатория, slug - url объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        simple_object = get_object_or_404(SimpleObject, slug=slug)
        if request.method == 'POST':
            form = request.POST
            if form['object_slug'] == simple_object.slug and request.user.is_superuser:
                simple_object.delete()
                return redirect(simple_objects_list, lab=lab)
        return redirect(simple_object_page, slug=slug, lab=lab)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


"""---------------------------------------------------------------------------------------------------------"""
"""--------------------------------------------BIG OBJECTS--------------------------------------------------"""


@login_required(login_url='/login/')
def base_big_object_page(request, lab, slug):
    """Страница составного объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:

        base_big_object = get_object_or_404(BaseBigObject, lab__slug=lab, slug=slug)

        if request.method == 'GET':
            file_categories = FileAndImageCategory.objects.filter(big_object=base_big_object)
            file_categories_form = FileAndImageCategoryForm()
            components = BigObjectList.objects.filter(big_object__slug=slug)
            all_parts = base_big_object.get_unique_parts(include_self=False)
            base_components = get_base_components(all_parts=all_parts)
            top_level_objects = base_big_object.get_top_level_big_objects()

            parents = base_big_object.get_base_big_object_parents()

            samples = base_big_object.components.filter(top_level=True)

            big_object_copy = CopyBigObject()

            context = {
                'base_big_object': base_big_object,
                'file_categories': file_categories,
                'file_categories_form': file_categories_form,
                'top_level_objects': top_level_objects,
                'copy_form': big_object_copy,
                'parents': parents,
                'all_parts': all_parts,
                'base_components': base_components,
                'components': components,
                'samples': samples,

            }
            return render(request, 'db_site/base_big_object_page.html', context=context)

        elif request.method == 'POST' and request.is_ajax():
            try:
                if request.POST['action'] == 'create_new_file':
                    create_new_file(name=base_big_object.name, base_big_object=base_big_object)
            except Exception as err:
                print(err)
                return JsonResponse({"rez": 'Что-то пошло не так, попробуйте снова!'}, status=400)
            else:
                return JsonResponse({"rez": True}, status=200)
        else:
            form = FileAndImageCategoryForm(request.POST)
            if form.is_valid():
                new_category = form.save(commit=False)
                new_category.big_object = base_big_object
                form.save()
                return redirect(base_big_object_page, lab=lab, slug=slug)


@login_required(login_url='/login/')
def big_object_page(request, lab, slug, pk):
    """Страница составного объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        base_big_object = get_object_or_404(BaseBigObject, lab__slug=lab, slug=slug)

        big_object = get_object_or_404(BigObject, pk=int(pk))

        if request.method == 'GET':
            if request.user.is_superuser or user.lab.slug == lab:
                components = BigObjectList.objects.filter(big_object__slug=slug)

                all_parts = big_object.get_descendants(include_self=False)

                base_components = get_base_components(all_parts=all_parts)

                file_categories = FileAndImageCategory.objects.filter(big_object=base_big_object)
                file_categories_form = FileAndImageCategoryForm()
                change_form = BigObjectForm(instance=big_object)

                big_object_copy = CopyBigObject()

                context = {
                    'base_big_object': base_big_object,
                    'big_object': big_object,
                    'components': components,
                    # 'parents': all_parents,
                    'all_parts': all_parts,
                    'base_components': base_components,
                    # 'status': status,
                    'file_categories': file_categories,
                    'file_categories_form': file_categories_form,
                    'copy_form': big_object_copy,
                    'change_form': change_form,

                }

                return render(request, 'db_site/big_object_page.html', context=context)
        elif request.method == 'POST' and request.is_ajax():
            try:
                if request.POST['action'] == 'create_new_file':
                    create_new_file(name=base_big_object.name, base_big_object=base_big_object)
            except Exception as err:
                print(err)
                return JsonResponse({"rez": 'Что-то пошло не так, попробуйте снова!'}, status=400)
            else:
                return JsonResponse({"rez": True}, status=200)
        else:
            form_type = 'copy'
            for key, value in request.POST.items():
                if key == 'text':
                    form_type = 'files'
                    break
                elif key == 'year':
                    form_type = 'change'

            if form_type == 'copy':
                form = CopyBigObject(request.POST)
                if form.is_valid():
                    data = form.clean()
                    if data['kod_end']:
                        new_big_object = big_object.copy_object_and_children(
                            new_name=data['name'], kod_end=data['kod_end']
                        )
                    else:
                        new_big_object = big_object.copy_object_and_children(new_name=data['name'])
                    return redirect(big_object_page, lab=lab, slug=slug, pk=new_big_object.pk)
                    # return redirect(big_object_page, lab=lab, slug=slug, pk=big_object.pk)

            elif form_type == 'files':
                print('CREATE NEW FILE CATEGORY')
                form = FileAndImageCategoryForm(request.POST)
                if form.is_valid():
                    new_category = form.save(commit=False)
                    new_category.big_object = base_big_object
                    form.save()
                    return redirect(big_object_page, lab=lab, slug=slug, pk=big_object.pk)
            elif form_type == 'change':
                form = BigObjectForm(request.POST, instance=big_object)
                if form.is_valid():
                    form.save()
                    return redirect(big_object_page, lab=lab, slug=slug, pk=big_object.pk)

    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def big_object_history(request, lab, slug):
    """Добавление нового составного объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        big_object = get_object_or_404(BigObject, base__lab__slug=lab, base__slug=slug)
        if request.method == 'GET':
            all_history = big_object.history.all().values_list(
                'name', 'status', 'inventory_number', 'price_text', 'history_date'
            )
            context = {
                'row_names': ['Название', 'Статус', 'Инв. номер', 'Стоимость', 'Дата'],
                'history': all_history,
                'object': big_object,
            }
            return render(request, 'db_site/history.html', context=context)


@login_required(login_url='/login/')
def big_object_add(request, lab):
    """Добавление нового составного объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        if request.method == 'GET':
            form = BaseBigObjectForm(lab=lab)
            context = {
                'form': form,
                'status': 'create_new'
            }
            return render(request, 'db_site/big_object_form.html', context=context)
        else:
            form = BaseBigObjectForm(request.POST, lab=lab)
            if form.is_valid():
                clean_data = form.clean()
                new_big_object = BaseBigObject(
                    name=clean_data['name'],
                    category=clean_data['category'],
                    inventory_number=clean_data['inventory_number'],
                    kod=clean_data['kod'],
                    text=clean_data['text'],
                    ready=clean_data['ready'],
                    lab=get_object_or_404(LabName, slug=lab)
                )
                new_big_object.save(top_level=clean_data['top_level'])

                # new_big_object = form.save(commit=False)
                # new_big_object.lab = get_object_or_404(LabName, slug=lab)
                # form.save(top_level=True, lab=get_object_or_404(LabName, slug=lab))

                # return redirect(big_object_add, lab)

                return redirect(base_big_object_page, lab=lab, slug=new_big_object.slug)
            else:
                print('NOT VALID')
                context = {
                    'form': form,
                }
                return render(request, 'db_site/big_object_form.html', context=context)
            # return redirect(big_object_add, lab=lab)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def big_object_update(request, lab, slug):
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        big_object = get_object_or_404(BaseBigObject, lab__slug=lab, slug=slug)
        if request.method == 'GET':
            form = BaseBigObjectForm(instance=big_object, lab=lab)
            context = {
                'form': form,
                'slug': slug,
                'status': 'update'
            }
            return render(request, 'db_site/big_object_form.html', context=context)
        else:
            form = BaseBigObjectForm(request.POST, instance=big_object, lab=lab)
            if form.is_valid():
                data = form.save(commit=False)
                # data.check_change_for_history_and_save()
                form.save()
                return redirect(base_big_object_page, lab=lab, slug=data.slug)
            else:
                context = {
                    'form': form,
                    'slug': slug
                }
                return render(request, 'db_site/big_object_form.html', context=context)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def big_object_update_components(request, lab, slug):
    """Добавление/Обновление компонентов составного объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        big_object = get_object_or_404(BaseBigObject, lab__slug=lab, slug=slug)
        if request.method == 'GET':
            big_object_components = BigObjectList.objects.filter(big_object=big_object)
            if len(big_object_components) == 0:
                extra = 1
            else:
                extra = 0
            formset = modelformset_factory(BigObjectList, form=SimpleObjectForBigObjectForm, extra=extra)
            context = {
                'formset': formset(form_kwargs={'lab': lab}, queryset=big_object_components),
                'big_object': big_object,
            }
            return render(request, 'db_site/big_object_components_form.html', context=context)
        elif request.method == 'POST' and request.is_ajax():
            print('AJAX')
            if request.POST.get('big_object_number_of_elements'):
                new_number_of_elements = request.POST.get('big_object_number_of_elements')
                BigObject.objects.filter(pk=big_object.pk).update(number_of_elements=new_number_of_elements)
                return JsonResponse({"rez": 'Количество компонентов : {}'.format(new_number_of_elements)}, status=200)
            else:
                return JsonResponse({"rez": 'Что-то пошло не так, попробуйте снова!'}, status=400)
        else:
            big_object_components = BigObjectList.objects.filter(big_object=big_object)
            components_formset = modelformset_factory(
                BigObjectList,
                form=SimpleObjectForBigObjectForm,
                extra=big_object.number_of_elements
            )
            formset = components_formset(request.POST, form_kwargs={'lab': lab}, queryset=big_object_components)
            if formset.is_valid():
                print('VALID')
                for form in formset:
                    clean_data = form.clean()
                    try:
                        old_component = BigObjectList.objects.get(pk=clean_data['id'].id)
                        simple_object = old_component.simple_object
                        if clean_data['amount'] == 0:
                            print('DELETE : {}'.format(old_component))

                            old_component.delete()  # Удаление старой составляющей если ее количество = 0

                            big_objects_list = BigObjectList.objects.filter(simple_object=simple_object)
                            amount = 0
                            for obj in big_objects_list:
                                amount += obj.amount
                            simple_object.update_amount(update_big_objects_price=True)
                            # simple_object.amount_in_work = amount
                            # simple_object.save()

                            big_object.number_of_elements -= 1
                        else:
                            if clean_data['amount'] != old_component.amount:
                                print('UPDATE : {}'.format(old_component))
                                old_component.amount = clean_data['amount']
                                old_component.simple_object = clean_data['simple_object']
                                old_component.save()    # Обновление компонента для объекта
                                simple_object.update_amount(update_big_objects_price=True)
                    except KeyError:
                        big_object.number_of_elements -= 1
                    except (ObjectDoesNotExist, AttributeError):
                        if clean_data['amount'] == 0:
                            big_object.number_of_elements -= 1
                        else:
                            print('CREATE NEW COMPONENT')
                            new_component, created = BigObjectList.objects.get_or_create(
                                simple_object=clean_data['simple_object'],
                                # amount=clean_data['amount'],
                                big_object=big_object
                            )

                            new_component.amount += clean_data['amount']
                            print('NEW COMPONENT SAVE')
                            new_component.save()
                            new_component.simple_object.update_amount()
                big_object.save()       # Обновление стоимости объекта и количества составляющих
                return redirect(base_big_object_page, lab=lab, slug=slug)
            else:
                context = {
                    'formset': formset,
                    'big_object': big_object,
                }
                return render(request, 'db_site/big_object_components_form.html', context=context)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def big_object_update_parts(request, lab, slug):
    """Добавление/Обновление компонентов составного объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        base_big_object = get_object_or_404(BaseBigObject, lab__slug=lab, slug=slug)
        if request.method == 'GET':
            form = PartForBigObjectForm(lab=lab)
            children = BigObject.objects.filter(parent__base=base_big_object)
            unique_parts = []
            all_unique_parts_name = []
            for part in children:
                if part.base.name not in all_unique_parts_name:
                    unique_parts.append(part)
                    all_unique_parts_name.append(part.base.name)
            context = {
                'big_object': base_big_object,
                'children': unique_parts,
                'form': form
            }
            return render(request, 'db_site/big_object_parst_form.html', context=context)
        else:
            form = PartForBigObjectForm(request.POST, lab=lab)
            all_parents = BigObject.objects.filter(base=base_big_object)
            if form.is_valid():
                print('VALID')
                clean_data = form.clean()
                part = clean_data.get('part')
                all_parts = part.get_children()
                for parent in all_parents:
                    new_part = part
                    new_part.pk = None
                    new_part.parent = parent
                    new_part.top_level = False
                    new_part.status = parent.status
                    new_part.save()

                    def search_all_parts(first_part):
                        for child in all_parts:
                            def create_new_part(p, new_parent):
                                p_children = p.get_children()

                                p_new = p
                                p_new.pk = None
                                p_new.parent = new_parent
                                p_new.top_level = False
                                p_new.status = new_parent.status
                                p_new.save()

                                for i in p_children:
                                    create_new_part(i, p_new)

                            create_new_part(child, first_part)

                    search_all_parts(new_part)

                BigObject.objects.rebuild()

                # Обновление стоимости сложных объектов с учетом новых сборочных едениц
                for big_object in BigObject.objects.filter(base=base_big_object):
                    big_object.update_price()

            else:
                print(form)
            return redirect(big_object_update_parts, lab, slug)


@login_required(login_url='/login/')
def big_object_delete_part(request, lab, slug, pk):
    """Добавление/Обновление компонентов составного объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser:
        base_big_object = get_object_or_404(BaseBigObject, lab__slug=lab, slug=slug)
        if request.method == 'POST':
            try:
                object_pk = request.POST.get('object_pk')
                if int(object_pk) == int(pk):
                    target_object = get_object_or_404(BigObject, pk=pk)
                    all_objects = BigObject.objects.filter(base=target_object.base)
                    for obj in all_objects:
                        if obj.full_name != target_object.base.name:
                            obj.delete()
            except:
                pass
        return redirect(big_object_update_parts, lab, slug)


"""---------------------------------------------------------------------------------------------------------"""
"""-----------------------------------------------SEARCH----------------------------------------------------"""


@login_required(login_url='/login/')
def search(request, lab):
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        if request.method == 'GET':
            return HttpResponseNotFound("METHOD != POST")
        else:
            form = SearchForm(request.POST)
            if form.is_valid():
                q = form.clean()['q']
                results = SimpleObject.objects.filter(
                    Q(inventory_number__icontains=q) | Q(name_lower__icontains=q) | Q(name__icontains=q) |
                    Q(directory_code__icontains=q)
                ).filter(lab__slug=lab)

                base_results = BaseObject.objects.filter(
                    Q(inventory_number__icontains=q) | Q(name_lower__icontains=q) | Q(name__icontains=q) |
                    Q(directory_code__icontains=q)
                ).filter(lab__slug=lab)
                context = {
                    'results': results,
                    'base_result': base_results,
                    'q': q
                }
                return render(request, 'db_site/search_result.html', context=context)
    else:
        return HttpResponseNotFound("У вас нет доступа к этой странице!")


"""---------------------------------------------------------------------------------------------------------"""
"""-----------------------------------------------WORKER----------------------------------------------------"""


@login_required(login_url='/login/')
def worker_page(request, pk, lab):
    user = get_object_or_404(Profile, pk=pk)
    if request.user.is_superuser or user.user == request.user:
        if request.method == 'GET':
            orders_list = Order.objects.filter(equipments__profile=user)
            orders = []
            for order in orders_list:
                if order not in orders:
                    orders.append(order)
            worker_equipments = WorkerEquipment.objects.filter(
                order__isnull=True, profile=user)
            context = {
                'worker': user,
                'orders': orders,
                'worker_equipments': worker_equipments,
            }
            return render(request, 'db_site/worker_page.html', context=context)

    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def worker_update_page(request, pk, lab):
    user = get_object_or_404(Profile, pk=pk)
    if request.user.is_superuser or user.user == request.user:
        if request.method == 'GET':
            form = ChangeProfile(instance=user)
            context = {
                'form': form,
                'worker': user
            }
            return render(request, 'db_site/worker_update_form.html', context=context)
        else:
            form = ChangeProfile(request.POST, instance=user)
            if form.is_valid():
                form.save()

            return redirect(worker_page, pk=user.pk, lab=lab)


@login_required(login_url='/login/')
def worker_equipment_form(request, pk, lab):
    user = get_object_or_404(Profile, pk=pk)
    if request.user.is_superuser or user.user == request.user:
        new_order = request.GET.get('new_order', default=False)
        order_number = request.GET.get('order_number', default=False)
        if request.method == 'GET':
            if new_order == 'true':
                worker_equipments = WorkerEquipment.objects.filter(profile=user, amount=0)
            else:
                if order_number:
                    worker_equipments = WorkerEquipment.objects.filter(profile=user, order__pk=order_number)
                else:
                    worker_equipments = WorkerEquipment.objects.filter(order__isnull=True, profile=user)

            if len(worker_equipments) == 0:
                extra = 1
            else:
                extra = 0
            formset = modelformset_factory(WorkerEquipment, form=AddSimpleObjectToProfile, extra=extra)
            context = {
                'formset': formset(form_kwargs={'lab': lab}, queryset=worker_equipments),
                'worker': user,
                'new_order': new_order,
                'order_number': order_number,
            }
            return render(request, 'db_site/worker_equipment_form.html', context=context)
        elif request.method == 'POST' and request.is_ajax():
            print('AJAX')
            if request.POST.get('big_object_number_of_elements'):
                new_number_of_elements = request.POST.get('big_object_number_of_elements')
                if order_number:
                    Order.objects.filter(pk=order_number).update(number_of_elements=new_number_of_elements)
                else:
                    Profile.objects.filter(pk=user.pk).update(number_of_elements=new_number_of_elements)

                return JsonResponse({"rez": 'Количество компонентов : {}'.format(new_number_of_elements)}, status=200)
            else:
                return JsonResponse({"rez": 'Что-то пошло не так, попробуйте снова!'}, status=400)
        else:
            if new_order == 'true':
                worker_equipments = WorkerEquipment.objects.filter(profile=user, amount=0)
            else:
                if order_number:
                    worker_equipments = WorkerEquipment.objects.filter(profile=user, order__pk=order_number)
                else:
                    worker_equipments = WorkerEquipment.objects.filter(profile=user)

            components_formset = modelformset_factory(
                WorkerEquipment,
                form=AddSimpleObjectToProfile,
                extra=user.number_of_elements
            )
            formset = components_formset(request.POST, form_kwargs={'lab': lab}, queryset=worker_equipments)
            if formset.is_valid():
                print('VALID')
                if new_order == 'true':
                    order = Order(number_of_elements=len(formset), lab=LabName.objects.get(slug=lab))
                    order.save()

                if order_number:
                    # Обновление количества позиций в конкретной заявке
                    Order.objects.filter(pk=order_number).update(number_of_elements=len(formset))
                    order = Order(pk=order_number)

                for form in formset:
                    clean_data = form.clean()
                    print(clean_data)
                    try:
                        old_component = WorkerEquipment.objects.get(pk=clean_data['id'].id)
                        if clean_data['amount'] == 0:
                            print('DELETE : {}'.format(old_component))
                            # simple_object = old_component.simple_object
                            old_component.delete()  # Удаление старой составляющей если ее количество = 0

                            if order_number:
                                Order.objects.filter(pk=order_number).update(
                                    number_of_elements=F('number_of_elements') - 1
                                )
                            else:
                                user.number_of_elements -= 1
                        else:
                            if clean_data['amount'] != old_component.amount:
                                print('UPDATE : {}'.format(old_component))
                                old_component.amount = clean_data['amount']
                                old_component.simple_object = clean_data['simple_object']
                                old_component.save()  # Обновление компонента для объекта
                    except KeyError:
                        user.number_of_elements -= 1
                    except (ObjectDoesNotExist, AttributeError):
                        if clean_data['amount'] == 0:
                            user.number_of_elements -= 1
                        else:

                            if new_order == 'true' or order_number:
                                new_component, created = WorkerEquipment.objects.get_or_create(
                                    simple_object=clean_data['simple_object'],
                                    profile=user,
                                    order=order,
                                )
                            else:
                                new_component, created = WorkerEquipment.objects.get_or_create(
                                    simple_object=clean_data['simple_object'],
                                    profile=user,
                                )

                            new_component.amount += clean_data['amount']

                            new_component.save()
                user.save()  # Обновление количества объектов у пользователя
                return redirect(worker_page, pk=pk, lab=lab)
            else:
                context = {
                    'formset': formset,
                    'worker': user,
                }
                return render(request, 'db_site/worker_equipment_form.html', context=context)


@login_required(login_url='/login/')
def worker_order_confirm(request, lab, pk):
    if request.user.is_superuser and request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        order.confirm = True
        order.save()

        return redirect(worker_page, pk=order.equipment.all()[0].profile.user_id, lab=lab)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


"""---------------------------------------------------------------------------------------------------------"""
"""-----------------------------------------------DATABASE--------------------------------------------------"""


@login_required(login_url='/login/')
def load_new_db(request, lab):
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser:
        if request.method == 'GET':
            form = DataBaseDocForm()
            context = {
                'form': form
            }
            return render(request, 'db_site/database_form.html', context=context)
        elif request.method == 'POST' and request.is_ajax():
            form = DataBaseDocForm(request.POST, request.FILES)
            if form.is_valid():
                new_file_pk = None
                try:
                    new_file = form.save(commit=False)
                    new_file.lab = LabName.objects.get(slug=lab)
                    form.save()
                    new_file_pk = new_file.pk

                    check = form.clean().get('check')

                    file = DataBaseDoc.objects.get(pk=new_file.pk)
                    file.update_all_data(create_simple_objects=check)
                    return JsonResponse({'error': False, 'message': 'Загрузка прошла успешно'})
                except Exception as err:
                    print(err)
                    if new_file_pk is not None:
                        DataBaseDoc.objects.get(pk=new_file_pk).delete()
                    return JsonResponse(
                        {'error': True, 'error_message': 'Ошибка при записи в базу данных.\n'
                                                         'Загружаемый файл должен соответствовать шаблону.\n'
                                                         'Ошибка : {}'.format(str(err))}
                    )
            else:
                return JsonResponse({'error': True, 'errors': form.errors})
        else:
            form = DataBaseDocForm(request.POST, request.FILES)
            if form.is_valid():
                print('VALID')
                # new_file = form.save(commit=False)
                # new_file.lab = LabName.objects.get(slug=lab)
                # form.save()
                #
                # file = DataBaseDoc.objects.get(pk=new_file.pk)
                # file.update_all_data()
                return redirect(load_new_db, lab=lab)

            else:
                context = {
                    'form': form
                }
                return render(request, 'db_site/database_form.html', context=context)

    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def backup(request):
    if request.user.is_superuser:
        if request.method == 'POST' and request.is_ajax():
            backup_send = data_base_backup(manual_start=True)
            if backup_send['status'] is True:
                return JsonResponse({"rez": 'Успешно'}, status=200)
            else:
                return JsonResponse({"rez": str(backup_send['err'])}, status=200)
        else:
            JsonResponse({}, status=400)


"""---------------------------------------------------------------------------------------------------------"""
"""----------------------------------------------DELETE ALL-------------------------------------------------"""


@login_required(login_url='/login/')
def delete_all_data_for_lab(request, lab):
    """Удаление всех объектов и категорий у конкретной лаборатории за исключением сложных объектов"""
    if request.user.is_superuser:
        if request.method == 'GET':
            print('DELETE ALL DATA')
            all_categories = Category.objects.filter(Q(lab__slug=lab) & ~Q(cat_type__icontains='BG'))
            for category in all_categories:
                print(category)
                category.delete()
            #
            # big_objects_slug = BigObject.objects.filter(lab__slug=lab).values_list('slug')
            # print(big_objects_slug)
            return redirect(home_page)


"""---------------------------------------------------------------------------------------------------------"""
"""-------------------------------------------------ROOM----------------------------------------------------"""


@login_required(login_url='/login/')
def room_page(request, lab, slug):
    """Страница кабинета"""
    user = Profile.objects.get(user_id=request.user.id)
    if user.lab.slug == lab or request.user.is_superuser:
        room = get_object_or_404(Room, lab__slug=lab, slug=slug)
        workers = Profile.objects.filter(room_number=room)
        all_base_cat = Category.objects.filter(cat_type='BO').values_list('name', flat=True)
        data = {}
        for cat in set(all_base_cat):
            data[cat] = SimpleObject.objects.filter(base_object__category__name__exact=cat, room=room)
        context = {
            'room': room,
            'all_workers': workers,
            'all_data': data,
        }
        return render(request, 'db_site/room_page.html', context=context)


"""---------------------------------------------------------------------------------------------------------"""
"""-----------------------------------------------ORDER LIST----------------------------------------------------"""


@login_required(login_url='/login/')
def order_list(request, lab):
    if request.user.is_superuser and request.method == 'GET':
        sort = request.GET.get('sort')

        if not sort:
            sort = '-date'
            orders = Order.objects.filter(lab__slug=lab).order_by(sort)
        else:
            if sort == '-active':
                orders = Order.objects.filter(lab__slug=lab, confirm=False).order_by('-date')
            elif sort == 'active':
                orders = Order.objects.filter(lab__slug=lab, confirm=False).order_by('date')
            elif sort == '-confirm':
                orders = Order.objects.filter(lab__slug=lab, confirm=True).order_by('-date')
            elif sort == 'confirm':
                orders = Order.objects.filter(lab__slug=lab, confirm=True).order_by('date')
            elif sort == '-all':
                orders = Order.objects.filter(lab__slug=lab).order_by('-date')
            elif sort == 'all':
                orders = Order.objects.filter(lab__slug=lab).order_by('date')
            else:
                orders = Order.objects.filter(lab__slug=lab).order_by('-date')

        prefix = ''
        if sort:
            prefix = '&sort=' + sort

        context = {
            'orders': orders,
            'old_prefix': prefix
        }
        return render(request, 'db_site/orders_list.html', context=context)


"""---------------------------------------------------------------------------------------------------------"""
