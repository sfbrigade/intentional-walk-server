from django.contrib import admin
from .models import AppUser, DailyWalk, IntentionalWalk


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "zip", "age", "created"]
    list_display_links = ["name"]
    ordering = ["-created"]
    search_fields = ["name", "zip"]


@admin.register(DailyWalk)
class DailyWalkAdmin(admin.ModelAdmin):
    list_display = ["appuser", "date", "steps"]
    list_display_links = ["appuser", "date", "steps"]
    ordering = ["-date"]
    search_fields = ["user__name"]


@admin.register(IntentionalWalk)
class IntentionalWalkAdmin(admin.ModelAdmin):
    list_display = ["pk", "appuser", "start", "end", "steps"]
    list_display_links = ["appuser", "start", "end", "steps"]
    ordering = ["-start"]
    search_fields = ["user__name"]
