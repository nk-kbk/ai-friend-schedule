# calendar_app/admin.py
from django.contrib import admin
from .models import Schedule

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'start_datetime', 
        'end_datetime', 
        'created_by_user', 
        'get_participant_names_display', # ✨ メソッド名変更 (adminメソッドと区別) ✨
        'created_at'
    )
    list_filter = (
        'created_by_user', 
        'start_datetime', 
        'participants'
    )
    search_fields = ('title', 'description', 'location', 'participants__username')
    date_hierarchy = 'start_datetime'
    filter_horizontal = ('participants',)

    # ✨ モデルのメソッドを呼び出す形に変更 ✨
    def get_participant_names_display(self, obj):
        return obj.get_participant_names() # モデルのメソッドを呼び出す
    get_participant_names_display.short_description = '参加者'