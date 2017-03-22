"""
modulo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import include, url
from . import views

app_name = 'modulo'

module_patterns = [
    url(r'^$', views.module_index, name='modulo-module'),
    url(r'^(?P<module_title>["\'\w\s\-\.?!():&,_/]+)$', views.module, name='modulo-module-title'),
]

category_patterns = [
    url(r'^$', views.category_index, name='modulo-category'),
    url(r'^(?P<category_name>[\w\s\-]+)$', views.category, name='modulo-category-name'),
]

interest_patterns = [
    url(r'^$', views.interest_index, name='modulo-interest'),
    url(r'^(?P<interest_name>[\w\s\-]+)$', views.interest, name='modulo-interest-name'),
]

documentation_patterns = [
    url(r'^$', views.documentation, name='modulo-documentation'),
    url(r'^category/', include(category_patterns)),
    url(r'^interest/', include(interest_patterns)),
    url(r'^module/', include(module_patterns)), 
]

urlpatterns = [
    url(r'^$', views.index, name='modulo-index'),
    url(r'^recommend/$', views.recommend, name='modulo-recommend'),
    url(r'^documentation/', include(documentation_patterns)),
]