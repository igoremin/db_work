from django.contrib import admin
from .models import SimpleObject, LabName, Category, Profile, BigObject, BigObjectList, ImageForBigObject,\
    FileAndImageCategoryForBigObject, FileForBigObject, DataBaseDoc, BaseObject


admin.site.register(LabName)
admin.site.register(Profile)
admin.site.register(ImageForBigObject)
admin.site.register(FileForBigObject)
admin.site.register(FileAndImageCategoryForBigObject)
admin.site.register(DataBaseDoc)
# admin.site.register(BaseObject)


@admin.register(BaseObject)
class BaseObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'measure', 'inventory_number', 'amount')
    search_fields = ('name_lower', 'name', 'inventory_number', 'directory_code')


@admin.register(BigObjectList)
class BigObjectListAdmin(admin.ModelAdmin):
    list_filter = ('big_object', )


@admin.register(BigObject)
class BigObjectAdmin(admin.ModelAdmin):
    list_filter = ('lab', 'category', 'status')


@admin.register(SimpleObject)
class SimpleObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'measure', 'inventory_number', 'amount')
    list_filter = ('lab', 'category')
    search_fields = ('name', 'name_lower', 'inventory_number', 'directory_code')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'lab')
    list_filter = ('lab',)
