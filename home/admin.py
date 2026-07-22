from django.contrib import admin
from .models import Category, FCMDevice

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "category_type", "visiting_charge", "is_trending", "trending_order")
    list_filter = ("category_type", "is_trending")
    search_fields = ("name",)

@admin.register(FCMDevice)
class FCMDeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at")
