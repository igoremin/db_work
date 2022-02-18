import requests
from django.shortcuts import render, redirect, reverse
from django.template.loader import render_to_string
from .models import SimpleObject, LabName, Category, Profile, BigObject, BigObjectList, ImageForObject, \
    FileAndImageCategory, FileForObject, DataBaseDoc, BaseObject, WorkerEquipment, BaseBigObject, Room, \
    Order, Invoice, InvoiceBaseObject, WorkCalendar
from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotFound, JsonResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q, F
from .forms import CategoryForm, SimpleObjectForm, SimpleObjectWriteOffForm, BaseBigObjectForm, \
    SimpleObjectAndAmountForm, SearchForm, CopyBigObject, FileAndImageCategoryForm, \
    AddNewImagesForm, AddNewFilesForm, DataBaseDocForm, ChangeProfile, AddSimpleObjectToProfile, PartForBigObjectForm, \
    BigObjectForm, BaseObjectForm, CategoryListForm, InvoiceForm, InvoiceBaseObjectForm, InventoryNumberForm, \
    BaseObjectsListForm, AllInvoiceForm, WorkCalendarChange
from .scripts import create_new_file, data_base_backup
from .models import get_base_components, update_big_objects_price
from tracker.models import Task, CommentForTask
from datetime import date


def custom_proc_user_categories_list(request):
    try:
        user = Profile.objects.get(user_id=request.user.id)
    except ObjectDoesNotExist:
        user = None

    data = {
        'user_cat_list': 'none',
        'current_lab': 'none',
        'search_form': 'none',
        'user_info': user,
        'big_objects_cat': 'none',
        'rooms': 'none'
    }
    try:
        all_lab = LabName.objects.all().values_list('slug', flat=True)
        lab = list(set(all_lab) & set(request.build_absolute_uri().replace('//', '').split('/')))
        if len(lab) == 1:
            lab = lab[0]
            lab_categories_base = Category.objects.filter(lab__slug=lab, cat_type='BO')
            lab_categories_simple_equipment = Category.objects.filter(lab__slug=lab, cat_type='SO', obj_type='EQ')
            lab_categories_simple_materials = Category.objects.filter(lab__slug=lab, cat_type='SO', obj_type='MT')
            lab_categories_big = Category.objects.filter(lab__slug=lab, cat_type='BG')
            search_form = SearchForm()
            workers = Profile.objects.filter(lab__slug=lab)
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
                    'user_info': user,
                    'big_objects_cat': 'none',
                    'rooms': 'none'
                }
    except Exception as err:
        print(err)
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
        elif object_type == 'invoice':
            target_object = get_object_or_404(Invoice, lab__slug=lab, pk=slug)
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
    if request.user.is_authenticated:
        if request.user.is_superuser:
            labs = LabName.objects.all()
        else:
            user = Profile.objects.get(pk=request.user.id)
            return redirect(lab_main_page, lab=user.lab.slug)
        context = {
            'labs': labs
        }

    return render(request, 'db_site/home_page.html', context=context)


@login_required(login_url='/login/')
def lab_main_page(request, lab):
    lab = LabName.objects.get(slug=lab)
    context = {
        'lab': lab
    }
    return render(request, 'db_site/lab_main_page.html', context)


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
            'cat': cat,
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
                elif 'amount_free' in sort[0]:
                    base_sorted = [sort[0].replace('amount_free', 'name_lower')]
            else:
                sort = ['name_lower']
                base_sorted = ['name_lower']

            base_objects = BaseObject.objects.filter(
                category__slug=slug, lab__slug=lab
            ).exclude(status='WO').order_by(*base_sorted)
            simple_objects = SimpleObject.objects.filter(
                category__slug=slug, lab__slug=lab
            ).exclude(base_object__status='WO').order_by(*sort)
            if category.cat_type == 'BG':
                big_objects = BigObject.objects.filter(
                    base__category__slug=slug, base__lab__slug=lab, parent=None,
                ).exclude(status='WO')
                write_off_objects = BigObject.objects.filter(
                    base__category__slug=slug, base__lab__slug=lab, parent=None, status='WO'
                )
            else:
                big_objects = BigObject.objects.filter(
                    base__category__slug=slug, base__lab__slug=lab, parent=None,
                )
                write_off_objects = None
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
                'big_objects_write_off': write_off_objects,
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
    if not request.user.is_superuser and user.lab.slug != lab:
        raise Http404
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
    """Страница обновления базового объекта. lab - текущая лаборатория"""
    user = Profile.objects.get(user_id=request.user.id)
    if not request.user.is_superuser and user.lab.slug != lab:
        raise Http404

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
    """Создание простого объекта на основе базового"""
    if not request.user.is_superuser:
        raise Http404

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
                measure=measure,
                price=round(base_object.total_price / base_object.amount, 2),
                amount=base_object.amount,
                category=cat_form.clean()['categories']
            )
            simple_object.save(update_base_object=False)
            form = SimpleObjectForm(instance=simple_object)
            context = {
                'form': form,
                'simple_object': simple_object,
                'status': 'update',
                'slug': simple_object.slug,
                'update_base_object': False
            }
            return render(request, 'db_site/simple_object_form.html', context=context)
    return redirect(base_object_page, lab, slug)


