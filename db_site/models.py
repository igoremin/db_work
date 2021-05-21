from django.db import models
from django.utils import timezone
from django.shortcuts import reverse
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from slugify import slugify
from django.utils.translation import gettext_lazy as _
from django.db import IntegrityError
from simple_history.models import HistoricalRecords
from mptt.models import MPTTModel, TreeForeignKey
from PIL import Image
import os


def get_all_children(big_object, all_children=None):
    if all_children is None:
        all_children = list()
    children = big_object.get_children()
    for child in children:
        print(child.name)
        all_children.append(child)
        if child.get_children():
            get_all_children(child)


def gen_slug(title, all_slugs, lab=None):
    new_slug = slugify(title, to_lower=True, separator='_')
    if lab is not None:
        new_slug = '{}_{}'.format(lab, new_slug)

    base_slug = new_slug
    end = 1
    while True:
        if new_slug in all_slugs:
            new_slug = '{}_{}'.format(base_slug, end)
            end += 1
        else:
            break

    return new_slug


def gen_slug_for_categories(title):
    new_slug = slugify(title, to_lower=True, separator='_')
    return new_slug


def gen_text_price(int_price):
    object_price = '{:,}'.format(int_price).replace(',', ' ').replace('.', ',')
    if len(object_price.split(',')[1]) == 1:
        object_price += '0'
    new_price = '{},{}'.format(object_price.split(',')[0], object_price.split(',')[1][0:2])
    return new_price


def some_model_thumb_name(instance, filename):
    original_image_path = str(instance.image).rsplit('/', 1)[0]
    return os.path.join(original_image_path, filename)


def some_model_save_photo(self, width, height):
    print(self.image.path)
    extension = str(self.image.path).rsplit('.', 1)[1]  # получаем расширение загруженного файла
    filename = str(self.image.path).rsplit(os.sep, 1)[1].rsplit('.', 1)[0]  # получаем имя загруженного файла (без пути к нему и расширения)
    full_path = str(self.image.path).rsplit(os.sep, 1)[0]  # получаем путь к файлу (без имени и расширения)

    img = Image.open(self.image.path)
    big_img = Image.open(str(self.image.path))
    thumb_name = filename + str("_big") + '.' + extension
    big_img.save(full_path + os.sep + thumb_name, quality=95)
    self.image_big = some_model_thumb_name(self, thumb_name)
    img.save(self.image.path, quality=60)


def generate_path(instance, filename):
    return '{0}/{1}/images/{2}'.format(instance.big_object.slug, instance.category.slug, filename)


def generate_path_for_files(instance, filename):
    return '{0}/{1}/files/{2}'.format(instance.big_object.slug, instance.category.slug, filename)


def generate_path_for_database(instance, filename):
    return 'database/{0}/{1}'.format(instance.lab.name, filename)


class LabName(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name='Название лаборатории')
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name='URL')

    class Meta:
        verbose_name = 'Лаборатория'
        verbose_name_plural = 'Лаборатории'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        print('---SAVE POST---')
        if not self.id:
            old_self = LabName.objects.get(pk=self.pk)
            if old_self.name != self.name:
                self.create_slug()
        else:
            self.create_slug()

            # self.slug = gen_slug(lab=False, title=self.name)
            # AllSlugs(slug=self.slug, lab='LB').save()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('categories_list_url', kwargs={'lab': self.slug})

    def create_slug(self):
        all_slugs = LabName.objects.all().values_list('slug', flat=True)
        self.slug = gen_slug(title=self.name, all_slugs=all_slugs)


