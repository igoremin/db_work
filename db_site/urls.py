from django.urls import path
from .views import simple_objects_list, home_page, simple_object_page, categories_list, category_page, big_object_page,\
    category_add_form, category_update_form, simple_object_add_form, simple_object_update_form,\
    simple_object_delete_form, big_object_add, big_object_update_components, big_object_update, search, worker_page,\
    big_object_history, simple_object_history, simple_objects_write_off_list, object_update_files_category,\
    object_delete_image, object_delete_file, load_new_db, base_object_page, worker_update_page,\
    worker_equipment_form, delete_all_data_for_lab, big_object_update_parts, big_object_delete_part,\
    base_big_object_page, room_page, backup, base_object_update_page, base_object_create_simple, worker_order_confirm,\
    order_list


urlpatterns = [
    path('', home_page, name='home_page_url'),
    path('<str:lab>/categories/', categories_list, name='categories_list_url'),
    path('<str:lab>/categories/add/', category_add_form, name='category_add_form_url'),
    path('<str:lab>/categories/<str:slug>/', category_page, name='category_page_url'),
    path('<str:lab>/categories/<str:slug>/update/', category_update_form, name='category_update_form_url'),
    path('<str:lab>/objects/', simple_objects_list, name='simple_objects_url'),
    path('<str:lab>/objects/write_off/', simple_objects_write_off_list, name='write_off_list_url'),
    path('<str:lab>/objects/write_off/type/<str:obj_type>/', simple_objects_write_off_list,
         name='write_off_list_for_obj_type_url'),
    path('<str:lab>/objects/type/<str:obj_type>/', simple_objects_list, name='simple_objects_for_obj_type_url'),
    path('<str:lab>/objects/add/', simple_object_add_form, name='simple_object_add_form_url'),
    path('<str:lab>/objects/<str:slug>/', simple_object_page, name='simple_object_url'),
    path('<str:lab>/objects/<str:slug>/history/', simple_object_history, name='simple_object_history_url'),
    path('<str:lab>/objects/<str:slug>/update/', simple_object_update_form, name='simple_object_update_form_url'),
    path('<str:lab>/objects/<str:slug>/delete/', simple_object_delete_form, name='simple_object_delete_form_url'),
    path('<str:lab>/base_big_objects/<str:slug>/', base_big_object_page, name='base_big_object_page_url'),
    path('<str:lab>/big_objects/create/', big_object_add, name='big_object_add_url'),
    path('<str:lab>/big_objects/<str:slug>/id=<str:pk>/', big_object_page, name='big_object_page_url'),
    path('<str:lab>/big_objects/<str:slug>/update/', big_object_update, name='big_object_update_url'),
    path('<str:lab>/big_objects/<str:slug>/history/', big_object_history, name='big_object_history_url'),
    path('<str:lab>/big_objects/<str:slug>/update_components/', big_object_update_components,
         name='big_object_update_components_url'),
    path('<str:lab>/big_objects/<str:slug>/update_parts/', big_object_update_parts,
         name='big_object_update_parts_url'),
    path('<str:lab>/big_objects/<str:slug>/delete_part/<int:pk>/', big_object_delete_part,
         name='big_object_delete_part_url'),
    path('<str:lab>/<str:object_type>/<str:slug>/update_files/<int:pk>/', object_update_files_category,
         name='object_update_category_files_url'),
    path('<str:lab>/image/<int:pk>/delete/', object_delete_image, name='object_delete_image_url'),
    path('<str:lab>/file/<int:pk>/delete/', object_delete_file, name='object_delete_file_url'),
    path('<str:lab>/base_objects/<str:slug>/', base_object_page, name='base_object_page_url'),
    path('<str:lab>/base_objects/<str:slug>/update/', base_object_update_page, name='base_object_update_page_url'),
    path('<str:lab>/base_objects/<str:slug>/create_simple/', base_object_create_simple,
         name='base_object_create_simple_url'),
    path('<str:lab>/search/', search, name='search_url'),
    path('<str:lab>/worker/<int:pk>/', worker_page, name='worker_page_url'),
    path('<str:lab>/worker/<int:pk>/update/', worker_update_page, name='worker_update_page_url'),
    path('<str:lab>/worker/<int:pk>/add_equipment/', worker_equipment_form, name='worker_equipment_form_url'),
    path('<str:lab>/room/<str:slug>/', room_page, name='room_page_url'),
    path('<str:lab>/database_file/add/', load_new_db, name='load_new_database_url'),
    path('<str:lab>/delete_all_data/', delete_all_data_for_lab, name='delete_all_data_for_lab_url'),
    path('<str:lab>/confirm_order/<int:pk>/', worker_order_confirm, name='worker_order_confirm_url'),
    path('<str:lab>/orders/', order_list, name='orders_list_url'),
    path('backup/', backup, name='backup_url'),
]
