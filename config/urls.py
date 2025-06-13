# config/urls.py の【最終解決版】フルコード！

from django.contrib import admin
from django.urls import path, include
from main_app import views as main_app_views

# メディアファイルを配信するために必要なインポート
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 各アプリのURLをインクルード
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('calendar/', include('calendar_app.urls')),
    path('ai/', include('ai_assistant_app.urls')),
    path('notifications/', include('notifications_app.urls')),
    # schedule_requests_app は名前空間も指定してるから、この書き方だよ！
    path('schedule-requests/', include(('schedule_requests_app.urls', 'schedule_requests_app'), namespace='schedule_requests_app')),
    
    # トップレベルのURLパターン
    path('', main_app_views.landing_page_view, name='landing_page'),
    path('dashboard/', main_app_views.top_page_view, name='dashboard_top_page'),
]

# --- ✨✨ ここが一番大事な修正ポイント！ ✨✨ ---
# if settings.DEBUG: の条件を外して、
# 本番環境(Render)でも /media/ へのアクセスがあった時に、
# MEDIA_ROOT で指定したフォルダの中身を見に行くようにするおまじない！
# これで、アップロードされた音声ファイルが聞こえるようになるはず！
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)