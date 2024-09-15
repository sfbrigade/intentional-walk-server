"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.urls import include, path
from ninja import NinjaAPI

from home.views.apiv2.appuser import router as appuser_router
from home.views.apiv2.contest import router as contest_router
from home.views.apiv2.dailywalk import router as daily_walk_router
from home.views.apiv2.device import router as device_router
from home.views.apiv2.export import router as export_router
from home.views.apiv2.intentionalwalk import router as intentional_walk_router
from home.views.apiv2.leaderboard import router as leaderboard_router
from home.views.apiv2.weeklygoal import router as weeklygoal_router
from home.views.apiv2.admin import router as admin_router

api = NinjaAPI()
api.add_router("/appuser", appuser_router)
api.add_router("/contest", contest_router)
api.add_router("/device", device_router)
api.add_router("/dailywalk", daily_walk_router)
api.add_router("/export", export_router)
api.add_router("/intentionalwalk", intentional_walk_router)
api.add_router("/leaderboard", leaderboard_router)
api.add_router("/weeklygoal", weeklygoal_router)
api.add_router("/admin", admin_router)


urlpatterns = [
    path("", include("home.urls")),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("api/v2/", api.urls),
]
