from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date, timedelta
import json
from django.urls import reverse_lazy, reverse
from django.db.models import Q

# models
from calendar_app.models import Schedule
from ai_assistant_app.models import AICharacter

# calendar_app.views から DivCalendar をインポートするよ！
from calendar_app.views import DivCalendar 


@login_required
def top_page_view(request): # ログイン後のダッシュボード
    current_today = timezone.now().date()
    
    try:
        target_year = int(request.GET.get('year', current_today.year))
        target_month = int(request.GET.get('month', current_today.month))
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
    
    schedules_for_js = []
    for s in schedules_for_month_queryset:
        start_dt_local = timezone.localtime(s.start_datetime)
        end_dt_local = timezone.localtime(s.end_datetime)
        schedules_for_js.append({
            'id': s.id,
            'title': s.title,
            'year': start_dt_local.year,
            'month': start_dt_local.month,
            'day': start_dt_local.day,
            'start_time': start_dt_local.strftime('%H:%M'),
            'end_time': end_dt_local.strftime('%H:%M'),
            'location': s.location or "",
            'description': s.description or "",
            'detail_url': reverse('calendar_app:schedule_detail', args=[s.id])
        })

    # ✨ ここで新しい DivCalendar を使うように変更！ is_dashboard=True を渡すよ！✨
    # ダッシュボード用は月曜始まり(firstweekday=0)にしてみる？おしゃれかも！
    cal = DivCalendar(target_year, target_month, schedules_for_month_queryset, firstweekday=0, is_dashboard=True) 
    html_cal = cal.formatmonth()

    # prev/next month の計算
    prev_month_date = (first_day - timedelta(days=1))
    next_month_date = (last_day + timedelta(days=1))
        
    context = {
        'page_title': 'ダッシュボード',
        'current_year': target_year,
        'current_month': target_month,
        'calendar_html': html_cal,
        'schedules_for_month_json': json.dumps(schedules_for_js),
        # ✨ prev/next nav は top_page.html で使うようになったから、ちゃんと渡しておくね！ ✨
        'prev_year_nav': prev_month_date.year,
        'prev_month_nav': prev_month_date.month,
        'next_year_nav': next_month_date.year,
        'next_month_nav': next_month_date.month,
    }
    return render(request, 'main_app/top_page.html', context)


def landing_page_view(request):
    if request.user.is_authenticated:
        return redirect(reverse_lazy('dashboard_top_page'))
    context = {
        'page_title': 'ようこそ！AIフレンドスケジュールへ'
    }
    return render(request, 'main_app/landing_page.html', context)