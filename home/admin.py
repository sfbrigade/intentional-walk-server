from django.contrib import admin
from .models import Device, Account, DailyWalk, IntentionalWalk, Contest


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["account", "device_id", "created"]
    list_display_links = ["account"]
    ordering = ["-created"]
    search_fields = ["account"]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "is_tester", "is_sf_resident", "created", "updated"]
    list_display_links = ["email", "name"]
    ordering = ["-created"]
    search_fields = ["email", "name", "zip"]


@admin.register(DailyWalk)
class DailyWalkAdmin(admin.ModelAdmin):
    list_display = ["account", "date", "steps", "distance"]
    list_display_links = ["account", "date", "steps", "distance"]
    readonly_fields = ['account', "created", "updated"]
    ordering = ["-date"]
    search_fields = ["account"]


@admin.register(IntentionalWalk)
class IntentionalWalkAdmin(admin.ModelAdmin):
    list_display = ["account", "start", "end", "steps", "distance"]
    list_display_links = ["account", "start", "end", "steps", "distance"]
    readonly_fields = ['account', "created"]
    ordering = ["-start"]
    search_fields = ["account"]


@admin.register(Contest)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ["start_promo", "start", "end", "contest_id"]
    list_display_links = ["contest_id"]
    ordering = ["-start_promo"]
    search_fields = []