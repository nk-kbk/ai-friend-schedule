# notifications_app/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse, NoReverseMatch

class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='通知先ユーザー'
    )
    notification_type = models.CharField(max_length=50, verbose_name='通知種別')
    message = models.TextField(verbose_name='通知メッセージ')
    is_read = models.BooleanField(default=False, verbose_name='既読フラグ')
    related_item_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='関連アイテムID')
    related_item_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='関連アイテム種別')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']

    def __str__(self):
        read_status = "既読" if self.is_read else "未読"
        user_display = self.user.username if hasattr(self.user, 'username') else str(self.user.id)
        return f"{user_display}への通知 ({self.notification_type}, {read_status}): {self.message[:50]}..."

    def get_absolute_url(self):
        url = None
        # print(f"DEBUG get_absolute_url: Notification ID={self.id}, Type='{self.notification_type}', ItemID={self.related_item_id}, ItemType='{self.related_item_type}'") # デバッグ開始
        if self.related_item_id and self.related_item_type: # 両方存在するかチェック
            try:
                if self.notification_type == 'friend_request' and self.related_item_type == 'friendship':
                    url = reverse('accounts:friend_requests_received')
                elif self.notification_type == 'friend_request_accepted' and self.related_item_type == 'friendship':
                    url = reverse('accounts:friend_list')
                
                elif self.notification_type == 'schedule_adjustment_request_received' and self.related_item_type == 'schedule_adjustment_request':
                    url = reverse('schedule_requests_app:schedule_request_detail', args=[self.related_item_id])
                
                elif self.notification_type == 'schedule_adjustment_request_accepted' and self.related_item_type == 'schedule_adjustment_request':
                    url = reverse('schedule_requests_app:schedule_request_detail', args=[self.related_item_id])
                elif self.notification_type == 'schedule_adjustment_request_declined' and self.related_item_type == 'schedule_adjustment_request':
                    url = reverse('schedule_requests_app:schedule_request_detail', args=[self.related_item_id])
                
                elif self.notification_type == 'schedule_invitation_proposal' and self.related_item_type == 'aicharacter':
                    # url = reverse('ai_assistant_app:ai_chat', args=[self.related_item_id])
                    pass 
                elif self.notification_type == 'schedule_reminder' and self.related_item_type == 'schedule':
                    url = reverse('calendar_app:schedule_detail', args=[self.related_item_id])
                
                # if url:
                # print(f"DEBUG get_absolute_url: Successfully generated URL: {url}")
                # else:
                # print(f"DEBUG get_absolute_url: No matching URL for this notification type and item type.")

            except NoReverseMatch as e:
                print(f"ERROR get_absolute_url: NoReverseMatch for notification ID {self.id}, type '{self.notification_type}', item ID {self.related_item_id}, item type '{self.related_item_type}'. Error: {e}")
            except Exception as e:
                print(f"ERROR get_absolute_url: Generic error for notification ID {self.id} (type: {self.notification_type}): {e}")
        # else:
            # print(f"DEBUG get_absolute_url: related_item_id or related_item_type is missing for Notification ID {self.id}")
            
        return url