from django.contrib import admin
from .models import AICharacter, AIChatHistory

@admin.register(AICharacter)
class AICharacterAdmin(admin.ModelAdmin):
    list_display = ('character_name', 'description', 'icon_url', 'created_at', 'updated_at')
    search_fields = ('character_name', 'description')
    list_filter = ('created_at',)
    # readonly_fields = ('created_at', 'updated_at')

@admin.register(AIChatHistory)
class AIChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'ai_character', 'sender_type', 'message_text_summary', 'timestamp')
    list_filter = ('ai_character', 'sender_type', 'timestamp', 'user')
    search_fields = ('user__username', 'ai_character__character_name', 'message_text')
    readonly_fields = ('timestamp',) # 基本的に編集させない

    def message_text_summary(self, obj):
        return obj.message_text[:50] + "..." if len(obj.message_text) > 50 else obj.message_text
    message_text_summary.short_description = 'メッセージ概要'