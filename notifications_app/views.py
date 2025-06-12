# notifications_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.http import HttpResponseForbidden # 権限チェック用
# from django.contrib import messages # 今回は使ってないけど、必要なら

@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'notifications': notifications,
        'page_title': 'お知らせ一覧' # ✨ page_title をコンテキストに追加！ ✨
    }
    return render(request, 'notifications_app/notification_list.html', context)

@login_required
def mark_notification_as_read_view(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    if notification.user != request.user:
        return HttpResponseForbidden("この通知を操作する権限がありません。")
        
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    
    redirect_url = notification.get_absolute_url()
    if redirect_url:
        return redirect(redirect_url)
    return redirect('notifications_app:notification_list')

@login_required
def mark_all_notifications_as_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notifications_app:notification_list')