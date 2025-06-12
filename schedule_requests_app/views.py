# schedule_requests_app/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime
from .models import ScheduleAdjustmentRequest
from calendar_app.models import Schedule
from notifications_app.models import Notification
from django.contrib import messages
from django.db import transaction
import traceback
from accounts.models import User
import json

@login_required
def schedule_request_detail_view(request, request_id):
    schedule_request = get_object_or_404(ScheduleAdjustmentRequest, id=request_id)
    if not (request.user == schedule_request.requester or request.user == schedule_request.invitee):
        messages.error(request, "この日程調整申請の詳細を見る権限がありません。")
        return redirect('dashboard_top_page')

    if request.user == schedule_request.requester:
        display_title = schedule_request.title_for_requester
    else:
        display_title = schedule_request.title_for_invitee

    context = {
        'schedule_request': schedule_request,
        'display_title': display_title,
        'user_is_invitee_and_pending': (
            request.user == schedule_request.invitee and
            schedule_request.status == ScheduleAdjustmentRequest.REQUEST_STATUS_PENDING
        )
    }
    return render(request, 'schedule_requests_app/schedule_request_detail.html', context)


@login_required
@require_POST
def respond_schedule_request_view(request, request_id, action):
    schedule_request = get_object_or_404(ScheduleAdjustmentRequest, id=request_id)

    if request.user != schedule_request.invitee:
        messages.error(request, "この申請に応答する権限がありません。")
        return redirect('schedule_requests_app:schedule_request_detail', request_id=schedule_request.id)
    if schedule_request.status != ScheduleAdjustmentRequest.REQUEST_STATUS_PENDING:
        messages.warning(request, "この申請は既に応答済みか、取り消されています。")
        return redirect('schedule_requests_app:schedule_request_detail', request_id=schedule_request.id)
    if action not in ['accept', 'decline']:
        messages.error(request, "無効な操作です。")
        return redirect('schedule_requests_app:schedule_request_detail', request_id=schedule_request.id)

    if action == 'accept':
        try:
            with transaction.atomic():
                schedule_request.status = ScheduleAdjustmentRequest.REQUEST_STATUS_ACCEPTED
                schedule_request.responded_at = timezone.now()
                
                # --- ✨ここからが新しいタイトル改良の魔法だよ！✨ ---
                
                # 1. 誰が見ても分かりやすい、共有のタイトルを作る！
                #    申請者用タイトルから、相手の名前を抜いた「用件」部分だけを取り出す
                #    例：「ひろとくんとマック」 -> 「とマック」 -> 「マック」
                base_title = schedule_request.title_for_requester.replace(schedule_request.invitee.username, '').replace('と', '').strip()
                # 二人の名前をくっつけて、新しいタイトルを作る！
                shared_title = f"{schedule_request.requester.username}と{schedule_request.invitee.username}の{base_title}"

                # 2. 参加者リストを作成
                participants_to_add = [schedule_request.requester, schedule_request.invitee]
                
                # 3. ひとつの共有スケジュールを、新しい共有タイトルで作る！
                new_schedule = Schedule.objects.create(
                    created_by_user=schedule_request.requester, 
                    title=shared_title, # ✨ 新しいタイトルを使う！
                    start_datetime=schedule_request.proposed_start_datetime,
                    end_datetime=schedule_request.proposed_end_datetime,
                    location=schedule_request.proposed_location,
                    description=f"AIによる日程調整で決定した予定です。\n元々のAI提案メモ: {schedule_request.proposed_description or '特になし'}"
                )
                # 4. 作成した予定に、参加者をまとめて登録！
                new_schedule.participants.set(participants_to_add)
                
                # 5. 申請レコードに、作成された予定を紐付ける
                schedule_request.related_schedule = new_schedule
                schedule_request.save()
                # --- ✨魔法はここまで！✨ ---

                # 6. 申請者にお知らせを送信
                notification_message = f"{schedule_request.invitee.username}さんが「{schedule_request.title_for_requester}」の申請を承認しました！"
                Notification.objects.create(
                    user=schedule_request.requester,
                    notification_type='schedule_adjustment_request_accepted',
                    message=notification_message,
                    related_item_id=schedule_request.id,
                    related_item_type='schedule_adjustment_request'
                )
            
            messages.success(request, f"申請を承認し、カレンダーに予定を登録しました。")

        except Exception as e:
            messages.error(request, f"予定の登録または通知の作成中に予期せぬエラーが発生しました: {e}")
            traceback.print_exc()

    elif action == 'decline':
        # (拒否の処理は変更なしだよ！)
        try:
            with transaction.atomic():
                schedule_request.status = ScheduleAdjustmentRequest.REQUEST_STATUS_DECLINED
                schedule_request.responded_at = timezone.now()
                schedule_request.save()
                
                notification_message = f"残念ながら、{schedule_request.invitee.username}さんが「{schedule_request.title_for_requester}」の申請を拒否しました。"
                Notification.objects.create(
                    user=schedule_request.requester,
                    notification_type='schedule_adjustment_request_declined',
                    message=notification_message,
                    related_item_id=schedule_request.id,
                    related_item_type='schedule_adjustment_request'
                )
            messages.info(request, f"申請を拒否しました。")
        except Exception as e:
            messages.error(request, f"申請の拒否処理中に予期せぬエラーが発生しました: {e}")
            traceback.print_exc()

    return redirect('schedule_requests_app:schedule_request_detail', request_id=schedule_request.id)


@login_required
@require_POST
def create_schedule_request_from_ai_view(request):
    # (このビューは変更なしでOKだよ！)
    try:
        data = json.loads(request.body)

        required_fields = ['invitee_username', 'title_for_requester', 'title_for_invitee', 'proposed_start_datetime', 'proposed_end_datetime']
        if not all(field in data for field in required_fields):
            return JsonResponse({'status': 'error', 'message': 'AIからの情報が不足しています。'}, status=400)

        try:
            invitee_user = User.objects.get(username__iexact=data['invitee_username'])
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': f"お友達「{data['invitee_username']}」が見つかりませんでした。"}, status=404)

        start_dt_naive = datetime.strptime(data['proposed_start_datetime'], '%Y-%m-%d %H:%M')
        end_dt_naive = datetime.strptime(data['proposed_end_datetime'], '%Y-%m-%d %H:%M')
        if end_dt_naive <= start_dt_naive:
            return JsonResponse({'status': 'error', 'message': '終了日時は開始日時より後にする必要があります。'}, status=400)
            
        start_dt_aware = timezone.make_aware(start_dt_naive)
        end_dt_aware = timezone.make_aware(end_dt_naive)

        with transaction.atomic():
            new_request = ScheduleAdjustmentRequest.objects.create(
                requester=request.user,
                invitee=invitee_user,
                title_for_requester=data['title_for_requester'],
                title_for_invitee=data['title_for_invitee'],
                proposed_start_datetime=start_dt_aware,
                proposed_end_datetime=end_dt_aware,
                proposed_location=data.get('proposed_location'),
                proposed_description=data.get('proposed_description')
            )
            
            Notification.objects.create(
                user=invitee_user,
                notification_type='schedule_adjustment_request_received',
                message=f"{request.user.username}さんから「{new_request.title_for_invitee}」の新しい日程調整の申請が届きました。",
                related_item_id=new_request.id,
                related_item_type='schedule_adjustment_request'
            )
        
        return JsonResponse({
            'status': 'success', 
            'message': f"{invitee_user.username}さんに「{new_request.title_for_requester}」の日程調整申請を送りました！"
        })

    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': '日時の形式が正しくありません。'}, status=400)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': '申請の作成中にエラーが発生しました。'}, status=500)