from django.contrib import admin
from .models import SimpleObject, LabName, Category, Profile, BigObject, BigObjectList, ImageForBigObject,\
    FileAndImageCategory, FileForBigObject, DataBaseDoc, BaseObject, BaseBigObject, Room


admin.site.register(LabName)
admin.site.register(Profile)
admin.site.register(ImageForBigObject)
admin.site.register(FileForBigObject)
admin.site.register(FileAndImageCategory)
admin.site.register(DataBaseDoc)
admin.site.register(Room)
# admin.site.register(BigObject)


@admin.register(BaseObject)
class BaseObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'measure', 'inventory_number', 'amount')
    search_fields = ('name_lower', 'name', 'inventory_number', 'directory_code')


@admin.register(BigObjectList)
class BigObjectListAdmin(admin.ModelAdmin):
    list_filter = ('big_object', )


@admin.register(BaseBigObject)
class BigObjectAdmin(admin.ModelAdmin):
    list_filter = ('lab', 'category')


@admin.register(BigObject)
class BigObjectAdmin(admin.ModelAdmin):
    list_filter = ('status', 'top_level')


@admin.register(SimpleObject)
class SimpleObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'measure', 'inventory_number', 'amount')
    list_filter = ('lab', 'category')
    search_fields = ('name', 'name_lower', 'inventory_number', 'directory_code')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'lab')
    list_filter = ('lab',)
