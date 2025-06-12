# calendar_app/views.py の修正後コード

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
import calendar as py_calendar
from datetime import date, timedelta, datetime
from django.utils.safestring import mark_safe
from .forms import ScheduleForm
from .models import Schedule
from django.urls import reverse_lazy, reverse
import re
import traceback
from django.db.models import Q
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST
import json
from django.utils import timezone
from datetime import datetime
import traceback
from django.http import JsonResponse, Http404 
from django.utils.html import escape # ✨ HTMLエスケープのために追加するよ！

# --- ✨✨ ここからが新しいDivCalendarクラスだよ！ ✨✨ ---
class DivCalendar:
    """
    月間カレンダーを<div>で生成するクラス。
    is_dashboardフラグで、ダッシュボード用と詳細ページ用の表示を切り替えるよ！
    """
    def __init__(self, year, month, schedules_for_month, firstweekday=6, is_dashboard=False):
        self.year = year
        self.month = month
        self.schedules_by_day = {}
        for schedule in schedules_for_month:
            # タイムゾーンを考慮して、ローカル時間の日付を取得
            day_num = timezone.localtime(schedule.start_datetime).day
            if day_num not in self.schedules_by_day:
                self.schedules_by_day[day_num] = []
            self.schedules_by_day[day_num].append(schedule)
            
        self.firstweekday = firstweekday
        self.is_dashboard = is_dashboard # ダッシュボード用かどうかのフラグ
        py_calendar.setfirstweekday(firstweekday) # 週の始まりを設定
        self.month_cal = py_calendar.monthcalendar(year, month)

    def formatmonth(self):
        cal_html = '<div class="grid grid-cols-7 gap-px bg-slate-200 border border-slate-200 rounded-lg overflow-hidden shadow-sm calendar-grid-container">\n'
        
        # 曜日のヘッダー（英語）
        day_names_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        # 週の始まりに合わせて並び替え
        ordered_day_names = day_names_en[self.firstweekday:] + day_names_en[:self.firstweekday]
        
        for day_name in ordered_day_names:
            cal_html += f'  <div class="text-center py-3 bg-slate-50 text-xs font-semibold text-slate-600 uppercase tracking-wider">{day_name}</div>\n'

        today = timezone.now().date()
        for week in self.month_cal:
            for day in week:
                if day == 0:
                    # 月の範囲外の日
                    cal_html += '  <div class="bg-slate-50/70 min-h-[8rem]"></div>\n'
                else:
                    current_date = date(self.year, self.month, day)
                    schedules_on_day = self.schedules_by_day.get(day, [])
                    
                    css_classes = ["relative p-2 h-32 overflow-hidden transition-colors day-cell"]
                    # 詳細ページではクリックでモーダルを出すので cursor-pointer をつける
                    if not self.is_dashboard:
                        css_classes.append("cursor-pointer")

                    is_today = (current_date == today)
                    if is_today:
                        css_classes.append("bg-blue-100/50 today-cell") # 今日のマスのスタイル
                    else:
                        css_classes.append("bg-white hover:bg-slate-50")

                    cal_html += f'  <div class="{" ".join(css_classes)}" data-year="{self.year}" data-month="{self.month}" data-day="{day}">\n'
                    
                    # 日付の数字部分のスタイル
                    num_css_classes = ["text-sm"]
                    if is_today:
                        num_css_classes.append("absolute top-1.5 right-1.5 size-7 flex items-center justify-center font-semibold text-white bg-blue-500 rounded-full")
                    else:
                        if current_date.weekday() == 5: # 土曜日
                           num_css_classes.append("text-blue-700")
                        elif current_date.weekday() == 6: # 日曜日
                            num_css_classes.append("text-red-600")
                        else:
                            num_css_classes.append("text-slate-700")

                    cal_html += f'    <span class="{" ".join(num_css_classes)}">{day}</span>\n'
                    
                    # 予定表示部分
                    if schedules_on_day:
                        if self.is_dashboard:
                            # --- ダッシュボード用の表示（小さな点） ---
                            cal_html += '    <div class="absolute bottom-2 right-2 flex flex-wrap-reverse gap-1 justify-end">\n'
                            for _ in schedules_on_day[:4]: # 最大4つまで
                                 cal_html += '      <div class="h-1.5 w-1.5 rounded-full bg-blue-600 opacity-80"></div>\n'
                            cal_html += '    </div>\n'
                        else:
                            # --- カレンダー詳細ページ用の表示（帯状） ---
                            cal_html += '    <div class="mt-4 space-y-1">\n'
                            for schedule in schedules_on_day[:3]: # 最大3つまで
                                # タイトルを安全にエスケープして、長すぎる場合は省略
                                title_text = escape(schedule.title)
                                if len(title_text) > 10:
                                    title_text = title_text[:9] + '…'
                                start_time = timezone.localtime(schedule.start_datetime).strftime('%H:%M')
                                cal_html += f'<a href="{reverse("calendar_app:schedule_detail", args=[schedule.id])}" class="block p-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 truncate" title="{escape(schedule.title)}">'
                                cal_html += f'<span>{start_time}</span> {title_text}'
                                cal_html += '</a>\n'

                            # 4件以上ある場合は「他〇件」と表示
                            if len(schedules_on_day) > 3:
                                remaining = len(schedules_on_day) - 3
                                cal_html += f'<div class="text-center text-xs text-slate-500 mt-1">他{remaining}件</div>\n'

                            cal_html += '    </div>\n'

                    cal_html += '  </div>\n'

        cal_html += '</div>'
        return mark_safe(cal_html)

