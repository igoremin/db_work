from django.shortcuts import render, redirect
from .models import SimpleObject, LabName, Category, Profile, BigObject, BigObjectList, ImageForBigObject,\
    FileAndImageCategoryForBigObject, FileForBigObject, DataBaseDoc, BaseObject, WorkerEquipment
from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotFound, JsonResponse
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import CategoryForm, SimpleObjectForm, SimpleObjectWriteOffForm, BigObjectCreateForm, \
    SimpleObjectForBigObjectForm, BigObjectUpdateForm, SearchForm, CopyBigObject, FileAndImageCategoryForBigObjectForm,\
    AddNewImagesForm, AddNewFilesForm, DataBaseDocForm, ChangeProfile, AddSimpleObjectToProfile
from .scripts import create_new_file


def custom_proc_user_categories_list(request):
    data = {
        'user_cat_list': 'none',
        'current_lab': 'none',
        'search_form': 'none',
        'user_info': 'none',
        'big_objects_cat': 'none'
    }
    try:
        lab = request.build_absolute_uri().replace('//', '').split('/')[1]

        lab_categories_base = Category.objects.filter(lab__slug=lab, cat_type='BO')
        lab_categories_simple = Category.objects.filter(lab__slug=lab, cat_type='SO')
        lab_categories_big = Category.objects.filter(lab__slug=lab, cat_type='BG')
        # base_categories = Category.objects.filter(lab__slug=lab, )
        search_form = SearchForm()
        workers = Profile.objects.filter(lab__slug=lab)
        user = Profile.objects.get(user_id=request.user.id)

        data = {'user_cat_list_base': lab_categories_base,
                'user_cat_list_simple': lab_categories_simple,
                'current_lab': LabName.objects.get(slug=lab),
                'search_form': search_form,
                'workers': workers,
                'user_info': user,
                'big_objects_cat': lab_categories_big,
                }
        if lab not in LabName.objects.values_list('slug', flat=True):
            data = {
                'user_cat_list': 'none',
                'current_lab': 'none',
                'search_form': 'none',
                'user_info': 'none',
                'big_objects_cat': 'none'
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
            base_objects = BaseObject.objects.filter(category__slug=slug, lab__slug=lab)
            simple_objects = SimpleObject.objects.filter(category__slug=slug, lab__slug=lab)
            big_objects = BigObject.objects.filter(category__slug=slug, lab__slug=lab)

            if simple_objects:
                page, is_paginator, next_url, prev_url, last_url, paginator_dict = paginator_module(
                    request=request, objects=simple_objects
                )
            else:
                page, is_paginator, next_url, prev_url, last_url, paginator_dict = paginator_module(
                    request=request, objects=base_objects
                )

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
            }

            context.update(paginator_dict)

            return render(request, 'db_site/objects_list.html', context=context)
        else:
            return HttpResponseNotFound("У вас нет доступа к этой странице!")


"""---------------------------------------------------------------------------------------------------------"""
"""------------------------------------------SIMPLE OBJECTS-------------------------------------------------"""


