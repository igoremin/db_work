from django.urls import path
from .views import task_list, task_page, task_form, create_task_for_exist_task, change_task_status

urlpatterns = [
    path('<str:lab>/all/', task_list, name='task_list_for_current_lab'),
    path('<str:lab>/all/<int:pk>/', task_page, name='task_page_url'),
    path('<str:lab>/create_new_task/', task_form, name='new_task_form_url'),
    path('<str:lab>/all/<int:pk>/update_task/', task_form, name='update_task_url'),
    path('<str:lab>/all/<int:pk>/create_new_task/', create_task_for_exist_task, name='create_task_for_task_url'),
    path('<str:lab>/all/<int:pk>/change_status/', change_task_status, name='change_task_status_url'),

]
