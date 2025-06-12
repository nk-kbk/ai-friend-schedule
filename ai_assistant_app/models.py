from django.db import models
from django.conf import settings

class AICharacter(models.Model):
    character_name = models.CharField(max_length=100, unique=True, verbose_name='キャラクター名')
    description = models.TextField(blank=True, null=True, verbose_name='キャラクター説明')
    prompt_template = models.TextField(verbose_name='プロンプトテンプレート')
    icon_url = models.CharField(max_length=255, blank=True, null=True, verbose_name='アイコン画像URL') # URLFieldも検討
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    def __str__(self):
        return self.character_name

    class Meta:
        verbose_name = 'AIキャラクター'
        verbose_name_plural = 'AIキャラクター'
        ordering = ['character_name']

class AIChatHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='ユーザー'
    )
    ai_character = models.ForeignKey(
        AICharacter,
        on_delete=models.CASCADE,
        verbose_name='AIキャラクター'
    )
    session_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='セッションID') # UUIDなども検討
    message_text = models.TextField(verbose_name='メッセージ内容')
    
    SENDER_USER = 'user'
    SENDER_AI = 'ai'
    SENDER_CHOICES = [
        (SENDER_USER, 'ユーザー'),
        (SENDER_AI, 'AI'),
    ]
    sender_type = models.CharField(
        max_length=10,
        choices=SENDER_CHOICES,
        verbose_name='送信者種別'
    )
    # (将来用) related_event = models.ForeignKey('calendar_app.Schedule', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='関連予定')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='送信日時')

    class Meta:
        verbose_name = 'AI会話履歴'
        verbose_name_plural = 'AI会話履歴'
        ordering = ['timestamp'] # 時系列順

    def __str__(self):
        user_display = self.user.username if hasattr(self.user, 'username') else str(self.user.id)
        return f"{user_display} to {self.ai_character.character_name} ({self.get_sender_type_display()}): {self.message_text[:30]}..."