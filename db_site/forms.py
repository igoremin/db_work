from django import forms
from .models import Category, SimpleObject, BigObject, BigObjectList, Profile, FileAndImageCategory,\
    ImageForObject, FileForObject, DataBaseDoc, WorkerEquipment, BaseBigObject, BaseObject, Invoice, InvoiceBaseObject,\
    WorkCalendar
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth.models import User
from db_site.models import Profile


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'text', 'cat_type', 'obj_type']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'cat_type': forms.Select(attrs={
                'class': 'form-control', 'id': 'cat_type', 'onchange': 'CatTypeSelectChange (this)'
            }),
            'obj_type': forms.Select(attrs={'class': 'form-control', 'id': 'obj_type'}),
        }


class CategoryListForm(forms.Form):
    all_parts = None
    categories = forms.ModelChoiceField(
        required=True,
        label='Выберите категорию',
        queryset=all_parts,
        widget=forms.Select(
            attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        cat_type = False
        try:
            cat_type = kwargs.pop('type')
            self.all_parts = Category.objects.filter(lab__slug=lab, cat_type=cat_type)
        except KeyError:
            self.all_parts = Category.objects.filter(
                lab__slug=lab,
            ).exclude(cat_type='BO')
        finally:
            super(CategoryListForm, self).__init__(*args, **kwargs)
            self.fields['categories'].queryset = self.all_parts
            if cat_type:
                self.fields['categories'].label = 'Категория для базового объекта'


class InventoryNumberForm(forms.Form):
    inventory_number = forms.CharField(
        required=True,
        label='Инвентаризационный номер',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Номер',
            }
        )
    )
    bill = forms.CharField(
        required=True,
        label='Счет',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Код',
            }
        )
    )

    # def __init__(self, bill=None, *args, **kwargs):
    #     super(InventoryNumberForm, self).__init__(*args, **kwargs)
    #     if bill:
    #         self.fields['bill'].value = bill


class BaseObjectForm(forms.ModelForm):
    class Meta:
        model = BaseObject
        fields = [
            'name', 'lab', 'category', 'status', 'date_add', 'inventory_number',
            'bill', 'measure', 'total_price', 'amount'
        ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'lab': forms.Select(attrs={'class': 'form-control', 'id': 'select_current_lab'}),
            'category': forms.Select(attrs={'class': 'form-control', 'required': ''}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'date_add': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'Дата'}),
            'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bill': forms.TextInput(attrs={'class': 'form-control'}),
            'measure': forms.TextInput(attrs={'class': 'form-control'}),
            'total_price': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.TextInput(attrs={
                'class': 'form-control',
                'step': 0.001,
                'min': 0,
            }),
        }

    categories_list = None
    category = forms.ModelChoiceField(
        label='Выбор категории',
        queryset=categories_list,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'category_for_lab', 'required': ''}),
    )

    def __init__(self, *args, **kwargs):
        self.category = Category.objects.filter(cat_type='BO')
        super(BaseObjectForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = self.category


class BaseObjectsListForm(forms.ModelForm):
    """Форма для обновления базового объекта из списка"""
    class Meta:
        model = BaseObject
        fields = [
            'name', 'inventory_number', 'status', 'date_add', 'bill', 'measure', 'amount', 'total_price'
        ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'date_add': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'Дата'}),
            'bill': forms.TextInput(attrs={'class': 'form-control'}),
            'measure': forms.TextInput(attrs={'class': 'form-control'}),
            'total_price': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.TextInput(attrs={
                'class': 'form-control',
                'step': 0.001,
                'min': 0,
            }),
        }


