"""webapps URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.urls import path
from django.conf.urls import url

from online_shop import views

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^home$', views.home,name='home'),
    # url(r'^make_transaction$', views.make_transaction, name='make_transaction'),
    url(r'^detect$', views.detect, name='detect'),
    url(r'^update$', views.update, name='update'),
    url(r'^update_single$', views.update_single, name='update_single'),
    url(r'^get_current_record$', views.get_current_record, name='get_current_record'),
]
