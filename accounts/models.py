# accounts/models.py の完全なコード

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    selected_ai_character_id = models.IntegerField(null=True, blank=True, verbose_name='選択中AIキャラID')
    
    # --- ✨ ここが追加された部分！ ---
    profile_image = models.ImageField(
        upload_to='profile_images/', 
        null=True, 
        blank=True, 
        verbose_name='プロフィール画像'
    )
    # --- ✨ 追加ここまで！ ---

    def __str__(self):
        return self.username

class Friendship(models.Model):
    user_from = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_friend_requests',
        on_delete=models.CASCADE,
        verbose_name='申請者'
    )
    user_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='received_friend_requests',
        on_delete=models.CASCADE,
        verbose_name='被申請者'
    )

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_BLOCKED = 'blocked'

    FRIENDSHIP_STATUS_CHOICES = [
        (STATUS_PENDING, '申請中'),
        (STATUS_ACCEPTED, '承認済み'),
        (STATUS_DECLINED, '拒否済み'),
        (STATUS_BLOCKED, 'ブロック中'),
    ]
    status = models.CharField(
        max_length=10,
        choices=FRIENDSHIP_STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='関係ステータス'
    )
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name='申請日時')
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='応答日時')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='レコード作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='レコード更新日時')

    class Meta:
        unique_together = ('user_from', 'user_to')
        ordering = ['-requested_at']
        verbose_name = '友達関係'
        verbose_name_plural = '友達関係'

    def __str__(self):
        return f"{self.user_from.username} -> {self.user_to.username} ({self.get_status_display()})"