from django.urls import path

from . import views

app_name = 'home'
urlpatterns = [
    path('api/appuser/create', views.AppUserCreateView.as_view(), name='appuser_create'),

    path('api/dailywalk/create', views.DailyWalkView.as_view(), name='dailywalk_create'),
    path('api/dailywalk/get', views.DailyWalkListView.as_view(), name='dailywalk_get'),

    path('api/intentionalwalk/create', views.IntentionalWalkView.as_view(), name='intentionalwalk_create'),
    path('api/intentionalwalk/get', views.IntentionalWalkListView.as_view(), name='intentionalwalk_get'),
]