class Category(models.Model):
    class ChoicesObjectType(models.TextChoices):
        BASE_OBJECT = 'BO', _('Базовый объект')
        SIMPLE_OBJECT = 'SO', _('Простой объект')
        BIG_OBJECT = 'BG', _('Составной объект')

    name = models.CharField(max_length=200, verbose_name='Название категории')
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name='URL')
    lab = models.ForeignKey(LabName, on_delete=models.CASCADE, verbose_name='Лаборатория')
    text = models.TextField(blank=True, verbose_name='Описание')
    cat_type = models.CharField(
        max_length=2,
        choices=ChoicesObjectType.choices,
        default=ChoicesObjectType.SIMPLE_OBJECT,
        verbose_name='Тип категории'
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return f'{self.lab.name} : {self.name}'

    def save(self, *args, **kwargs):
        print('---SAVE CATEGORY---')
        if self.pk is not None:
            old_self = Category.objects.get(pk=self.pk)
            if old_self.name != self.name:
                self.create_slug()
        else:
            self.create_slug()
        # self.slug = gen_slug(lab=self.lab.slug, title=self.name)
        # AllSlugs(slug=self.slug, lab=self.lab, cat_type='CT').save()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category_page_url', kwargs={'slug': self.slug, 'lab': self.lab.slug})

    def create_slug(self):
        all_slugs = Category.objects.all().values_list('slug')
        self.slug = gen_slug(lab=self.lab.slug, title=self.name, all_slugs=all_slugs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name='Имя')
    lab = models.ForeignKey(LabName, on_delete=models.CASCADE, verbose_name='Лаборатория', blank=True, null=True)
    room_number = models.IntegerField(verbose_name='Номер кабинета', blank=True, null=True)
    number_of_elements = models.IntegerField(verbose_name='Количество позиций простых элементов', default=1, blank=True)

    def __str__(self):
        if self.lab is None:
            return self.name
        else:
            return f'{self.name} : {self.lab.name}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.name = self.user.username
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('worker_page_url', kwargs={'pk': self.pk, 'lab': self.lab.slug})


class BaseObject(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    name_lower = models.CharField(max_length=200, verbose_name='Название в нижнем регистре', blank=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name='URL')
    lab = models.ForeignKey(LabName, on_delete=models.CASCADE, verbose_name='Лаборатория')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', blank=True, null=True)
    inventory_number = models.CharField(verbose_name='Инвентаризационный номер, не уникальный', max_length=100,
                                        blank=True, null=True)
    directory_code = models.CharField(verbose_name='Код справочника, не уникальный', max_length=100,
                                      blank=True, null=True)
    measure = models.CharField(verbose_name='Единица измерения', max_length=10, blank=True, null=True)
    total_price = models.FloatField(verbose_name='Сумма', default=0, blank=True)
    total_price_text = models.CharField(verbose_name='Общая сумма с пробелами', max_length=100, blank=True)
    amount = models.FloatField(verbose_name='Общее количество единиц', default=0)

    class Meta:
        verbose_name = 'Базовый объект'
        verbose_name_plural = 'Базовые объекты'
        ordering = ['name_lower']

    def __str__(self):
        return '{} ({})'.format(self.name, self.inventory_number)

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        if self.inventory_number:
            self.inventory_number = self.inventory_number.strip()
        if self.directory_code:
            self.directory_code = self.directory_code.strip()

        if self.pk is not None:
            old_self = BaseObject.objects.get(pk=self.pk)
            if old_self.name != self.name:
                self.name_lower = self.name.lower()
                self.create_slug()
        else:
            self.name_lower = self.name.lower()
            self.create_slug()

        self.update_price()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('base_object_page_url', kwargs={'slug': self.slug, 'lab': self.lab.slug})

    def create_slug(self):
        all_slugs = BaseObject.objects.all().values_list('slug', flat=True)
        self.slug = gen_slug(lab=self.lab.slug, title=self.name, all_slugs=all_slugs)

    def update_price(self):
        """Обновление текстовой цены и общей стоимости"""
        if self.total_price != 0:
            self.total_price_text = gen_text_price(round(self.total_price, 2))
        else:
            self.total_price_text = '0,00'


class SimpleObject(models.Model):
    class ChoicesStatus(models.TextChoices):
        NOT_IN_WORK = 'NW', _('Не в работе')
        IN_WORK = 'IW', _('Активный')
        WRITTEN_OF = 'WO', _('Списано')

    # parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)
    base_object = models.ForeignKey(to=BaseObject, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=200, verbose_name='Название')
    name_lower = models.CharField(max_length=200, verbose_name='Название в нижнем регистре', blank=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name='URL')
    lab = models.ForeignKey(LabName, on_delete=models.CASCADE, verbose_name='Лаборатория')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', blank=True, null=True)
    inventory_number = models.CharField(verbose_name='Инвентаризационный номер, не уникальный', max_length=100,
                                        blank=True, null=True)
    directory_code = models.CharField(verbose_name='Код справочника, не уникальный', max_length=100,
                                      blank=True, null=True)
    place = models.CharField(max_length=200, verbose_name='Место расположения', blank=True)
    price = models.FloatField(verbose_name='Стоимость', default=0)
    total_price = models.FloatField(verbose_name='Сумма', default=0, blank=True)
    price_text = models.CharField(verbose_name='Сумма за единицу с пробелами', max_length=100, blank=True)
    total_price_text = models.CharField(verbose_name='Общая сумма с пробелами', max_length=100, blank=True)
    amount = models.FloatField(verbose_name='Общее количество единиц', default=0)
    amount_in_work = models.FloatField(verbose_name='Количество единиц в работе', blank=True, default=0)
    amount_free = models.FloatField(verbose_name='Количество свободных единиц', null=True, blank=True)
    text = models.TextField(blank=True, verbose_name='Описание')
    date_add = models.DateTimeField(default=timezone.now)
    measure = models.CharField(verbose_name='Единица измерения', max_length=10, blank=True, null=True)
    status = models.CharField(
        max_length=2,
        choices=ChoicesStatus.choices,
        default=ChoicesStatus.IN_WORK,
        verbose_name='Статус'
    )
    history = HistoricalRecords(
        verbose_name='История',
        excluded_fields=['name_lower', 'slug', 'lab', 'place', 'worker', 'price', 'total_price', 'total_price_text',
                         'amount_free', 'text', 'date_add']
    )   # История изменений

    class Meta:
        verbose_name = 'Простой объект'
        verbose_name_plural = 'Простые объекты'
        # ordering = ['date_add']
        ordering = ['name_lower']

    def __str__(self):
        return '{} ({})'.format(self.name, self.inventory_number)

    def save(self, *args, **kwargs):
        update_big_objects_price = False    # Статус для обновления всех связанных объектов
        if self.pk is not None:
            old_self = SimpleObject.objects.get(pk=self.pk)
            print('---SAVE SIMPLE OBJECT---', self)
            if old_self.name != self.name:
                self.name = self.name.strip()
                self.create_slug()
                self.name_lower = self.name.lower()
            if old_self.price != self.price or old_self.amount != self.amount:
                """Если цена изменилась то считаем новую сумму и обновляем все связанные цены"""
                self.total_price = self.price * self.amount
                update_big_objects_price = True
                # self.update_price()
            if old_self.inventory_number != self.inventory_number:
                self.inventory_number = self.inventory_number.upper()

            if old_self.directory_code != self.directory_code:
                self.directory_code = self.directory_code.upper()

            self.update_amount()
            self.update_price()

            """Проверка изменений полей для записи истории изменений.
            Если какое-либо из полей изменилось то сохраняем объект с записями в истории,
            иначе пропускаем запись истории"""
            obj = [self.name, self.category, self.status, self.inventory_number, self.directory_code, self.price_text,
                   self.amount, self.amount_in_work]
            old_obj = [old_self.name, old_self.category, old_self.status, old_self.inventory_number,
                       old_self.directory_code, old_self.price_text, old_self.amount, old_self.amount_in_work]

            if obj == old_obj:
                self.skip_history_when_saving = True

        else:
            print('---SAVE NEW SIMPLE OBJECT---', self)
            self.create_slug()
            self.total_price = self.price * self.amount
            if self.inventory_number:
                self.inventory_number = self.inventory_number.upper().strip()
            if self.directory_code:
                self.directory_code = self.directory_code.upper().strip()
            self.name = self.name.strip()
            self.name_lower = self.name.lower()

            self.update_amount()
            self.update_price()

        if self.category is None:
            category, created = Category.objects.get_or_create(
                name='Разное',
                lab=self.lab,
                cat_type='SO'
            )

            self.category = category

        super().save(*args, **kwargs)

        try:
            del self.skip_history_when_saving
        except:
            pass

        if update_big_objects_price:
            """Обновляем цену у всех комплектующих и больших объектов где присутствует данный простой объект"""
            for component in BigObjectList.objects.filter(simple_object=self):
                """Обновление всех компонентов"""
                component.save()
            for big_object in BigObject.objects.filter(bigobjectlist__simple_object=self):
                """Обновление всех больших объектов"""
                big_object.save()

        """Проверка на количество простых объектов входящих в состав базового.
        Если базовый объект состоит из одного простого, то их количество должно совпадать
        Если базовый объект состоит из нескольких простых, то его количество будет равно нулю только в случае если
        количество всех простых компонетов так же равно нулю"""
        if self.base_object:
            base_object_components = SimpleObject.objects.filter(base_object=self.base_object)
            if len(base_object_components) == 1:
                print('Найден один компонент')
                self.base_object.amount = self.amount
                self.base_object.save()
            elif len(base_object_components) > 1:
                print('Количество компонентов больше одного')
                empty_components = 0
                for component in base_object_components:
                    print(component, component.amount)
                    if component.amount == 0:
                        empty_components += 1
                if empty_components != 0:
                    print('Все составляющие пустые')
                    self.base_object.amount = 0
                    self.base_object.save()

    def get_absolute_url(self):
        return reverse('simple_object_url', kwargs={'slug': self.slug, 'lab': self.lab.slug})

    def create_slug(self):
        all_slugs = SimpleObject.objects.all().values_list('slug', flat=True)
        self.slug = gen_slug(lab=self.lab.slug, title=self.name, all_slugs=all_slugs)

    def update_price(self):
        """Обновление текстовой цены и общей стоимости"""
        if self.price != 0:
            self.price_text = gen_text_price(round(self.price, 2))
            self.total_price_text = gen_text_price(round(self.total_price, 2))
        else:
            self.price_text = '0,00'
            self.total_price_text = '0,00'

    def update_amount(self):
        """Обновлние количества"""
        amount = 0
        self.amount = round(self.amount, 3)
        big_objects_list = BigObjectList.objects.filter(simple_object=self, big_object__status='IW')
        for obj in big_objects_list:
            amount += obj.amount
        self.amount_in_work = amount
        self.amount_free = self.amount - self.amount_in_work

    def delete(self, *args, **kwargs):
        all_big_objects = BigObject.objects.filter(bigobjectlist__simple_object=self)
        for big_object in all_big_objects:
            simple_objects_list = BigObjectList.objects.filter(big_object=big_object).exclude(simple_object=self)
            big_object.update_price(simple_objects_list=simple_objects_list)
            BigObject.objects.filter(pk=big_object.pk).update(price=big_object.price, price_text=big_object.price_text)
        super().delete(*args, **kwargs)


class BigObject(MPTTModel):
    class ChoicesStatus(models.TextChoices):
        NOT_IN_WORK = 'NW', _('Не в работе')
        IN_WORK = 'IW', _('В работе')
        READY = 'RD', _('Готово')
        WRITTEN_OF = 'WO', _('Списано')

    parent = TreeForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE,
                            verbose_name='Родитель')
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name='URL')
    text = models.TextField(verbose_name='Описание', blank=True)
    lab = models.ForeignKey(LabName, on_delete=models.CASCADE, verbose_name='Лаборатория', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', blank=True, null=True)
    inventory_number = models.CharField(verbose_name='Инвентаризационный номер', unique=True, blank=True, null=True,
                                        max_length=100)
    status = models.CharField(
        max_length=2,
        choices=ChoicesStatus.choices,
        default=ChoicesStatus.NOT_IN_WORK,
        verbose_name='Статус'
    )
    price = models.FloatField(verbose_name='Стоимость', default=0)
    price_text = models.CharField(verbose_name='Сумма с пробелами', max_length=100, blank=True)
    number_of_elements = models.IntegerField(verbose_name='Количество позиций простых элементов', default=1, blank=True)
    system_number = models.CharField(max_length=400, verbose_name='Номер системы', blank=True, null=True)
    controller = models.CharField(max_length=100, verbose_name='Контроллер', blank=True, null=True)
    detector = models.CharField(max_length=400, verbose_name='Детектор', blank=True, null=True)
    interface = models.CharField(max_length=400, verbose_name='Интерфейс', blank=True, null=True)
    report = models.CharField(max_length=100, verbose_name='Отчет', blank=True, null=True)
    year = models.IntegerField(verbose_name='Год', blank=True, null=True)
    history = HistoricalRecords(
        verbose_name='История',
        excluded_fields=['slug', 'text', 'lab', 'price', 'number_of_elements',
                         'system_number', 'controller', 'detector', 'interface', 'report', 'year',
                         'level', 'lft', 'rght', 'tree_id']
    )  # История изменений

    class Meta:
        verbose_name = 'Сложный объект'
        verbose_name_plural = 'Сложные объекты'
        ordering = ['name']

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' -> '.join(full_path[::-1])
        # if self.lab is None:
        #     return self.name
        # else:
        #     return f'{self.name} : {self.lab.name}'

    def get_all_children(self):
        get_all_children(self)

    def save(self, *args, **kwargs):
        print('---BIG OBJECT SAVE---')
        if self.pk is not None:
            old_self = BigObject.objects.get(pk=self.pk)

            if old_self.name != self.name:
                self.create_slug()
                # self.slug = gen_slug(lab=self.lab.slug, title=self.name)
                # AllSlugs(slug=self.slug, lab=self.lab, cat_type='BG').save()
                # for old_slug in AllSlugs.objects.filter(slug=old_self.slug):
                #     old_slug.delete()

            if old_self.inventory_number != self.inventory_number:
                self.inventory_number = self.inventory_number.upper()

            if self.status == 'IW':
                """Если объект в работе, тогда обновляем цену"""
                self.update_price()
            elif self.status in ['NW']:
                """Если статус не рабочий тогда зануляем стоимость"""
                self.price = 0
                self.price_text = '0,00'

            """Проверка изменений полей для записи истории изменений.
            Если какое-либо из полей изменилось то сохраняем объект с записями в истории,
            иначе пропускаем запись истории"""
            obj = [self.name, self.status, self.inventory_number, self.price_text]
            old_obj = [old_self.name, old_self.status, old_self.inventory_number, old_self.price_text]
            if obj == old_obj:
                self.skip_history_when_saving = True

            super().save(*args, **kwargs)
            try:
                del self.skip_history_when_saving
            except:
                pass
            self.update_simple_objects(old_self=old_self)  # Обновление простых объектов входящих в состав сложного

        else:
            self.create_slug()
            # self.slug = gen_slug(lab=self.lab.slug, title=self.name)
            # AllSlugs(slug=self.slug, lab=self.lab, cat_type='BG').save()
            if self.inventory_number:
                self.inventory_number = self.inventory_number.upper()

            if self.status in ['WO', 'NW']:
                """Если статус не рабочий тогда зануляем стоимость"""
                self.price = 0
                self.price_text = '0,00'
            super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('big_object_page_url', kwargs={'slug': self.slug, 'lab': self.lab.slug})

    def create_slug(self):
        all_slugs = BigObject.objects.all().values_list('slug', flat=True)
        self.slug = gen_slug(lab=self.lab.slug, title=self.name, all_slugs=all_slugs)

    def update_price(self, simple_objects_list=None):
        print('---UPDATE BIG OBJECT PRICE---', self)
        if simple_objects_list is None:
            simple_objects_list = BigObjectList.objects.filter(big_object=self)
        total_price = 0
        for simple_object in simple_objects_list:
            total_price += simple_object.total_price
        self.price = total_price
        if self.price == 0:
            self.price_text = '0,00'
        else:
            self.price_text = gen_text_price(self.price)
        # self.save()

    def update_simple_objects(self, old_self=None):
        if self.status == 'IW':
            """Если статус рабочий, тогда обновляем количество свободных простых объектов"""
            # self.update_price()
            all_simple_objects = SimpleObject.objects.filter(big_object_list__big_object=self)
            for simple_object in all_simple_objects:
                simple_object.save()

        elif self.status in ['WO', 'NW', 'RD']:
            """Если старый статус был в работе а новый нет, тогда зануляем цену и обновляем свободные простые объекты"""
            self.price = 0
            self.price_text = '0,00'
            all_simple_objects = SimpleObject.objects.filter(big_object_list__big_object=self)
            for simple_object in all_simple_objects:
                if self.status == 'RD' and old_self.status == 'IW':
                    """Если статус изменился с рабочего на готовый, тогда вычитаем количество использованных
                    простых объектов в этой камере из общего числа этих объектов"""
                    amount = BigObjectList.objects.get(big_object=self, simple_object=simple_object).amount
                    simple_object.amount -= amount
                simple_object.save()
            if self.status == 'RD' and old_self.status == 'IW':
                """После сохранения всех простых объектов списываем их если статус
                сложного объекта изменился на готовый и количество простых объектов == 0"""
                all_simple_objects.filter(amount=0).update(status='WO')

    def delete(self, *args, **kwargs):
        self.status = 'WO'
        self.save()
        super().delete(*args, **kwargs)


class FileAndImageCategoryForBigObject(models.Model):
    big_object = models.ForeignKey(BigObject, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Объект')
    name = models.CharField(max_length=150, verbose_name='Название категории')
    text = models.TextField(max_length=2000, verbose_name='Описание', blank=True)
    slug = models.SlugField(max_length=250, blank=True, null=True, verbose_name='Название на латинице')

    class Meta:
        verbose_name = 'Категория документов для сложного объекта'
        verbose_name_plural = 'Категории документов для сложных объектов'

    def __str__(self):
        return '{} , для {}'.format(self.name, self.big_object.name)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.slug = gen_slug_for_categories(self.name)
        else:
            old_self = FileAndImageCategoryForBigObject.objects.get(pk=self.pk)
            if old_self.name != self.name:
                self.slug = gen_slug_for_categories(self.name)
        super().save(*args, **kwargs)


class ImageForBigObject(models.Model):
    big_object = models.ForeignKey(BigObject, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Объект')
    image = models.ImageField(verbose_name='Изображение', upload_to=generate_path)
    image_big = models.ImageField(blank=True, upload_to=generate_path,
                                  verbose_name='Фото без сжатия, создается само при сохранеии')
    category = models.ForeignKey(
        FileAndImageCategoryForBigObject, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Категория',
        related_name='images', related_query_name='image'
    )

    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения для объектов'

    def __str__(self):
        return 'Изображение для ' + str(self.big_object.name)

    def filename(self):
        return os.path.basename(self.image.name)

    def save(self, *args, **kwargs):
        print('---SAVE PHOTO---')
        if self.pk is not None:
            old_self = ImageForBigObject.objects.get(pk=self.pk)
            if self.image != old_self.image:
                if len(self.image.name) > 50:
                    self.image.name = str(self.image.name)[50::]

                super().save(*args, **kwargs)
                some_model_save_photo(self, 700, 700)
        else:
            if len(self.image.name) > 50:
                self.image.name = str(self.image.name)[50::]

            super().save(*args, **kwargs)
            some_model_save_photo(self, 700, 700)

        super().save(*args, **kwargs)

    def change_photo(self, new_image):
        print('---CHANGE PHOTO---')
        self.image.delete(False)
        self.image_big.delete(False)
        self.image = new_image
        self.save()

    def change_path(self, *args, **kwargs):
        print('---CHANGE PATH---')
        for image in [self.image, self.image_big]:
            image_name = str(image.path).rsplit(os.sep, 1)[1]
            image.name = generate_path(self, image_name)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        print("---УДАЛЕНИЕ---")
        self.image.delete(False)
        self.image_big.delete(False)
        super().delete(*args, **kwargs)


class FileForBigObject(models.Model):
    big_object = models.ForeignKey(BigObject, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Объект')
    file = models.FileField(upload_to=generate_path_for_files, verbose_name='Файл')
    category = models.ForeignKey(
        FileAndImageCategoryForBigObject, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Категория',
        related_name='files', related_query_name='file'
    )

    class Meta:
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы для объектов'

    def __str__(self):
        return 'Файл для ' + str(self.big_object.name)

    def filename(self):
        return os.path.basename(self.file.name)

    def delete(self, *args, **kwargs):
        self.file.delete(save=False)
        super().delete(*args, **kwargs)


class BigObjectList(models.Model):
    simple_object = models.ForeignKey(
        to=SimpleObject,
        on_delete=models.CASCADE,
        related_name='big_objects_list',
        related_query_name='big_object_list',
        verbose_name='Простой объект',
    )
    amount = models.FloatField(verbose_name='Количество', default=0)
    total_price = models.FloatField(verbose_name='Сумма', default=0, blank=True)
    total_price_text = models.CharField(verbose_name='Сумма с пробелами', max_length=100, blank=True)
    big_object = models.ForeignKey(to=BigObject, verbose_name='Сложный объект', on_delete=models.CASCADE, blank=True)
    history = HistoricalRecords(verbose_name='История')  # История изменений

    class Meta:
        verbose_name = 'Составляющая сложного объекта'
        verbose_name_plural = 'Составляющие сложного объекта'
        ordering = ['simple_object__name_lower']

    def __str__(self):
        return f'{self.simple_object.name}, количетво : {self.amount}'

    def save(self, *args, **kwargs):
        print('---SAVE BIG OBJECT LIST---')
        self.update_total_price()
        super().save(*args, **kwargs)

    def update_total_price(self):
        self.total_price = self.amount * self.simple_object.price
        self.total_price_text = gen_text_price(self.total_price)
        # self.save()


class WorkerEquipment(models.Model):
    profile = models.ForeignKey(to=Profile, on_delete=models.CASCADE, verbose_name='Профиль', blank=True)
    simple_object = models.ForeignKey(
        to=SimpleObject,
        on_delete=models.CASCADE,
        related_name='worker_objects_list',
        related_query_name='worker_object_list',
        verbose_name='Объект'
    )
    amount = models.FloatField(verbose_name='Количество', default=0)
    # history = HistoricalRecords(verbose_name='История')  # История изменений

    class Meta:
        verbose_name = 'Оборудование у сотрудника'
        verbose_name_plural = 'Обородувания у сотрудников'
        ordering = ['simple_object__name_lower']

    def __str__(self):
        return f'{self.simple_object.name}, количетво : {self.amount}'

    def save(self, *args, **kwargs):
        print('---SAVE WORKER EQUIPMENT LIST---')
        super().save(*args, **kwargs)


# class AllSlugs(models.Model):
#     class ChoicesObjectType(models.TextChoices):
#         BASE_OBJECT = 'BO', _('Базовый объект')
#         SIMPLE_OBJECT = 'SO', _('Простой объект')
#         BIG_OBJECT = 'BG', _('Составной объект')
#         CATEGORY = 'CT', _('Категория')
#         LABORATORY = 'LB', _('Лаборатория')
#     slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name='URL')
#     lab = models.ForeignKey(LabName, on_delete=models.CASCADE, verbose_name='Лаборатория', blank=True, null=True)
#     cat_type = models.CharField(
#         max_length=2,
#         choices=ChoicesObjectType.choices,
#         default=ChoicesObjectType.SIMPLE_OBJECT,
#         verbose_name='Тип категории'
#     )
#
#     class Meta:
#         verbose_name = 'Список Url_ов'
#         verbose_name_plural = 'Списки Url_ов'
#
#     def __str__(self):
#         return self.slug


class DataBaseDoc(models.Model):
    name = models.CharField(max_length=150, verbose_name='Название файла')
    lab = models.ForeignKey(LabName, on_delete=models.PROTECT, verbose_name='Лаборатория', blank=True, null=True)
    file = models.FileField(upload_to=generate_path_for_database, verbose_name='Файл')
    date_add = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Файл с данными'
        verbose_name_plural = 'Файлы с данными'

    def __str__(self):
        if self.lab:
            return '{} {}'.format(self.name, self.lab.name)
        else:
            return self.name

    def update_all_data(self, create_simple_objects=False):
        from openpyxl import load_workbook
        wb = load_workbook(self.file.path)
        sheet = wb.worksheets[0]
        for row in sheet.iter_rows(values_only=True, min_row=1):
            category, created = Category.objects.get_or_create(name=row[3], lab=self.lab, cat_type='BO')

            base_object = BaseObject(
                name=row[2].strip(),
                lab=self.lab,
                inventory_number=row[0],
                directory_code=row[1],
                measure=row[5],
                total_price=float(row[7]),
                amount=float(row[6]),
                category=category,
            )
            base_object.save()

            if create_simple_objects is True:
                if row[4] is not None:
                    simple_category, created = Category.objects.get_or_create(name=row[4], lab=self.lab, cat_type='SO')
                else:
                    simple_category, created = Category.objects.get_or_create(
                        name='Разное ({})'.format(category.name.lower()), lab=self.lab, cat_type='SO'
                    )

                SimpleObject(
                    base_object=base_object,
                    name=base_object.name,
                    lab=self.lab,
                    inventory_number=base_object.inventory_number,
                    directory_code=base_object.directory_code,
                    measure=base_object.measure,
                    price=round(base_object.total_price / base_object.amount, 2),
                    amount=base_object.amount,
                    category=simple_category,
                ).save()

    def delete(self, *args, **kwargs):
        self.file.delete(save=False)
        super().delete(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