@login_required(login_url='/login/')
def base_object_page(request, lab, slug):
    """Список простых объектов. lab - текущая лаборатория"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        if request.method == 'GET':
            base_object = get_object_or_404(BaseObject, slug=slug)
            simple_objects = SimpleObject.objects.filter(base_object=base_object)
            context = {
                'object': base_object,
                'simple_objects': simple_objects,
            }
            return render(request, 'db_site/base_object_page.html', context=context)


"""---------------------------------------------------------------------------------------------------------"""
"""------------------------------------------SIMPLE OBJECTS-------------------------------------------------"""


@login_required(login_url='/login/')
def simple_objects_list(request, lab):
    """Список простых объектов. lab - текущая лаборатория"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        if request.method == 'GET':
            all_objects = SimpleObject.objects.filter(lab__slug=lab, status__in=['IW', 'NW'])
            big_objects = BigObject.objects.filter(lab__slug=lab)

            page, is_paginator, next_url, prev_url, last_url, paginator_dict = paginator_module(
                request=request, objects=all_objects
            )

            context = {
                'big_objects': big_objects,
                'simple_objects': all_objects,
                'simple_objects_count': all_objects.count(),
                'category': 'all',              # Необходимо для определения текущей категории.
                                                # Если категория общая то нет доступа для ее редактирования
            }
            context.update(paginator_dict)

            return render(request, 'db_site/objects_list.html', context=context)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def simple_objects_write_off_list(request, lab):
    """Список списаных простых объектов. lab - текущая лаборатория"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        if request.method == 'GET':
            all_objects = SimpleObject.objects.filter(lab__slug=lab, status='WO')
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
            # Список составляющих сложных объектов в которых присутствуют простые объекты
            big_objects_list = BigObjectList.objects.filter(simple_object__slug=slug, big_object__status='IW')
            # Форма для списания
            write_off_form = SimpleObjectWriteOffForm(
                max_value=simple_object.amount, simple_object=simple_object
            )
            context = {
                'write_off_form': write_off_form,
                'object': simple_object,
                'big_objects_list': big_objects_list,
            }
            return render(request, 'db_site/simple_object_page.html', context=context)
        else:
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
        if request.method == 'GET':
            form = SimpleObjectForm(lab=lab)
            context = {
                'form': form,
                'status': 'add',
            }
            return render(request, 'db_site/simple_object_form.html', context=context)
        else:
            form = SimpleObjectForm(request.POST, lab=lab)
            if form.is_valid():
                print('SIMPLE OBJECT CREATE FORM VALID')
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
            form = SimpleObjectForm(instance=simple_object, lab=lab)    # Создаем новую форму
            context = {
                'form': form,
                'status': 'update',
                'slug': simple_object.slug,
            }
            return render(request, 'db_site/simple_object_form.html', context=context)
        else:
            form = SimpleObjectForm(request.POST, instance=simple_object, lab=lab)
            if form.is_valid():
                form.save()
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
def big_object_page(request, lab, slug):
    """Страница составного объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        big_object = get_object_or_404(BigObject, lab__slug=lab, slug=slug)
        components = BigObjectList.objects.filter(big_object__slug=slug)

        all_components = list()
        all_children = list()

        def get_all_children(parent):
            children = parent.get_children()
            for child in children:
                all_children.append(child)
                all_components.append(BigObjectList.objects.filter(big_object__slug=child.slug))
                if child.get_children():
                    get_all_children(child)

        get_all_children(big_object)

        file_categories = FileAndImageCategoryForBigObject.objects.filter(big_object=big_object)
        if request.method == 'GET':
            if request.user.is_superuser or user.lab.slug == lab:
                big_object_copy = CopyBigObject()
                file_categories_form = FileAndImageCategoryForBigObjectForm()
                """-------------------------"""
                # for componet in components:
                #     componet.update_total_price()
                """-------------------------"""
                status = 'Not Found'
                for s in big_object.ChoicesStatus.choices:
                    if big_object.status == s[0]:
                        status = s[1]

                base_components = set()
                for component in components:
                    base_components.add(component.simple_object.base_object)

                context = {
                    'big_object': big_object,
                    'components': components,
                    'all_components': all_components,
                    'all_children': all_children,
                    'base_components': base_components,
                    'status': status,
                    'copy_form': big_object_copy,
                    'file_categories': file_categories,
                    'file_categories_form': file_categories_form,

                }

                # big_object.update_price()
                return render(request, 'db_site/big_object_page.html', context=context)
        elif request.method == 'POST' and request.is_ajax():
            print('AJAX')
            print(request.POST)
            try:
                if request.POST['action'] == 'create_new_file':
                    print('CREATE NEW FILE')
                    all_data = components.values_list('simple_object__name', 'simple_object__measure',
                                                      'simple_object__inventory_number',
                                                      'simple_object__directory_code', 'amount')
                    create_new_file(name=big_object.name, all_data=all_data, big_object=big_object)
            except Exception as err:
                print(err)
                return JsonResponse({"rez": 'Что-то пошло не так, попробуйте снова!'}, status=400)
            else:
                return JsonResponse({"rez": True}, status=200)
            # return redirect(big_object_page, lab=lab, slug=slug)
        else:
            form_type = 'copy'
            for key, value in request.POST.items():
                if key == 'text':
                    form_type = 'files'
                    break

            # return redirect(big_object_page, lab=lab, slug=slug)
            if form_type == 'copy':
                form = CopyBigObject(request.POST)
                if form.is_valid():
                    data = form.clean()
                    new_big_object = big_object
                    new_big_object.pk = None
                    new_big_object.name = data['name']
                    new_big_object.inventory_number = None
                    new_big_object.status = 'NW'
                    new_big_object.save()

                    for component in components:
                        new_component = component
                        new_component.pk = None
                        new_component.big_object = new_big_object
                        new_component.save()

                    new_big_object.update_simple_objects()
                    return redirect(big_object_page, lab=lab, slug=new_big_object.slug)
            elif form_type == 'files':
                form = FileAndImageCategoryForBigObjectForm(request.POST)
                if form.is_valid():
                    new_category = form.save(commit=False)
                    new_category.big_object = big_object
                    form.save()
                    return redirect(big_object_page, lab=lab, slug=slug)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


