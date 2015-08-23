"""statuspage URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from .views import RegistrationView


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/$', auth_views.login, {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout_then_login, name='logout'),
    url(r'^password/change/$', auth_views.password_change,
        {'template_name': 'password-change.html'}, name='password_change'),
    url(r'^password/change/done/$', auth_views.password_change_done,
        {'template_name': 'password-change-done.html'}, name='password_change_done'),
    url(r'register/$', RegistrationView.as_view(), name='register'),
    url(r'^', include('domainchecks.urls')),
]