# --- ✨✨ DivCalendarクラスはここまで！ ✨✨ ---


@login_required
def monthly_calendar_view(request, year=None, month=None):
    current_today = timezone.now().date()
    try:
        target_year = int(request.GET.get('year', year if year else current_today.year))
        target_month = int(request.GET.get('month', month if month else current_today.month))
        if not (1 <= target_month <= 12):
            raise ValueError
    except (ValueError, TypeError):
        target_year = current_today.year
        target_month = current_today.month
    
    first_day = date(target_year, target_month, 1)
    if target_month == 12:
        last_day = date(target_year, 12, 31)
    else:
        last_day = date(target_year, target_month + 1, 1) - timedelta(days=1)
    
    schedules_for_month_queryset = Schedule.objects.filter(
        (Q(created_by_user=request.user) | Q(participants=request.user)),
        start_datetime__date__gte=first_day,
        start_datetime__date__lte=last_day
    ).distinct().order_by('start_datetime')

    schedules_for_js = [{
        'id': s.id, 'title': s.title,
        'year': timezone.localtime(s.start_datetime).year,
        'month': timezone.localtime(s.start_datetime).month,
        'day': timezone.localtime(s.start_datetime).day,
        'start_time': timezone.localtime(s.start_datetime).strftime('%H:%M'),
        'end_time': timezone.localtime(s.end_datetime).strftime('%H:%M'),
        'location': s.location or "",
        'detail_url': reverse('calendar_app:schedule_detail', args=[s.id])
    } for s in schedules_for_month_queryset]

    # --- ✨ 修正ポイント！ is_dashboard=False を渡して「詳細カレンダー用」の表示にするよ！ ---
    cal = DivCalendar(target_year, target_month, schedules_for_month_queryset, firstweekday=6, is_dashboard=False) 
    html_cal = cal.formatmonth()

    prev_month_date = (first_day - timedelta(days=1))
    next_month_date = (last_day + timedelta(days=1))

    context = {
        'calendar_html': html_cal,
        'current_year': target_year,
        'current_month': target_month,
        'prev_year_nav': prev_month_date.year,
        'prev_month_nav': prev_month_date.month,
        'next_year_nav': next_month_date.year,
        'next_month_nav': next_month_date.month,
        'schedules_for_month_json': json.dumps(schedules_for_js),
    }
    return render(request, 'calendar_app/monthly_calendar.html', context)