@login_required(login_url='/login/')
def big_object_history(request, lab, slug):
    """Добавление нового составного объекта"""
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        big_object = get_object_or_404(BigObject, lab__slug=lab, slug=slug)
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
            form = BigObjectCreateForm(lab=lab)
            context = {
                'form': form,
            }
            return render(request, 'db_site/big_object_form.html', context=context)
        else:
            form = BigObjectCreateForm(request.POST, lab=lab)
            if form.is_valid():
                new_big_object = form.save(commit=False)
                new_big_object.lab = get_object_or_404(LabName, slug=lab)
                form.save()
                return redirect(big_object_page, lab=lab, slug=new_big_object.slug)
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
        big_object = get_object_or_404(BigObject, lab__slug=lab, slug=slug)
        if request.method == 'GET':
            form = BigObjectUpdateForm(instance=big_object, lab=lab)
            context = {
                'form': form,
                'slug': slug
            }
            return render(request, 'db_site/big_object_form.html', context=context)
        else:
            form = BigObjectUpdateForm(request.POST, instance=big_object, lab=lab)
            if form.is_valid():
                data = form.save(commit=False)
                # data.check_change_for_history_and_save()
                form.save()
                return redirect(big_object_page, lab=lab, slug=data.slug)
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
        big_object = get_object_or_404(BigObject, lab__slug=lab, slug=slug)
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
                    print(clean_data)
                    try:
                        old_component = BigObjectList.objects.get(pk=clean_data['id'].id)
                        if clean_data['amount'] == 0:
                            print('DELETE : {}'.format(old_component))
                            simple_object = old_component.simple_object
                            old_component.delete()  # Удаление старой составляющей если ее количество = 0

                            big_objects_list = BigObjectList.objects.filter(simple_object=simple_object)
                            amount = 0
                            for obj in big_objects_list:
                                amount += obj.amount
                            simple_object.amount_in_work = amount
                            simple_object.save()

                            big_object.number_of_elements -= 1
                        else:
                            if clean_data['amount'] != old_component.amount:
                                print('UPDATE : {}'.format(old_component))
                                old_component.amount = clean_data['amount']
                                old_component.simple_object = clean_data['simple_object']
                                old_component.save()    # Обновление компонента для объекта
                    except KeyError:
                        big_object.number_of_elements -= 1
                    except (ObjectDoesNotExist, AttributeError):
                        if clean_data['amount'] == 0:
                            big_object.number_of_elements -= 1
                        else:

                            new_component, created = BigObjectList.objects.get_or_create(
                                simple_object=clean_data['simple_object'],
                                # amount=clean_data['amount'],
                                big_object=big_object
                            )

                            new_component.amount += clean_data['amount']

                            new_component.save()
                big_object.save()       # Обновление стоимости объекта и количества составляющих
                return redirect(big_object_page, lab=lab, slug=slug)
            else:
                context = {
                    'formset': formset,
                    'big_object': big_object,
                }
                return render(request, 'db_site/big_object_components_form.html', context=context)
    return HttpResponseNotFound("У вас нет доступа к этой странице!")


