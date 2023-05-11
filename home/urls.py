import os

from django.urls import path
from django.views.generic import TemplateView

from . import views

PRODUCTION = os.getenv("DEPLOY_ENV") == "production"

app_name = "home"

urlpatterns = []
if PRODUCTION:
    # serve the React SPA index.html as a catch-all
    urlpatterns = [
        path("users/", TemplateView.as_view(template_name="index.html")),
        path("login/", TemplateView.as_view(template_name="index.html")),
    ]
else:
    # mount old views for comparison testing until fully deprecated and removed
    urlpatterns = [
        path("", views.HomeView.as_view(), name="home_view"),
        path("users/", views.UserListView.as_view(), name="user_list_view"),
        path(
            "intentionalwalks/",
            views.IntentionalWalkWebView.as_view(),
            name="int_walk_list_view",
        ),
        path(
            "data/users_agg.csv",
            views.user_agg_csv_view,
            name="users_agg_csv_view",
        ),
        path("data/users.csv", views.users_csv_view, name="users_csv_view"),
        path(
            "data/daily_walks.csv",
            views.daily_walks_csv_view,
            name="dailywalks_csv_view",
        ),
        path(
            "data/intentional_walks.csv",
            views.intentional_walks_csv_view,
            name="intentionalwalks_csv_view",
        ),
    ]

urlpatterns = urlpatterns + [
    path("api/admin/me", views.AdminMeView.as_view(), name="admin_me"),
    path("api/admin/home", views.AdminHomeView.as_view(), name="admin_home"),
    path(
        "api/admin/home/users/daily",
        views.AdminHomeUsersDailyView.as_view(),
        name="admin_home_users_daily",
    ),
    path(
        "api/admin/home/users/cumulative",
        views.AdminHomeUsersCumulativeView.as_view(),
        name="admin_home_users_cumulative",
    ),
    path(
        "api/admin/home/steps/daily",
        views.AdminHomeStepsDailyView.as_view(),
        name="admin_home_steps_daily",
    ),
    path(
        "api/admin/home/steps/cumulative",
        views.AdminHomeStepsCumulativeView.as_view(),
        name="admin_home_steps_cumulative",
    ),
    path(
        "api/admin/home/distance/daily",
        views.AdminHomeDistanceDailyView.as_view(),
        name="admin_home_distance_daily",
    ),
    path(
        "api/admin/home/distance/cumulative",
        views.AdminHomeDistanceCumulativeView.as_view(),
        name="admin_home_distance_cumulative",
    ),
    path(
        "api/admin/contests",
        views.AdminContestsView.as_view(),
        name="admin_contests",
    ),
    path(
        "api/admin/users", views.AdminUsersView.as_view(), name="admin_users"
    ),
    path(
        "api/admin/users/zip",
        views.AdminUsersByZipView.as_view(),
        name="admin_users_zip",
    ),
    path(
        "api/admin/users/zip/active",
        views.AdminUsersActiveByZipView.as_view(),
        name="admin_users_zip_active",
    ),
    path(
        "api/admin/users/zip/steps",
        views.AdminUsersByZipMedianStepsView.as_view(),
        name="admin_users_zip_steps",
    ),
    path(
        "api/admin/users/age/between",
        views.AdminUsersByAgeGroupView.as_view(),
        name="admin_users_age_between",
    ),
    path(
        "api/admin/users/age/between/dates",
        views.AdminUsersByAgeGroupDatesView.as_view(),
        name="admin_users_age_between",
    ),
    path(
        "api/appuser/create",
        views.AppUserCreateView.as_view(),
        name="appuser_create",
    ),
    path(
        "api/appuser/delete",
        views.AppUserDeleteView.as_view(),
        name="appuser_delete",
    ),
    path(
        "api/dailywalk/create",
        views.DailyWalkCreateView.as_view(),
        name="dailywalk_create",
    ),
    path(
        "api/dailywalk/get",
        views.DailyWalkListView.as_view(),
        name="dailywalk_get",
    ),
    path(
        "api/export/users",
        views.ExportUsersView.as_view(),
        name="export_users",
    ),
    path(
        "api/intentionalwalk/create",
        views.IntentionalWalkView.as_view(),
        name="intentionalwalk_create",
    ),
    path(
        "api/intentionalwalk/get",
        views.IntentionalWalkListView.as_view(),
        name="intentionalwalk_get",
    ),
    path(
        "api/contest/current",
        views.ContestCurrentView.as_view(),
        name="contest_current",
    ),
    path(
        "api/leaderboard/get/",
        views.LeaderboardListView.as_view(),
        name="leaderboard_get",
    ),
]
