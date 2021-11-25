from django.contrib import admin
from .models import SimpleObject, LabName, Category, Profile, BigObject, BigObjectList, ImageForObject,\
    FileAndImageCategory, FileForObject, DataBaseDoc, BaseObject, BaseBigObject, Room, Order, WorkerEquipment, Invoice,\
    InvoiceBaseObject, InvoiceType, WorkCalendar, Position


admin.site.register(LabName)
admin.site.register(Profile)
admin.site.register(ImageForObject)
admin.site.register(FileForObject)
admin.site.register(FileAndImageCategory)
admin.site.register(DataBaseDoc)
admin.site.register(Room)
admin.site.register(WorkerEquipment)
admin.site.register(Order)
admin.site.register(Invoice)
admin.site.register(InvoiceType)
admin.site.register(InvoiceBaseObject)
admin.site.register(Position)


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
    list_display = ('name', 'measure', 'amount')
    list_filter = ('lab', 'category')
    search_fields = ('name', 'name_lower')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'lab')
    list_filter = ('lab',)


@admin.register(WorkCalendar)
class WorkCalendarAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'date')
    list_filter = ('user', 'type')
    search_fields = ('date', )
