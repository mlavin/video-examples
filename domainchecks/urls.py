from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^(?P<domain>[-A-Za-z0-9.]{4,253})/$',
        views.StatusDetail.as_view(), name='status-detail'),
    url(r'^$', views.StatusList.as_view(), name='status-list'),
]
