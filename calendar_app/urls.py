# calendar_app/urls.py
from django.urls import path
from . import views

app_name = 'calendar_app'

urlpatterns = [
    path('', views.monthly_calendar_view, name='monthly_calendar_today'),
    path('<int:year>/<int:month>/', views.monthly_calendar_view, name='monthly_calendar'),
    path('schedule/new/', views.schedule_new_view, name='schedule_new'),
    path('schedule/<int:schedule_id>/', views.schedule_detail_view, name='schedule_detail'),
    path('schedule/<int:schedule_id>/edit/', views.schedule_edit_view, name='schedule_edit'),
    path('schedule/<int:schedule_id>/delete/', views.schedule_delete_view, name='schedule_delete'),
    
    # ✨ ここを追加！AIから自分だけの予定を作成するためのURLだよ！ ✨
    path('schedule/create-from-ai/', views.create_personal_schedule_from_ai_view, name='create_personal_schedule_from_ai'),
]