# schedule_requests_app/urls.py
from django.urls import path
from . import views

app_name = 'schedule_requests_app'

urlpatterns = [
    path('<int:request_id>/', views.schedule_request_detail_view, name='schedule_request_detail'),
    path('<int:request_id>/respond/<str:action>/', views.respond_schedule_request_view, name='respond_schedule_request'),
    
    # ✨ ここを追加！AIから友達への申請を作成するためのURLだよ！ ✨
    path('create-request-from-ai/', views.create_schedule_request_from_ai_view, name='create_request_from_ai'),
]