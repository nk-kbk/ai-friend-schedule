# schedule_requests_app/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import traceback

class ScheduleAdjustmentRequest(models.Model):
    """
    ユーザー間の日程調整申請を管理するモデル (新規予定に特化)
    """
    # --- 申請ステータス ---
    REQUEST_STATUS_PENDING = 'pending'
    REQUEST_STATUS_ACCEPTED = 'accepted'
    REQUEST_STATUS_DECLINED = 'declined'
    REQUEST_STATUS_CANCELED = 'canceled'
    
    STATUS_CHOICES = [
        (REQUEST_STATUS_PENDING, '申請中'),
        (REQUEST_STATUS_ACCEPTED, '承認済み'),
        (REQUEST_STATUS_DECLINED, '拒否済み'),
        (REQUEST_STATUS_CANCELED, 'キャンセル済み'),
    ]

    # --- 誰から誰への申請か ---
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_schedule_requests',
        on_delete=models.CASCADE,
        verbose_name='申請者'
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='received_schedule_requests',
        on_delete=models.CASCADE,
        verbose_name='被申請者'
    )

    # --- ✨✨ ここが修正ポイント！ ✨✨ ---
    # 提案された予定の内容
    # proposed_title は使わなくなるので、コメントアウトか削除してもOKだよ！
    # proposed_title = models.CharField(max_length=200, verbose_name='提案タイトル') 
    title_for_requester = models.CharField(max_length=200, verbose_name='申請者用のタイトル')
    title_for_invitee = models.CharField(max_length=200, verbose_name='被申請者用のタイトル')
    # --- ✨✨ 修正ここまで！ ✨✨ ---

    proposed_start_datetime = models.DateTimeField(verbose_name='提案開始日時')
    proposed_end_datetime = models.DateTimeField(verbose_name='提案終了日時')
    proposed_location = models.CharField(max_length=255, blank=True, null=True, verbose_name='提案場所')
    proposed_description = models.TextField(blank=True, null=True, verbose_name='提案詳細（AIからの理由など）')

    # --- 申請のステータス ---
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=REQUEST_STATUS_PENDING,
        verbose_name='申請ステータス'
    )

    # --- タイムスタンプ ---
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='申請作成日時')
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='応答日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='最終更新日時')

    # --- 承認後に作成されたScheduleへのリンク ---
    # ✨✨ ここも修正ポイント！ 承認時に1つの共有スケジュールを作るように変更するよ！✨✨
    related_schedule = models.ForeignKey(
        'calendar_app.Schedule',
        related_name='adjustment_request_source',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='承認後に作成された予定'
    )
    # related_schedule_requester と related_schedule_invitee は使わなくなるよ！
    # related_schedule_requester = models.ForeignKey(...)
    # related_schedule_invitee = models.ForeignKey(...)

    class Meta:
        verbose_name = '日程調整申請'
        verbose_name_plural = '日程調整申請'
        ordering = ['-created_at']

    def __str__(self):
        # 表示を申請者用のタイトルにする
        return f"{self.requester.username}から{self.invitee.username}への「{self.title_for_requester}」の申請 ({self.get_status_display()})"

    # accept_request, decline_request, cancel_request などのメソッドは
    # views.py のロジックに統合するので、ここではシンプルにしておくか、
    # もし使うなら中のロジックを修正する必要があるよ！
    # 今回は views.py で全部やるので、一旦そのままで大丈夫！