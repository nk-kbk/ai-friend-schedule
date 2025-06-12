from django.contrib import admin
from .models import ScheduleAdjustmentRequest

@admin.register(ScheduleAdjustmentRequest)
class ScheduleAdjustmentRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        # 'proposed_title' の代わりに、2つの新しいタイトルを表示するよ！
        'title_for_requester',
        'title_for_invitee',
        'requester', 
        'invitee', 
        'status', 
        'proposed_start_datetime', 
        'created_at',
        # 'related_schedule_requester', 'related_schedule_invitee' の代わりに、新しい関連スケジュールを表示！
        'related_schedule',
    )
    list_filter = (
        'status', 
        'created_at', 
        'requester', 
        'invitee'
    )
    # search_fields も新しいタイトルを検索対象にするよ！
    search_fields = ('title_for_requester', 'title_for_invitee', 'requester__username', 'invitee__username') 
    readonly_fields = ('created_at', 'responded_at', 'updated_at')
    # raw_id_fields も新しい関連スケジュールを対象にするよ！
    raw_id_fields = ('related_schedule',)