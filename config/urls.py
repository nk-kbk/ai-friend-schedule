# config/urls.py の完全なコード

from django.contrib import admin
from django.urls import path, include
from main_app import views as main_app_views

# --- ✨ ここが追加された部分！ ---
from django.conf import settings
from django.conf.urls.static import static
# --- ✨ 追加ここまで！ ---

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('calendar/', include('calendar_app.urls')),
    path('ai/', include('ai_assistant_app.urls')),
    path('notifications/', include('notifications_app.urls')),
    path('schedule-requests/', include(('schedule_requests_app.urls', 'schedule_requests_app'), namespace='schedule_requests_app')),
    
    path('', main_app_views.landing_page_view, name='landing_page'),
    path('dashboard/', main_app_views.top_page_view, name='dashboard_top_page'),
]

# --- ✨ ここが追加された部分！ ---
# 開発環境（DEBUG=Trueの時）にメディアファイル（アップロードされた画像など）を配信するための設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# --- ✨ 追加ここまで！ ---