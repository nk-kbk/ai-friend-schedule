# calendar_app/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Schedule(models.Model):
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_schedules',
        verbose_name='作成者'
    )
    title = models.CharField(max_length=200, verbose_name='タイトル')
    description = models.TextField(blank=True, null=True, verbose_name='詳細')
    start_datetime = models.DateTimeField(verbose_name='開始日時')
    end_datetime = models.DateTimeField(verbose_name='終了日時')
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name='場所')
    
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='participating_schedules',
        blank=True,
        verbose_name='参加者'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '予定'
        verbose_name_plural = '予定'
        ordering = ['start_datetime']

    @property
    def is_today(self):
        today = timezone.now().date()
        start_date_local = timezone.localtime(self.start_datetime).date() if settings.USE_TZ else self.start_datetime.date()
        end_date_local = timezone.localtime(self.end_datetime).date() if settings.USE_TZ else self.end_datetime.date()
        return start_date_local <= today <= end_date_local

    def get_participant_names(self):
        # このメソッドが呼び出された時に初めてクエリが実行されるはず
        return ", ".join([user.username for user in self.participants.all()])
