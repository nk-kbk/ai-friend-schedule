from django.urls import path
from . import views

app_name = 'notifications_app'

urlpatterns = [
    path('', views.notification_list_view, name='notification_list'),
    path('read/<int:notification_id>/', views.mark_notification_as_read_view, name='mark_as_read'),
    path('read/all/', views.mark_all_notifications_as_read_view, name='mark_all_as_read'),
]