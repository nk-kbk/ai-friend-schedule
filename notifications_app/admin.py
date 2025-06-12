from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'message_summary', 'is_read', 'created_at', 'related_item_type', 'related_item_id')
    list_filter = ('is_read', 'notification_type', 'created_at', 'user')
    search_fields = ('user__username', 'message', 'related_item_type')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_as_read_admin', 'mark_as_unread_admin']

    def message_summary(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_summary.short_description = 'メッセージ概要'

    def mark_as_read_admin(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read_admin.short_description = "選択された通知を既読にする"

    def mark_as_unread_admin(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread_admin.short_description = "選択された通知を未読にする"