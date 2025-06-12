from django.urls import path
from . import views

app_name = 'ai_assistant_app'

urlpatterns = [
    path('chat/<int:character_id>/', views.ai_chat_view, name='ai_chat'),
    path('chat/<int:character_id>/send/', views.send_message_to_ai_view, name='send_ai_message'),
    path('chat/<int:character_id>/reset/', views.reset_chat_history_view, name='reset_chat_history'),
    path('characters/', views.get_ai_character_list_view, name='get_ai_character_list'), # (おまけ) AIキャラリスト取得
]