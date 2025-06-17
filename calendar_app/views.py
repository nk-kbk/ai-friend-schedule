# calendar_app/views.py の完全なコード

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
import calendar as py_calendar
from datetime import date, timedelta, datetime
from django.utils.safestring import mark_safe
from .forms import ScheduleForm # ScheduleForm を使うのでインポート！
from .models import Schedule
from django.urls import reverse_lazy, reverse
import re
import traceback
from django.db.models import Q
from django.contrib import messages
from django.db import transaction
from django.utils.html import escape
import json

# --- DivCalendarクラス (ここは変更なし！) ---
class DivCalendar:
    def __init__(self, year, month, schedules_for_month, firstweekday=6, is_dashboard=False):
        self.year = year
        self.month = month
        self.schedules_by_day = {}
        for schedule in schedules_for_month:
            day_num = timezone.localtime(schedule.start_datetime).day
            if day_num not in self.schedules_by_day:
                self.schedules_by_day[day_num] = []
            self.schedules_by_day[day_num].append(schedule)
        self.firstweekday = firstweekday
        self.is_dashboard = is_dashboard
        py_calendar.setfirstweekday(firstweekday)
        self.month_cal = py_calendar.monthcalendar(year, month)

    def formatmonth(self):
        cal_html = '<div class="grid grid-cols-7 gap-px bg-slate-200 border border-slate-200 rounded-lg overflow-hidden shadow-sm calendar-grid-container">\n'
        day_names_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        ordered_day_names = day_names_en[self.firstweekday:] + day_names_en[:self.firstweekday]
        
        for day_name in ordered_day_names:
            cal_html += f'  <div class="text-center py-3 bg-slate-50 text-xs font-semibold text-slate-600 uppercase tracking-wider">{day_name}</div>\n'

        today = timezone.now().date()
        for week in self.month_cal:
            for day in week:
                if day == 0:
                    cal_html += '  <div class="bg-slate-50/70 min-h-[8rem]"></div>\n'
                else:
                    current_date = date(self.year, self.month, day)
                    schedules_on_day = self.schedules_by_day.get(day, [])
                    css_classes = ["relative p-2 h-32 overflow-hidden transition-colors day-cell"]
                    if not self.is_dashboard:
                        css_classes.append("cursor-pointer")
                    is_today = (current_date == today)
                    if is_today:
                        css_classes.append("bg-blue-100/50 today-cell")
                    else:
                        css_classes.append("bg-white hover:bg-slate-50")
                    cal_html += f'  <div class="{" ".join(css_classes)}" data-year="{self.year}" data-month="{self.month}" data-day="{day}">\n'
                    num_css_classes = ["text-sm"]
                    if is_today:
                        num_css_classes.append("absolute top-1.5 right-1.5 size-7 flex items-center justify-center font-semibold text-white bg-blue-500 rounded-full")
                    else:
                        if current_date.weekday() == 5:
                           num_css_classes.append("text-blue-700")
                        elif current_date.weekday() == 6:
                            num_css_classes.append("text-red-600")
                        else:
                            num_css_classes.append("text-slate-700")
                    cal_html += f'    <span class="{" ".join(num_css_classes)}">{day}</span>\n'
                    if schedules_on_day:
                        if self.is_dashboard:
                            cal_html += '    <div class="absolute bottom-2 right-2 flex flex-wrap-reverse gap-1 justify-end">\n'
                            for _ in schedules_on_day[:4]:
                                 cal_html += '      <div class="h-1.5 w-1.5 rounded-full bg-blue-600 opacity-80"></div>\n'
                            cal_html += '    </div>\n'
                        else:
                            cal_html += '    <div class="mt-4 space-y-1">\n'
                            for schedule in schedules_on_day[:3]:
                                title_text = escape(schedule.title)
                                if len(title_text) > 10:
                                    title_text = title_text[:9] + '…'
                                start_time = timezone.localtime(schedule.start_datetime).strftime('%H:%M')
                                cal_html += f'<a href="{reverse("calendar_app:schedule_detail", args=[schedule.id])}" class="block p-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 truncate" title="{escape(schedule.title)}">'
                                cal_html += f'<span>{start_time}</span> {title_text}'
                                cal_html += '</a>\n'
                            if len(schedules_on_day) > 3:
                                remaining = len(schedules_on_day) - 3
                                cal_html += f'<div class="text-center text-xs text-slate-500 mt-1">他{remaining}件</div>\n'
                            cal_html += '    </div>\n'
                    cal_html += '  </div>\n'
        cal_html += '</div>'
        return mark_safe(cal_html)


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

@login_required
def schedule_new_view(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by_user = request.user
            schedule.save()
            form.save_m2m()
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
        messages.success(request, f'予定「{title}」を削除しました。')
        return redirect(reverse_lazy('calendar_app:monthly_calendar', args=[year, month]))
    return render(request, 'calendar_app/schedule_delete_confirm.html', {'schedule': schedule})


# --- ✨✨ ここからが修正された最終兵器バージョンだよ！ ✨✨ ---
@login_required
@require_POST
def create_personal_schedule_from_ai_view(request):
    try:
        data = json.loads(request.body)
        print(f"--- [AIからの受信データ] ---: {data}")

        # AIからのデータを元に、フォームで使うための辞書データを作成
        form_data = {
            'title': data.get('title'),
            'start_datetime': data.get('start_datetime'),
            'end_datetime': data.get('end_datetime'),
            'location': data.get('location'),
            'description': data.get('description'),
        }
        
        # Djangoのフォーム機能を使って、データが正しいか厳しくチェック！
        form = ScheduleForm(form_data)

        if form.is_valid():
            # データが正しければ、保存処理に進む
            with transaction.atomic():
                schedule = form.save(commit=False)
                schedule.created_by_user = request.user
                schedule.save()
                schedule.participants.add(request.user)

            print(f"--- [成功] 予定をデータベースに保存しました！ ID: {schedule.id} ---")
            return JsonResponse({
                'status': 'success', 
                'message': f"予定「{schedule.title}」をカレンダーに登録しました！"
            })
        else:
            # もしデータに不備があったら、エラーの内容を詳しく返す！
            print(f"--- [エラー] フォームのバリデーションに失敗しました ---: {form.errors.as_json()}")
            error_message = "AIからのデータに不備がありました: " + " ".join([f"{field}: {' '.join(errors)}" for field, errors in form.errors.items()])
            return JsonResponse({'status': 'error', 'message': error_message}, status=400)

    except Exception as e:
        # その他の予期せぬエラーも、ちゃんとログに出す！
        print(f"--- [致命的エラー] 予期せぬエラーが発生しました ---")
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'予定の作成中に予期せぬエラーが発生しました: {e}'}, status=500)