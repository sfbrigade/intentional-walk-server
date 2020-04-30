from django.contrib import admin
from .models import AppUser, Contest, DailyWalk, IntentionalWalk


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "zip", "age", "created", "account_id"]
    list_display_links = ["name"]
    ordering = ["-created"]
    search_fields = ["name", "zip"]


@admin.register(Contest)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ["start_promo", "start", "end", "contest_id"]
    list_display_links = ["contest_id"]
    ordering = ["-start_promo"]
    search_fields = []


@admin.register(DailyWalk)
class DailyWalkAdmin(admin.ModelAdmin):
    list_display = ["appuser", "date", "steps", "distance"]
    list_display_links = ["appuser", "date", "steps", "distance"]
    ordering = ["-date"]
    search_fields = ["user__name"]


@admin.register(IntentionalWalk)
class IntentionalWalkAdmin(admin.ModelAdmin):
    list_display = ["appuser", "start", "end", "steps", "distance", "event_id"]
    list_display_links = ["appuser", "start", "end", "steps", "distance", "event_id"]
    ordering = ["-start"]
    search_fields = ["user__name"]
