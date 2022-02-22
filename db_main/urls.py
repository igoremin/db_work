"""db_main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from db_site.views import register
from db_site.forms import UserLoginForm


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('accounts/', include('django.contrib.auth.urls')),
    path('login/', views.LoginView.as_view(authentication_form=UserLoginForm), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', register, name="register"),
    path('feedback/', include('feedback.urls')),
    path('tracker/', include('tracker.urls')),
    path('telegram/', include('telegram_bot.urls')),
    path('documentation/', TemplateView.as_view(template_name='documentation.html'), name='doc_page_url'),
    path('favicon.ico/', RedirectView.as_view(url=staticfiles_storage.url('/db_site/favicon/LogoADL.gif'))),
    path('', include('db_site.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
