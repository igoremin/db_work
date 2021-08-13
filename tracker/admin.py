from django.contrib import admin
from .models import Task, CommentForTask


@admin.register(Task)
class BaseObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    search_fields = ('name', )


@admin.register(CommentForTask)
class BaseObjectAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'task')