class SimpleObjectForm(forms.ModelForm):
    class Meta:
        model = SimpleObject
        fields = ['base_object', 'name', 'lab', 'room', 'place', 'category',
                  'price', 'amount', 'measure', 'text']

        widgets = {
            'base_object': forms.Select(
                attrs={
                    'class': 'form-control selectpicker',
                    'data-live-search': 'true'
                }
            ),
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'search_box', 'autocomplete': "off"}),
            'lab': forms.Select(attrs={'class': 'form-control', 'id': 'select_current_lab'}),
            'room': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'place': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control', 'id': 'category_for_lab'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 0.001,
                'min': 0,
            }),
            'measure': forms.Select(attrs={'class': 'form-control'}),
            'text': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.category = Category.objects.filter(cat_type='SO')
        super(SimpleObjectForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = self.category


class SimpleObjectWriteOffForm(forms.Form):
    max_value = None
    simple_object = None

    def __init__(self, *args, **kwargs):
        max_value = kwargs.pop('max_value')
        min_value = 0.001
        step = 0.001
        if 'simple_object' in kwargs.keys():
            simple_object = kwargs.pop('simple_object')
            if simple_object.measure:
                if simple_object.measure.lower() == 'шт':
                    step = 1
                    min_value = 1
        super(SimpleObjectWriteOffForm, self).__init__(*args, **kwargs)

        self.fields['write_off_amount'] = forms.CharField(
                required=True,
                label='Количество для списания',
                widget=forms.NumberInput(
                    attrs={
                        'class': 'form-control',
                        'placeholder': 'Количество',
                        'type': 'number',
                        'name': 'write_off',
                        'value': 1,
                        'min': min_value,
                        'step': step,
                        'max': max_value,
                    }
                )
            )


# class BigObjectCreateForm(forms.ModelForm):
#     class Meta:
#         model = BaseBigObject
#         fields = ['name', 'category', 'inventory_number', 'text']
#
#         widgets = {
#             # 'parent': forms.Select(attrs={'class': 'form-control'}),
#             'name': forms.TextInput(attrs={'class': 'form-control'}),
#             'category': forms.Select(attrs={'class': 'form-control'}),
#             'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
#             'text': forms.Textarea(
#                 attrs={
#                     'class': 'form-control',
#                     'rows': 2,
#                 }),
#         }
#
#     def __init__(self, *args, **kwargs):
#         lab = kwargs.pop('lab')
#         self.categories = Category.objects.filter(lab__slug=lab, cat_type='BG')
#         super(BigObjectCreateForm, self).__init__(*args, **kwargs)
#         self.fields['category'].queryset = self.categories


class BaseBigObjectForm(forms.ModelForm):
    top_level = forms.CharField(
        label='Объект верхнего уровня',
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'class': 'form-check-input',
            }
        )
    )

    class Meta:
        model = BaseBigObject
        fields = ['name', 'category', 'inventory_number', 'kod', 'text', 'ready']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control', 'required': ''}),
            'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
            'kod': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                }),
            'ready': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        self.categories = Category.objects.filter(lab__slug=lab, cat_type='BG')
        super(BaseBigObjectForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = self.categories


class BigObjectForm(forms.ModelForm):
    class Meta:
        model = BigObject
        fields = ['name', 'kod_end', 'status', 'system_number', 'controller', 'detector', 'interface', 'report', 'year']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'kod_end': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'system_number': forms.TextInput(attrs={'class': 'form-control'}),
            'controller': forms.TextInput(attrs={'class': 'form-control'}),
            'detector': forms.TextInput(attrs={'class': 'form-control'}),
            'interface': forms.TextInput(attrs={'class': 'form-control'}),
            'report': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Год',
                    'type': 'number',
                    'step': 1,
                    'min': 1900,
                    'max': 2100,
                })
        }

    def __init__(self, *args, **kwargs):
        super(BigObjectForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs.keys():
            big_object = kwargs['instance']
            if big_object.status == 'NW':
                self.fields['status'].choices = self.fields['status'].choices[0:2]
            elif big_object.status == 'IW':
                self.fields['status'].choices = self.fields['status'].choices[1:3]
            if big_object.status == 'RD':
                self.fields['status'].choices = self.fields['status'].choices[2:4]


class SimpleObjectAndAmountForm(forms.ModelForm):
    class Meta:
        model = BigObjectList
        fields = ['simple_object', 'amount']

        widgets = {
            'simple_object': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
            }),
            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Количество',
                    'type': 'number',
                    'step': 0.001,
                    'min': 0,
                })
        }

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        self.simple_objects = SimpleObject.objects.filter(lab__slug=lab, base_object__status='IW')
        super(SimpleObjectAndAmountForm, self).__init__(*args, **kwargs)
        self.fields['simple_object'].queryset = self.simple_objects


class PartForBigObjectForm(forms.Form):
    all_parts = None
    part = forms.ModelChoiceField(
        required=True,
        label='Выберите сборочную единицу',
        queryset=all_parts,
        widget=forms.Select(
            attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        self.all_parts = BigObject.objects.filter(
            base__lab__slug=lab, parent=None
        ).exclude(base__category__name='Камеры').order_by('full_name')
        super(PartForBigObjectForm, self).__init__(*args, **kwargs)
        self.fields['part'].queryset = self.all_parts


class CopyBigObject(forms.Form):
    name = forms.CharField(
        required=True,
        max_length=200,
        label='Введите новое название',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Название',
            }
        )
    )
    kod_end = forms.CharField(
        required=False,
        max_length=20,
        label='Окончание кода РЮКС/РШАП для нового экземпляра',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Окончание кода',
            }
        )
    )


class SearchForm(forms.Form):
    q = forms.CharField(
        required=True,
        min_length=3,
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'type': 'search',
                'class': 'form-control mr-sm-2',
                'placeholder': 'Поиск',
                'aria-label': 'Поиск',
            }
        )
    )


class FileAndImageCategoryForm(forms.ModelForm):
    class Meta:
        model = FileAndImageCategory
        fields = ['name', 'text']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                }),
        }


class AddNewImagesForm(forms.ModelForm):
    class Meta:
        model = ImageForObject
        fields = ['image', ]

        widgets = {
            'image': forms.ClearableFileInput(attrs={'multiple': True, 'class': 'form-control-file'}),
        }
        labels = {
            "image": _("Выберите изображения"),
        }


class AddNewFilesForm(forms.ModelForm):
    class Meta:
        model = FileForObject
        fields = ['file', ]

        widgets = {
            'file': forms.ClearableFileInput(attrs={'multiple': True, 'class': 'form-control-file'}),
        }
        labels = {
            "file": _("Выберите файлы"),
        }


