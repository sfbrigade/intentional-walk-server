from django.urls import path

from . import views

app_name = "home"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home_view"),
    path("users/", views.UserListView.as_view(), name="user_list_view"),
    path("intentionalwalks/", views.IntentionalWalkWebView.as_view(), name="int_walk_list_view"),
    path("api/appuser/create", views.AppUserCreateView.as_view(), name="appuser_create"),
    path("api/dailywalk/create", views.DailyWalkCreateView.as_view(), name="dailywalk_create"),
    path("api/dailywalk/get", views.DailyWalkListView.as_view(), name="dailywalk_get"),
    path("api/intentionalwalk/create", views.IntentionalWalkView.as_view(), name="intentionalwalk_create",),
    path("api/intentionalwalk/get", views.IntentionalWalkListView.as_view(), name="intentionalwalk_get",),
    path("api/contest/current", views.ContestCurrentView.as_view(), name="contest_current"),
]
