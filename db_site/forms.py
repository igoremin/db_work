from django import forms
from .models import Category, SimpleObject, BigObject, BigObjectList, Profile, FileAndImageCategoryForBigObject,\
    ImageForBigObject, FileForBigObject, DataBaseDoc, WorkerEquipment, BaseBigObject
from django.utils.translation import ugettext_lazy as _


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'text', 'cat_type']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'cat_type': forms.Select(attrs={'class': 'form-control'}),
        }


class SimpleObjectForm(forms.ModelForm):
    class Meta:
        model = SimpleObject
        fields = ['base_object', 'name', 'inventory_number', 'directory_code', 'lab', 'place', 'category', 'price',
                  'amount', 'measure', 'status', 'text']

        widgets = {
            'base_object': forms.Select(
                attrs={
                    'class': 'form-control selectpicker',
                    'data-live-search': 'true'
                }
            ),
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'search_box', 'autocomplete': "off"}),
            'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
            'directory_code': forms.TextInput(attrs={'class': 'form-control'}),
            'lab': forms.Select(attrs={'class': 'form-control', 'id': 'select_current_lab'}),
            'place': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control', 'required': ''}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                # 'step': 0.01,
                'min': 0,
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 0.001,
                'min': 0,
            }),
            'measure': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'text': forms.TextInput(attrs={'class': 'form-control'}),
        }

    categories_list = None
    category = forms.ModelChoiceField(
        label='Выбор категории',
        queryset=categories_list,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'category_for_lab'}),
    )

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        self.category = Category.objects.filter(lab__slug=lab, cat_type='SO')
        super(SimpleObjectForm, self).__init__(*args, **kwargs)
        # self.fields['category'].queryset = self.category
        self.fields['category'].queryset = Category.objects.all()


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
            # 'parent': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control', 'required': ''}),
            'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
            'kod': forms.TextInput(attrs={'class': 'form-control'}),
            # 'status': forms.Select(attrs={'class': 'form-control'}),
            'text': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                }),
            'ready': forms.CheckboxInput(attrs={'class': 'form-check-input'})
            # 'system_number': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # 'controller': forms.TextInput(attrs={'class': 'form-control'}),
            # 'detector': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # 'interface': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # 'report': forms.TextInput(attrs={'class': 'form-control'}),
            # 'year': forms.NumberInput(attrs={'class': 'form-control'}),
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


class SimpleObjectForBigObjectForm(forms.ModelForm):
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
        self.simple_objects = SimpleObject.objects.filter(lab__slug=lab)
        super(SimpleObjectForBigObjectForm, self).__init__(*args, **kwargs)
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
    # class Meta:
    #     model = BigObject
    #     fields = ['parent', ]
    #
    #     widgets = {
    #         'parent': forms.Select(attrs={'class': 'form-control'}),
    #     }
    #
    #     labels = {
    #         'parent': 'Выберите сборочную еденицу'
    #     }


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


class FileAndImageCategoryForBigObjectForm(forms.ModelForm):
    class Meta:
        model = FileAndImageCategoryForBigObject
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
        model = ImageForBigObject
        fields = ['image', ]

        widgets = {
            'image': forms.ClearableFileInput(attrs={'multiple': True, 'class': 'form-control-file'}),
        }
        labels = {
            "image": _("Выберите изображения"),
        }


class AddNewFilesForm(forms.ModelForm):
    class Meta:
        model = FileForBigObject
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
    class Meta:
        model = Profile
        fields = ['name', 'room_number']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'room_number': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Кабинет',
                    'type': 'number',
                    'step': 1,
                    'min': 1,
                    'max': 700
                })
        }


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