class DataBaseDocForm(forms.ModelForm):

    check = forms.BooleanField(label='Создать простые объекты на основе данного файла', required=False)

    class Meta:
        model = DataBaseDoc
        fields = ['name', 'file']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }


class ChangeProfile(forms.ModelForm):
    avatar_label = None

    class Meta:
        model = Profile
        fields = ['name', 'room_number', 'sex', 'position', 'lab', 'avatar']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'room_number': forms.Select(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control-file'}),
            'sex': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
            'lab': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        is_admin = kwargs.pop('is_admin', False)
        super(ChangeProfile, self).__init__(*args, **kwargs)
        if 'instance' in kwargs.keys():
            profile = kwargs['instance']
            if profile.avatar:
                self.avatar_label = f'Текущий аватар : {profile.avatar.url}'
            else:
                self.avatar_label = f'Текущий аватар не выбран'
            self.fields['avatar'].label = self.avatar_label
            self.fields['avatar'].label_suffix = ''
            self.fields['lab'].empty_label = None
        if is_admin is False:
            self.fields.pop('lab')
            self.fields.pop('position')


class AddSimpleObjectToProfile(forms.ModelForm):
    class Meta:
        model = WorkerEquipment
        fields = ['simple_object', 'amount']

        widgets = {
            'simple_object': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
            }),
            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Количество',
                    'type': 'number',
                    'step': 0.001,
                    'min': 0,
                })
        }

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        self.simple_objects = SimpleObject.objects.filter(lab__slug=lab)
        super(AddSimpleObjectToProfile, self).__init__(*args, **kwargs)
        self.fields['simple_object'].queryset = self.simple_objects


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_type', 'number', 'bill', 'date', 'total_price']

        widgets = {
            'invoice_type': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
            }),
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'bill': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'Дата'}),
            'total_price': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AllInvoiceForm(forms.Form):
    all_invoice = None
    invoice = forms.ModelChoiceField(
            label='Накладная',
            required=True,
            queryset=all_invoice,
            widget=forms.Select(
                attrs={
                    'class': 'form-control selectpicker',
                    'data-live-search': 'true',
                }
            )
    )

    def __init__(self, *args, **kwargs):
        if 'lab' in kwargs.keys():
            self.all_invoice = Invoice.objects.filter(lab__slug=kwargs.pop('lab'))
        else:
            self.all_invoice = Invoice.objects.all()
        super(AllInvoiceForm, self).__init__(*args, **kwargs)
        self.fields['invoice'].queryset = self.all_invoice


class InvoiceBaseObjectForm(forms.ModelForm):
    class Meta:
        model = InvoiceBaseObject
        fields = ['base_object', 'amount']

        widgets = {
            'base_object': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true',
            }),
            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Количество',
                    'type': 'number',
                    'step': 0.001,
                    'min': 0,
                })
        }

    def __init__(self, *args, **kwargs):
        invoice_pk = False
        try:
            invoice_pk = kwargs.pop('invoice_pk')
        except KeyError:
            pass
        if invoice_pk is not False:
            self.base_list = BaseObject.objects.exclude(invoicebaseobject__invoice__pk=invoice_pk)
        super(InvoiceBaseObjectForm, self).__init__(*args, **kwargs)
        if invoice_pk is not False:
            self.fields['base_object'].queryset = self.base_list


class WorkCalendarChange(forms.ModelForm):
    class Meta:
        model = WorkCalendar
        fields = ['work_hours', 'work_minutes', 'type']

        widgets = {
            'work_hours': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Количество рабочих часов',
                    'type': 'number',
                    'step': 1,
                    'min': 0,
                    'max': 23
                }
            ),
            'work_minutes': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Количество минут в последнем часе',
                    'type': 'number',
                    'step': 1,
                    'min': 0,
                    'max': 59
                }
            ),
            'type': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            )
        }

class RegisterUserForm(forms.ModelForm):
    password = forms.CharField(
        min_length=8, max_length=128, widget=forms.PasswordInput(
            attrs={
                'class': 'form-control login_form',
                'placeholder': '********',
                'id': 'user_password',
            }
        )
    )

    username = UsernameField(widget=forms.TextInput(
        attrs={'class': 'form-control login_form', 'placeholder': 'Введите логин', 'id': 'user_username'}))
    fio = forms.CharField(
        min_length=4, max_length=128, widget=forms.TextInput(
            attrs={
                'class': 'form-control login_form',
                'placeholder': 'Введите ФИО (полностью)',
                'id': 'user_fio',
            }
        )
    )

    class Meta:
        model = User
        fields = ('username', 'password')
        labels = {'username': 'Login', 'password': 'Password'}

    def save(self, commit=True):
        user = super(RegisterUserForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)

    username = UsernameField(widget=forms.TextInput(
        attrs={'class': 'form-control login_form', 'placeholder': 'Введите логин', 'id': 'user_username'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control login_form',
            'placeholder': '********',
            'id': 'user_password',
        }
    ))