from django.urls import path
from .views import add_feedback, feedback_list, feedback_page, change_feedback

urlpatterns = [
    path('new/', add_feedback, name='feedback_form_url'),
    path('all/', feedback_list, name='feedback_list_url'),
    path('all/<int:pk>/', feedback_page, name='feedback_url'),
    path('all/<int:pk>/change/', change_feedback, name='change_feedback_form_url'),
]
