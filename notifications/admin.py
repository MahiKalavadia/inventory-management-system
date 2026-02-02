from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'role_target', 'type', 'is_read', 'created_at')
    list_filter = ('role_target', 'type', 'is_read')
    search_fields = ('title', 'message')