# 
# --- 他のビュー (schedule_new_view, schedule_detail_viewなど) は変更なしでOKだよ！ ---
# 
@login_required
def schedule_new_view(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by_user = request.user
            schedule.save()
            form.save_m2m()
            # ここで messages を使うよ！
            messages.success(request, f'予定「{schedule.title}」を登録しました。')
            return redirect(reverse_lazy('calendar_app:monthly_calendar', args=[schedule.start_datetime.year, schedule.start_datetime.month]))
    else:
        now = timezone.now()
        initial_start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        initial_end = initial_start + timedelta(hours=1)
        form = ScheduleForm(initial={
            'start_datetime': initial_start,
            'end_datetime': initial_end,
        })
    return render(request, 'calendar_app/schedule_form.html', {'form': form})

@login_required
def schedule_detail_view(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    if not (schedule.created_by_user == request.user or request.user in schedule.participants.all()):
        # ここで messages を使うよ！
        messages.error(request, "この予定の詳細を見る権限がありません。")
        return redirect(reverse_lazy('dashboard_top_page'))
    return render(request, 'calendar_app/schedule_detail.html', {'schedule': schedule})

@login_required
def schedule_edit_view(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, created_by_user=request.user)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            # ここで messages を使うよ！
            messages.success(request, f'予定「{schedule.title}」を更新しました。')
            return redirect(reverse_lazy('calendar_app:schedule_detail', args=[schedule.id]))
    else:
        form = ScheduleForm(instance=schedule)
    return render(request, 'calendar_app/schedule_form.html', {'form': form})

@login_required
def schedule_delete_view(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, created_by_user=request.user)
    if request.method == 'POST':
        title = schedule.title
        year, month = schedule.start_datetime.year, schedule.start_datetime.month
        schedule.delete()
        # ここで messages を使うよ！
        messages.success(request, f'予定「{title}」を削除しました。')
        return redirect(reverse_lazy('calendar_app:monthly_calendar', args=[year, month]))
    return render(request, 'calendar_app/schedule_delete_confirm.html', {'schedule': schedule})

@login_required
@require_POST
def create_personal_schedule_from_ai_view(request):
    try:
        data = json.loads(request.body)

        # 必須項目のチェック
        required_fields = ['title', 'start_datetime', 'end_datetime']
        if not all(field in data for field in required_fields):
            return JsonResponse({'status': 'error', 'message': '必須項目が不足しています。'}, status=400)
        
        # 日時のパースとバリデーション
        start_dt_naive = datetime.strptime(data['start_datetime'], '%Y-%m-%d %H:%M')
        end_dt_naive = datetime.strptime(data['end_datetime'], '%Y-%m-%d %H:%M')

        if end_dt_naive <= start_dt_naive:
            return JsonResponse({'status': 'error', 'message': '終了日時は開始日時より後にする必要があります。'}, status=400)

        start_dt_aware = timezone.make_aware(start_dt_naive)
        end_dt_aware = timezone.make_aware(end_dt_naive)

        # 安全なトランザクション内でスケジュールを作成
        with transaction.atomic():
            new_schedule = Schedule.objects.create(
                created_by_user=request.user,
                title=data['title'],
                start_datetime=start_dt_aware,
                end_datetime=end_dt_aware,
                location=data.get('location'),
                description=data.get('description')
            )
            # 自分だけの予定なので、participantsには自分だけ追加する
            new_schedule.participants.add(request.user)

        return JsonResponse({
            'status': 'success', 
            'message': f"予定「{new_schedule.title}」をカレンダーに登録しました！"
        })

    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': '日時の形式が正しくありません。'}, status=400)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': '予定の作成中にエラーが発生しました。'}, status=500)