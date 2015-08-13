from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views


urlpatterns = [
    url(r'^domains/(?P<domain>[-A-Za-z0-9.]{4,253})/$',
        login_required(views.PrivateStatusDetail.as_view()), name='status-detail'),
    url(r'^(?P<domain>[-A-Za-z0-9.]{4,253})/$',
        views.StatusDetail.as_view(), name='public-status-detail'),
    url(r'^timeline/(?P<check>[0-9]{1,19})/$',
        views.CheckTimeline.as_view(), name='status-timeline'),
    url(r'^$', login_required(views.StatusList.as_view()), name='status-list'),
]