@login_required(login_url='/login/')
def base_objects_list_update(request, lab, cat):
    """Страница обновления таблица базовых объектов по выбранной категории (cat). lab - текущая лаборатория"""
    if not request.user.is_superuser:
        raise Http404

    base_objects = BaseObject.objects.filter(category__slug=cat, lab__slug=lab)
    page, is_paginator, next_url, prev_url, last_url, paginator_dict = paginator_module(
        request=request, objects=base_objects
    )
    if request.method == 'GET':
        category = Category.objects.get(slug=cat)
        formset = modelformset_factory(BaseObject, form=BaseObjectsListForm, extra=0)
        context = {
            'formset': formset(queryset=page.object_list),
            'cat': category,
        }
        context.update(paginator_dict)
        return render(request, 'db_site/base_objects_list_update_page.html', context=context)
    else:
        forms_formset = modelformset_factory(
            BaseObject,
            form=BaseObjectsListForm,
            extra=len(base_objects)
        )
        formset = forms_formset(request.POST, queryset=page.object_list)
        if formset.is_valid():
            for form in formset:
                clean_data = form.clean()
                old_base_object = BaseObject.objects.get(pk=clean_data['id'].id)
                old_base_object_dict = {
                    'name': old_base_object.name,
                    'inventory_number': old_base_object.inventory_number,
                    'status': old_base_object.status,
                    'bill': old_base_object.bill,
                    'measure': old_base_object.measure,
                    'amount': old_base_object.amount,
                    'total_price': old_base_object.total_price,
                    'id': old_base_object
                }
                if clean_data != old_base_object_dict:
                    form.save()
            return redirect(category_page, lab, cat)
        else:
            context = {
                'formset': formset,
            }
        return render(request, 'db_site/base_objects_list_update_page.html', context=context)


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
                    lab__slug=lab, base_object__status__in=['IW', 'NW'], category__obj_type=obj_type
                ).order_by(*sort)
                all_name = Category.objects.filter(obj_type=obj_type)[0].get_obj_type_display()
            else:
                all_objects = SimpleObject.objects.filter(
                    lab__slug=lab, base_object__status__in=['IW', 'NW']
                ).order_by(*sort)
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
                'category': 'all',  # Необходимо для определения текущей категории.
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
                    lab__slug=lab, base_object__status='WO', category__obj_type=obj_type
                ).order_by(*sort)
            else:
                all_objects = SimpleObject.objects.filter(lab__slug=lab, base_object__status='WO').order_by(*sort)
            page, is_paginator, next_url, prev_url, last_url, paginator_dict = paginator_module(
                request=request, objects=all_objects
            )
            context = {
                'write_off_objects': all_objects,
                'category': 'all',  # Необходимо для определения текущей категории.
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
            big_objects_list = BigObjectList.objects.filter(simple_object=simple_object)
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
                    simple_object.write_off(float(clean_data['write_off_amount']))
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
                'name', 'category__name', 'price_text',
                'amount', 'amount_in_work', 'history_date'
            )
            context = {
                'row_names': ['Название', 'Категория', 'Стоимость',
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
            q = request.GET.dict()['q'].lower()
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
        update_base_object = request.GET.get('update_base_object', default=True)
        if request.method == 'GET':
            form = SimpleObjectForm(instance=simple_object)  # Создаем новую форму
            context = {
                'form': form,
                'status': 'update',
                'slug': simple_object.slug,
                'simple_object': simple_object,
            }
            return render(request, 'db_site/simple_object_form.html', context=context)
        else:
            form = SimpleObjectForm(request.POST, instance=simple_object)
            if form.is_valid():
                if update_base_object is True:
                    form.save()
                elif update_base_object == 'no':
                    update_simple_object = form.save(commit=False)
                    update_simple_object.save(update_base_object=False)

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
            all_parts = base_big_object.get_unique_parts(include_self=True)
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
                all_parts = big_object.get_descendants(include_self=True)
                base_components = get_base_components(all_parts=all_parts)
                file_categories = FileAndImageCategory.objects.filter(big_object=base_big_object)
                file_categories_form = FileAndImageCategoryForm()
                change_form = BigObjectForm(instance=big_object)

                big_object_copy = CopyBigObject()

                context = {
                    'base_big_object': base_big_object,
                    'big_object': big_object,
                    'all_parts': all_parts,
                    'base_components': base_components,
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
                'status': 'update',
                'big_object': big_object,
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
        big_object_components = BigObjectList.objects.filter(big_object=big_object)

        base_form = SimpleObjectAndAmountForm(lab=lab)
        context = {
            'big_object': big_object,
            'base_form': base_form,
            'all_components': big_object_components,
        }
        if request.method == 'GET':
            return render(request, 'db_site/big_object_components_form.html', context=context)
        elif request.method == 'POST' and request.is_ajax():
            if request.POST.get('big_object_number_of_elements'):
                new_number_of_elements = request.POST.get('big_object_number_of_elements')
                BigObject.objects.filter(pk=big_object.pk).update(number_of_elements=new_number_of_elements)
                return JsonResponse({"rez": 'Количество компонентов : {}'.format(new_number_of_elements)}, status=200)
            elif request.POST.get('form'):
                form = SimpleObjectAndAmountForm(request.POST, lab=lab)
                if form.is_valid():
                    clean_data = form.clean()
                    new_simple_object = clean_data['simple_object']
                    if new_simple_object.pk in big_object_components.values_list('simple_object', flat=True):
                        return JsonResponse({"err": f'{new_simple_object} уже добавлен в список!'}, status=200)
                    else:
                        new_component, created = BigObjectList.objects.get_or_create(
                            simple_object=clean_data['simple_object'],
                            big_object=big_object,
                            amount=clean_data['amount']
                        )

                        new_component.simple_object.update_amount()

                        big_object.update_price_for_instance()

                        html_str = render_to_string(
                            'db_site/big_object_components_form.html', context=context, request=request
                        )

                        return JsonResponse(
                            {
                                "rez": 'Объект добавлен',
                                'new_object': f'{new_component.simple_object.name}',
                                'amount': f'{new_component.amount}',
                                'pk': f'{new_component.pk}',
                                'url': f'{new_component.simple_object.get_absolute_url()}',
                                'new_html': f'{html_str}'
                            }, status=200)

                return JsonResponse({"err": 'Ошибка при чтении формы'}, status=200)

            elif request.POST.get('delete'):
                if request.user.is_superuser:
                    pk = request.POST.get('delete')
                    try:
                        component = BigObjectList.objects.get(pk=pk)
                        component.delete()
                        return JsonResponse({"rez": 'Объект удален'}, status=200)
                    except ObjectDoesNotExist:
                        return JsonResponse({"not_found": 'Объект не найден'}, status=200)
                    except Exception as err:
                        return JsonResponse({"err": '{}'.format(str(err))}, status=200)
                else:
                    return JsonResponse({"err": 'Пользователь должен быть администратором!'}, status=200)

            elif request.POST.get('update'):
                if request.user.is_superuser:
                    try:
                        pk = request.POST.get('update')
                        new_amount = float(request.POST.get('new_amount'))
                        if new_amount > 0:
                            component = BigObjectList.objects.get(pk=pk)
                            component.amount = new_amount
                            component.save(update_simple_object=True)
                            big_object.update_price_for_instance()
                            # update_big_objects_price(component.big_object)
                            return JsonResponse({"rez": 'Количество обновленно', 'new_amount': component.amount},
                                                status=200)
                        else:
                            return JsonResponse({"err": 'Введенное значение должно быть больше нуля!'}, status=200)
                    except ObjectDoesNotExist:
                        return JsonResponse({"not_found": 'Объект не найден'}, status=200)
                    except Exception as err:
                        return JsonResponse({"err": '{}'.format(str(err))}, status=200)
                else:
                    return JsonResponse({"err": 'Пользователь должен быть администратором!'}, status=200)
            else:
                return JsonResponse({"rez": 'Что-то пошло не так, попробуйте снова!'}, status=400)
        else:
            return HttpResponseNotFound("Что-то пошло не так, обратитесь к администратору!")
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def big_object_update_parts(request, lab, slug):
    """Добавление/Обновление частей составного объекта"""
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
                    big_object.update_total_price()

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
                q = form.clean()['q'].lower()
                results = SimpleObject.objects.filter(
                    Q(name_lower__icontains=q) | Q(name__icontains=q)
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
    if request.method == 'GET':
        worker_tasks, private_tasks, orders = None, None, None
        self_page = False
        if request.user.is_superuser or user.user == request.user:
            self_page = True
            worker_tasks = Task.objects.filter(executors__in=[user], status__in=['IW', 'NW'], privat=False)
            private_tasks, done_private_tasks = Task.get_task_tree(lab=lab, private=True, user=user)
            orders_list = Order.objects.filter(equipments__profile=user)
            orders = []
            for order in orders_list:
                if order not in orders:
                    orders.append(order)
        worker_equipments = WorkerEquipment.objects.filter(
            order__isnull=True, profile=user
        )

        all_base_cat = Category.objects.filter(cat_type='BO', lab__slug=lab).values_list('name', flat=True)
        data = {}
        for cat in set(all_base_cat):
            data[cat] = worker_equipments.filter(simple_object__base_object__category__name__exact=cat)

        context = {
            'self_page': self_page,
            'worker': user,
            'orders': orders,
            'worker_equipments': data,
            'worker_tasks': worker_tasks,
            'private_tasks': private_tasks,
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
            form = ChangeProfile(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()

            return redirect(worker_page, pk=user.pk, lab=lab)


@login_required(login_url='/login/')
def worker_change_date(request, pk, lab, day):
    """Изменение конкретной даты в календаре у пользователя"""
    user = get_object_or_404(Profile, pk=pk)
    if not request.user.is_superuser:
        raise Http404
    d = str(day).split('-')
    change_day = WorkCalendar.objects.get(user=user, date__day=d[0], date__month=d[1], date__year=d[2])

    if request.method == 'GET':
        form = WorkCalendarChange(instance=change_day)
        context = {
            'form': form,
            'day': change_day
        }
        return render(request, 'db_site/worker_calendar_change_form.html', context)

    if request.method == 'POST':
        form = WorkCalendarChange(request.POST, instance=change_day)
        if form.is_valid():
            form.save()
            return redirect(worker_calendar, pk=pk, lab=lab)
        else:
            context = {
                'form': form,
            }
            return render(request, 'db_site/worker_calendar_change_form.html', context)


@login_required(login_url='/login/')
def worker_calendar(request, pk, lab):
    """Календарь с графиком работы для конкретного пользователя"""
    user = get_object_or_404(Profile, pk=pk)
    if not request.user.is_superuser and user.user != request.user:
        raise Http404

    if request.method == 'GET' and request.is_ajax():
        if request.GET.get('type') == 'get_data_for_month':

            year = request.GET.get('year', default=date.today().year)
            month = request.GET.get('month', default=date.today().month)

            month_data = user.get_or_create_month_for_calendar(
                int(year), int(month), request.user.is_superuser
            )
            return JsonResponse({"rez": month_data}, status=200)
    elif request.method == 'GET':
        context = {
            'worker': user
        }
        return render(request, 'db_site/worker_calendar.html', context)
    elif request.method == 'POST' and request.is_ajax():
        if request.POST.get('type') == 'change_value':
            target_date = request.POST.get('date').split(':')
            new_value = request.POST.get('value')
            try:
                calendar_day = WorkCalendar.objects.get(
                    date=date(
                        year=int(target_date[2]), month=int(target_date[1]), day=int(target_date[0])
                    ),
                    user=user
                )
                calendar_day.type = new_value
                calendar_day.save()
            except ObjectDoesNotExist:
                return JsonResponse({"rez": 'not'}, status=200)
            else:
                return JsonResponse({"rez": 'ok'}, status=200)
        return JsonResponse({"rez": 'not'}, status=200)


@login_required(login_url='/login/')
def timesheet(request, lab):
    """Табель по количеству рабочих дней у лаборатории"""
    if not request.user.is_superuser:
        raise Http404

    if request.method != 'GET':
        raise Http404

    timesheet_type = request.GET.get('type', default='full')
    year = request.GET.get('year', default=date.today().year)
    month = request.GET.get('month', default=date.today().month)

    workers = Profile.objects.filter(lab__slug=lab)
    all_data = []

    i = 1
    for k in range(13):     # 13 -> Количество сотрудников которые помещаются на одну страницу табеля
        data = dict()
        try:
            worker = workers[k]
            data['num'] = i
            data['name'] = worker.get_short_name()
            data['position'] = worker.position
            calendar_for_month = worker.get_or_create_month(year, month)

            cal = []
            for day in calendar_for_month:
                if timesheet_type == 'first_half':
                    if day.date.day <= 15:
                        cal.append(day.get_name_for_timesheet())
                    else:
                        cal.append({'type': ''})
                else:
                    cal.append(day.get_name_for_timesheet())
            data['calendar'] = cal
            data['telescope_days'] = calendar_for_month.filter(type='Т').count()
        except IndexError:
            data['num'] = i
            data['name'] = ''
            data['position'] = ''
            data['calendar'] = ['' for _ in range(31)]
            data['telescope_days'] = 0
        finally:
            all_data.append(data)
            i += 1

    days = [i for i in range(1, 32)]

    context = {
        'days': days,
        'all_data': all_data
    }

    return render(request, 'db_site/timesheet.html', context)


@login_required(login_url='/login/')
def worker_equipment_form(request, pk, lab):
    user = get_object_or_404(Profile, pk=pk)
    if not request.user.is_superuser and user.user != request.user:
        raise Http404

    new_order = request.GET.get('new_order', default=False)
    order_number = request.GET.get('order_number', default=False)

    if new_order == 'true':
        worker_equipments = WorkerEquipment.objects.filter(profile=user, amount=0, order__isnull=True)
    else:
        if order_number:
            worker_equipments = WorkerEquipment.objects.filter(profile=user, order__pk=order_number)
        else:
            worker_equipments = WorkerEquipment.objects.filter(order__isnull=True, profile=user)

    base_form = SimpleObjectAndAmountForm(lab=lab)
    context = {
        'simple_object_select_form': base_form,
        'all_components': worker_equipments,
        'worker': user,
        'new_order': new_order,
        'order_number': order_number,
    }

    if request.method == 'GET':
        return render(request, 'db_site/worker_equipment_form.html', context=context)
    elif request.method == 'POST' and request.is_ajax():
        if request.POST.get('big_object_number_of_elements'):
            new_number_of_elements = request.POST.get('big_object_number_of_elements')
            if order_number:
                Order.objects.filter(pk=order_number).update(number_of_elements=new_number_of_elements)
            else:
                Profile.objects.filter(pk=user.pk).update(number_of_elements=new_number_of_elements)

            return JsonResponse({"rez": 'Количество компонентов : {}'.format(new_number_of_elements)}, status=200)
        elif request.POST.get('form'):
            form = SimpleObjectAndAmountForm(request.POST, lab=lab)
            if form.is_valid():
                clean_data = form.clean()
                new_simple_object = clean_data['simple_object']
                if new_simple_object.pk in worker_equipments.values_list('simple_object', flat=True):
                    return JsonResponse({"err": f'{new_simple_object} уже добавлен в список!'}, status=200)
                else:
                    order = None
                    if len(worker_equipments) == 0 and new_order == 'true':
                        order = Order(number_of_elements=1, lab=LabName.objects.get(slug=lab))
                        order.save()
                        order_number = order.pk

                    elif order_number:
                        # Обновление количества позиций в конкретной заявке
                        Order.objects.filter(pk=order_number).update(number_of_elements=len(worker_equipments))
                        order = Order(pk=order_number)

                    new_component, created = WorkerEquipment.objects.get_or_create(
                        simple_object=clean_data['simple_object'],
                        profile=user,
                        order=order,
                        amount=clean_data['amount']
                    )

                    if order_number:
                        worker_equipments = WorkerEquipment.objects.filter(profile=user, order__pk=order_number)
                    else:
                        worker_equipments = WorkerEquipment.objects.filter(order__isnull=True, profile=user)

                    context['all_components'] = worker_equipments
                    context['order_number'] = order_number
                    context['new_order'] = False

                    new_page_url = None
                    if new_order == 'true':
                        new_page_url = reverse(
                            'worker_equipment_form_url', args=(lab, pk)
                        ) + f'?order_number={order_number}'

                    html_str = render_to_string(
                        'db_site/worker_equipment_form.html', context=context, request=request
                    )

                    return JsonResponse(
                        {
                            "rez": 'Объект добавлен',
                            "new_page_url": new_page_url,
                            'new_object': f'{new_component.simple_object.name}',
                            'amount': f'{new_component.amount}',
                            'pk': f'{new_component.pk}',
                            'url': f'{new_component.simple_object.get_absolute_url()}',
                            'new_html': f'{html_str}'
                        }, status=200)

            return JsonResponse({"rez": 'Объект добавлен'}, status=200)
        elif request.POST.get('delete'):
            pk = request.POST.get('delete')
            try:
                component = WorkerEquipment.objects.get(pk=pk)
                component.delete()
                return JsonResponse({"rez": 'Объект удален'}, status=200)
            except ObjectDoesNotExist:
                return JsonResponse({"not_found": 'Объект не найден'}, status=200)
            except Exception as err:
                return JsonResponse({"err": '{}'.format(str(err))}, status=200)

        elif request.POST.get('update'):
                try:
                    pk = request.POST.get('update')
                    new_amount = float(request.POST.get('new_amount'))
                    if new_amount > 0:
                        component = WorkerEquipment.objects.get(pk=pk)
                        component.amount = new_amount
                        component.save()
                        return JsonResponse(
                            {"rez": 'Количество обновленно', 'new_amount': component.amount, 'pos': '4'},
                            status=200)
                    else:
                        return JsonResponse({"err": 'Введенное значение должно быть больше нуля!'}, status=200)
                except ObjectDoesNotExist:
                    return JsonResponse({"not_found": 'Объект не найден'}, status=200)
                except Exception as err:
                    return JsonResponse({"err": '{}'.format(str(err))}, status=200)

        else:
            return JsonResponse({"rez": 'Что-то пошло не так, попробуйте снова!'}, status=400)


@login_required(login_url='/login/')
def worker_equipment_by_invoice_form(request, pk, lab):
    user = get_object_or_404(Profile, pk=pk)
    if not request.user.is_superuser and user.user != request.user:
        raise Http404
    if request.method == 'GET':
        form = AllInvoiceForm(lab=lab)
        context = {
            'form': form,
            'worker': user,
        }
        return render(request, 'db_site/worker_equipment_for_invoice_form.html', context=context)
    else:
        form = AllInvoiceForm(request.POST, lab=lab)
        if form.is_valid():
            invoice = form.clean()['invoice']
            all_invoice_objects = InvoiceBaseObject.objects.filter(invoice=invoice)
            order = Order(number_of_elements=len(all_invoice_objects), lab=LabName.objects.get(slug=lab))
            order.save()
            for obj in all_invoice_objects:
                simple_objects = SimpleObject.objects.filter(base_object=obj.base_object)
                for simple_object in simple_objects:
                    amount = 0
                    if len(simple_objects) == 1:
                        amount = obj.amount
                    WorkerEquipment(
                        simple_object=simple_object,
                        profile=user,
                        order=order,
                        amount=amount
                    ).save()

            user.save()
            return redirect(reverse('worker_equipment_form_url', args=(lab, pk))+f'?order_number={order.pk}')
        context = {
            'form': form,
            'worker': user,
        }
        return render(request, 'db_site/worker_equipment_for_invoice_form.html', context=context)


@login_required(login_url='/login/')
def worker_order_confirm(request, lab, pk):
    if request.user.is_superuser and request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        order.confirm = True
        order.save()

        return redirect(worker_page, pk=order.equipment.all()[0].profile.user_id, lab=lab)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


"""---------------------------------------------------------------------------------------------------------"""
"""-----------------------------------------------INVOICE--------------------------------------------------"""


@login_required(login_url='/login/')
def invoice_list(request, lab):
    """Список накладных"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        all_invoice = Invoice.objects.filter(lab__slug=lab)
        context = {
            'all_invoice': all_invoice,
        }
        return render(request, 'db_site/invoice_list.html', context=context)


@login_required(login_url='/login/')
def invoice_page(request, lab, pk):
    """Страница накладной"""
    user = Profile.objects.get(user_id=request.user.id)
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.user.is_superuser or user.lab.slug == lab:
        if request.method == 'GET':
            file_categories_form = FileAndImageCategoryForm()
            file_categories = FileAndImageCategory.objects.filter(invoice=invoice)

            context = {
                'invoice': invoice,
                'file_categories_form': file_categories_form,
                'file_categories': file_categories,
            }
            return render(request, 'db_site/invoice_page.html', context=context)
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
                    new_category.invoice = invoice
                    form.save()

                return redirect(invoice_page, lab, pk)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def invoice_page_form(request, lab, pk=None):
    """Редактирование и создание накладной"""
    if not request.user.is_superuser:
        return HttpResponseNotFound("У вас нет доступа к этой странице!")

    if request.method == 'GET':
        if pk is None:
            form = InvoiceForm()
            invoice = False
        else:
            invoice = get_object_or_404(Invoice, pk=pk)
            form = InvoiceForm(instance=invoice)

        context = {
            'invoice': invoice,
            'form': form,
        }
        return render(request, 'db_site/invoice_form.html', context=context)
    else:
        if pk is None:
            form = InvoiceForm(request.POST)
            invoice = False
        else:
            invoice = get_object_or_404(Invoice, pk=pk)
            form = InvoiceForm(request.POST, instance=invoice)

        if form.is_valid():
            if pk is None:
                new_invoice = form.save(commit=False)
                new_invoice.lab = LabName.objects.get(slug=lab)
                new_invoice.save()
                return redirect(invoice_page, lab=lab, pk=new_invoice.pk)
            else:
                form.save()
                return redirect(invoice_page, lab=lab, pk=pk)
        else:
            context = {
                'invoice': invoice,
                'form': form,
            }
            return render(request, 'db_site/invoice_form.html', context=context)


@login_required(login_url='/login/')
def invoice_object_form(request, lab, pk):
    """Создание нового простого объекта и базавого на его основе.
    Базовый так же привязывается к конкретной накладной"""
    if not request.user.is_superuser:
        return HttpResponseNotFound("У вас нет доступа к этой странице!")

    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'GET' and request.is_ajax():
        """Поиск простых объектов по введенным буквам"""
        q = request.GET.dict()['q'].lower()
        find_simple_objects = SimpleObject.objects.filter(name_lower__icontains=q).values_list('name', flat=True)
        return JsonResponse({"rez": str(list(find_simple_objects))}, status=200)
    elif request.method == 'GET':
        form = SimpleObjectForm()
        base_form = CategoryListForm(lab=lab, type='BO')
        inventory_form = InventoryNumberForm(initial={'bill': invoice.bill})
        context = {
            'form': form,
            'invoice': invoice,
            'base_form': base_form,
            'inventory_form': inventory_form,
        }
        return render(request, 'db_site/invoice_object_form.html', context=context)
    else:
        base_form = CategoryListForm(request.POST, lab=lab, type='BO')
        base_cat = False
        if base_form.is_valid():
            # Определяем категорию базового объекта
            base_cat = base_form.clean()['categories']

        inventory_form = InventoryNumberForm(request.POST, initial={'bill': invoice.bill})
        inventory_number = None
        bill = None
        if inventory_form.is_valid():
            inventory_number = inventory_form.clean()['inventory_number']
            bill = inventory_form.clean()['bill']

        form = SimpleObjectForm(request.POST)
        if form.is_valid():
            # Сохраняем базовый объект на основе созданного простого, создаем связь между базовым и накладной
            simple_object = form.save(commit=False)
            base_object = BaseObject()
            base_object.name = simple_object.name
            base_object.lab = simple_object.lab
            base_object.amount = simple_object.amount
            base_object.total_price = simple_object.amount * simple_object.price
            base_object.date_add = invoice.date
            if inventory_number:
                base_object.inventory_number = inventory_number
            if bill:
                base_object.bill = bill
            base_object.measure = simple_object.measure
            if base_cat:
                base_object.category = base_cat
            base_object.save()

            simple_object.base_object = base_object
            form.save()

            InvoiceBaseObject(base_object=base_object, invoice=invoice, amount=simple_object.amount).save()

            return redirect(invoice_page, lab, pk)
        else:
            context = {
                'form': form,
                'invoice': invoice,
                'base_form': base_form,
                'inventory_form': inventory_form,
            }
            return render(request, 'db_site/invoice_object_form.html', context=context)


@login_required(login_url='/login/')
def invoice_base_object_form(request, lab, pk):
    """Создание нового базового объекта для конкретной накладной"""
    if not request.user.is_superuser:
        return HttpResponseNotFound("У вас нет доступа к этой странице!")

    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'GET':
        form = BaseObjectForm(initial={'bill': invoice.bill, 'date_add': invoice.date})
        context = {
            'invoice': invoice,
            'form': form,
            'type': 'base_object_form',
        }
        return render(request, 'db_site/invoice_object_form.html', context=context)
    else:
        form = BaseObjectForm(request.POST, initial={'bill': invoice.bill})
        context = {
            'invoice': invoice,
            'form': form,
            'type': 'base_object_form',
        }
        if form.is_valid():
            base_object = form.save()
            InvoiceBaseObject(base_object=base_object, invoice=invoice, amount=base_object.amount).save()
            return redirect(invoice_page, lab, pk)
        return render(request, 'db_site/invoice_object_form.html', context=context)


@login_required(login_url='/login/')
def invoice_base_object_instance_form(request, lab, pk, instance_pk=None):
    """Добавление и обновление составляющей для накладной.
    Если указана переменная instance_pk, то составляющая накладной будет обновляться,
    иначе происходит добавлдение уже существующего базового объекта к данной накладной"""
    if not request.user.is_superuser:
        return HttpResponseNotFound("У вас нет доступа к этой странице!")

    invoice = get_object_or_404(Invoice, pk=pk)
    form_type = 'add_exist_base_object'
    if request.method == 'GET':
        form = InvoiceBaseObjectForm(invoice_pk=invoice.pk)
        if instance_pk:
            instance = get_object_or_404(InvoiceBaseObject, pk=instance_pk)
            form = InvoiceBaseObjectForm(instance=instance)
            form_type = 'update_exist_instance'
        context = {
            'invoice': invoice,
            'form': form,
            'type': form_type,
            'instance_pk': instance_pk
        }
        return render(request, 'db_site/invoice_object_form.html', context=context)
    else:
        form = InvoiceBaseObjectForm(request.POST, invoice_pk=invoice.pk)
        if instance_pk:
            instance = get_object_or_404(InvoiceBaseObject, pk=instance_pk)
            form = InvoiceBaseObjectForm(request.POST, instance=instance)
            form_type = 'update_exist_instance'

        context = {
            'invoice': invoice,
            'form': form,
            'type': form_type,
            'instance_pk': instance_pk
        }
        if form.is_valid():
            if instance_pk:
                form.save()
            else:
                new_object_for_invoice = form.save(commit=False)
                new_object_for_invoice.invoice = invoice
                if not new_object_for_invoice.base_object.bill:
                    BaseObject.objects.filter(pk=new_object_for_invoice.base_object.pk).update(bill=invoice.bill)
                form.save()
            return redirect(invoice_page, lab, pk)
        return render(request, 'db_site/invoice_object_form.html', context=context)


"""---------------------------------------------------------------------------------------------------------"""
"""-----------------------------------------------DATABASE--------------------------------------------------"""


@login_required(login_url='/login/')
def load_new_db(request, lab):
    """Загрузка нового файла с данными для конкретной лаборатории"""
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
                new_file = form.save(commit=False)
                new_file.lab = LabName.objects.get(slug=lab)
                form.save()

                file = DataBaseDoc.objects.get(pk=new_file.pk)
                file.update_all_data()
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
"""-----------------------------------------------ORDERS----------------------------------------------------"""


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


@login_required(login_url='/login/')
def order_print_page(request, lab, pk):
    if request.user.is_superuser:
        if request.method == "GET":
            import datetime
            order = get_object_or_404(Order, pk=pk)
            profile = order.equipment.first().profile
            context = {
                'order': order,
                'profile': profile,
                'time': datetime.datetime.now()
            }
            return render(request, 'db_site/order_print_page.html', context=context)


"""---------------------------------------------------------------------------------------------------------"""