def big_object_update_files_category(request, lab, slug, pk):
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        big_object = get_object_or_404(BigObject, lab__slug=lab, slug=slug)
        category = get_object_or_404(FileAndImageCategoryForBigObject, pk=pk)
        if request.method == 'GET':
            all_images = ImageForBigObject.objects.filter(category=category)
            files = FileForBigObject.objects.filter(category=category)
            add_new_images_form = AddNewImagesForm()
            add_new_files_form = AddNewFilesForm()
            context = {
                'images': all_images,
                'files': files,
                'big_object': big_object,
                'add_new_images_form': add_new_images_form,
                'add_new_files_form': add_new_files_form,
                'category': category,
            }
            return render(request, 'db_site/big_object_update_category_files_form.html', context=context)
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
                    print('VALID')
                    for image in images:
                        new_image = ImageForBigObject(
                            big_object=big_object,
                            category=category,
                            image=image
                        )
                        new_image.save()
            elif form_type == 'file':
                form = AddNewFilesForm(request.POST, request.FILES)
                files = request.FILES.getlist('file')
                if form.is_valid():
                    for file in files:
                        new_file = FileForBigObject(
                            big_object=big_object,
                            category=category,
                            file=file
                        )
                        new_file.save()
            return redirect(big_object_update_files_category, lab, slug, pk)


def big_object_delete_image(request, lab, slug, pk):
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        image = get_object_or_404(ImageForBigObject, pk=pk)
        cat_pk = image.category.pk
        if request.method == 'POST':
            form = request.POST
            if form['image_pk'] == str(image.pk):
                image.delete()
            return redirect(big_object_update_files_category, lab=lab, slug=slug, pk=cat_pk)


def big_object_delete_file(request, lab, slug, pk):
    user = Profile.objects.get(user_id=request.user.id)
    if request.user.is_superuser or user.lab.slug == lab:
        file = get_object_or_404(FileForBigObject, pk=pk)
        cat_pk = file.category.pk
        if request.method == 'POST':
            form = request.POST
            if form['file_pk'] == str(file.pk):
                file.delete()
            return redirect(big_object_update_files_category, lab=lab, slug=slug, pk=cat_pk)


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
                print(base_results)
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
            context = {
                'worker': user,
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
        if request.method == 'GET':
            worker_equipments = WorkerEquipment.objects.filter(profile=user)
            if len(worker_equipments) == 0:
                extra = 1
            else:
                extra = 0
            formset = modelformset_factory(WorkerEquipment, form=AddSimpleObjectToProfile, extra=extra)
            context = {
                'formset': formset(form_kwargs={'lab': lab}, queryset=worker_equipments),
                'worker': user,
            }
            return render(request, 'db_site/worker_equipment_form.html', context=context)
        elif request.method == 'POST' and request.is_ajax():
            print('AJAX')
            if request.POST.get('big_object_number_of_elements'):
                new_number_of_elements = request.POST.get('big_object_number_of_elements')
                Profile.objects.filter(pk=user.pk).update(number_of_elements=new_number_of_elements)
                return JsonResponse({"rez": 'Количество компонентов : {}'.format(new_number_of_elements)}, status=200)
            else:
                return JsonResponse({"rez": 'Что-то пошло не так, попробуйте снова!'}, status=400)
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
                for form in formset:
                    clean_data = form.clean()
                    print(clean_data)


                    try:
                        old_component = WorkerEquipment.objects.get(pk=clean_data['id'].id)
                        if clean_data['amount'] == 0:
                            print('DELETE : {}'.format(old_component))
                            simple_object = old_component.simple_object
                            old_component.delete()  # Удаление старой составляющей если ее количество = 0

                            # big_objects_list = BigObjectList.objects.filter(simple_object=simple_object)
                            # amount = 0
                            # for obj in big_objects_list:
                            #     amount += obj.amount
                            # simple_object.amount_in_work = amount
                            # simple_object.save()

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

                            new_component, created = WorkerEquipment.objects.get_or_create(
                                simple_object=clean_data['simple_object'],
                                profile=user,
                                # amount=clean_data['amount'],

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

            # return redirect(worker_equipment_form, pk=pk, lab=lab)


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
