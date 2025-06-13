# config/urls.py

from django.contrib import admin
# ✨ re_path と serve をインポートするよ！ ✨
from django.urls import path, include, re_path 
from django.views.static import serve

from main_app import views as main_app_views
from django.conf import settings
# from django.conf.urls.static import static # こっちはもう使わないから消してもOK！

urlpatterns = [
    # (ここは今まで通り、変更なしだよ)
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('calendar/', include('calendar_app.urls')),
    path('ai/', include('ai_assistant_app.urls')),
    path('notifications/', include('notifications_app.urls')),
    path('schedule-requests/', include(('schedule_requests_app.urls', 'schedule_requests_app'), namespace='schedule_requests_app')),
    path('', main_app_views.landing_page_view, name='landing_page'),
    path('dashboard/', main_app_views.top_page_view, name='dashboard_top_page'),
]

# --- ✨✨ ここが新しい、本格的な地図だよ！ ✨✨ ---
# 本番環境でも、/media/ から始まるURLへのリクエストが来たら、
# Djangoの serve ビューを使って、MEDIA_ROOTの中のファイルを探しに行くように、
# はっきりと道順を教えてあげるんだ！
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]