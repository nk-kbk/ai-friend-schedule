
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm, UserUpdateForm, ProfileImageForm
from .models import Friendship, User
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q
from notifications_app.models import Notification
from django.utils import timezone
from calendar_app.models import Schedule

@login_required
def profile_view(request):
    if request.method == 'POST':
        image_form = ProfileImageForm(request.POST, request.FILES, instance=request.user)
        if image_form.is_valid():
            image_form.save()
            messages.success(request, 'プロフィール画像を更新しました！')
            return redirect('accounts:profile')
        else:
            messages.error(request, '画像のアップロードに失敗しました。')
    
    image_form = ProfileImageForm(instance=request.user)

    # --- ✨ ここを修正！「今日の予定」を数えるよ！ ---
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timezone.timedelta(days=1)
    
    todays_events_count = Schedule.objects.filter(
        (Q(created_by_user=request.user) | Q(participants=request.user)),
        start_datetime__lt=today_end, # 今日の終わりより前に開始して
        end_datetime__gte=today_start # 今日の始まりより後に終わる予定
    ).distinct().count()

    # 友達の数を数える
    friends_count = Friendship.objects.filter(
        (Q(user_from=request.user) | Q(user_to=request.user)),
        status='accepted'
    ).distinct().count()
    
    context = {
        'image_form': image_form,
        'todays_events_count': todays_events_count, # ✨ 変数名も変更！
        'friends_count': friends_count,
    }
    return render(request, 'accounts/profile.html', context)


# --- 以下、他のビューは変更なしだよ！ ---
def signup_view(request):
    if request.user.is_authenticated:
        return redirect(reverse_lazy('dashboard_top_page'))
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'アカウント登録が完了し、ログインしました！')
            return redirect(reverse_lazy('dashboard_top_page'))
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form, 'page_title': '新規アカウント作成'})

def login_view(request):
    if request.user.is_authenticated:
        return redirect(reverse_lazy('dashboard_top_page'))
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'ようこそ、{username}さん！')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(reverse_lazy('dashboard_top_page'))
            else:
                messages.error(request, 'ユーザー名またはパスワードが無効です。')
        else:
            messages.error(request, '入力内容を確認してください。') 
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form, 'page_title': 'ログイン'})

@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'ログアウトしました。')
        return redirect(reverse_lazy('landing_page'))
    if request.user.is_authenticated:
        return redirect(reverse_lazy('dashboard_top_page'))
    else:
        return redirect(reverse_lazy('landing_page'))

@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'プロフィール情報が更新されました！')
            return redirect(reverse_lazy('accounts:profile'))
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form, 'page_title': 'プロフィール編集'})

@login_required
def account_delete_view(request):
    user_to_delete = request.user
    if request.method == 'POST':
        logout(request)
        user_to_delete.delete()
        messages.success(request, 'アカウントが正常に削除されました。')
        return redirect(reverse_lazy('landing_page'))
    return render(request, 'accounts/account_delete_confirm.html', {'user_to_delete': user_to_delete, 'page_title': 'アカウント削除の確認'})

@login_required
def user_search_view(request):
    query = request.GET.get('q', '')
    users_list = []
    if query:
        users_list = User.objects.filter(
            (Q(username__icontains=query) | Q(email__icontains=query)) & ~Q(id=request.user.id)
        ).distinct()[:20]
    return render(request, 'accounts/user_search_results.html', {'query': query, 'users_list': users_list, 'page_title': '友達を探す'})

@login_required
def send_friend_request_view(request, user_id_to):
    user_to = get_object_or_404(User, id=user_id_to)
    if request.user == user_to:
        messages.error(request, '自分自身に友達申請を送ることはできません。')
        return redirect(request.META.get('HTTP_REFERER', reverse_lazy('accounts:user_search')))
    existing_friendship = Friendship.objects.filter((Q(user_from=request.user, user_to=user_to) | Q(user_from=user_to, user_to=request.user))).first()
    if existing_friendship:
        if existing_friendship.status == Friendship.STATUS_PENDING:
            messages.warning(request, f'{user_to.username}さんとは既に申請中または申請されています。')
        elif existing_friendship.status == Friendship.STATUS_ACCEPTED:
            messages.warning(request, f'{user_to.username}さんとは既に友達です。')
        else: 
            messages.warning(request, f'{user_to.username}さんとの過去の関係により、現在申請できません。')
    else:
        friend_request = Friendship.objects.create(user_from=request.user, user_to=user_to, status=Friendship.STATUS_PENDING)
        messages.success(request, f'{user_to.username}さんに友達申請を送りました。')
        try:
            Notification.objects.create(user=user_to, notification_type='friend_request', message=f'{request.user.username}さんから友達申請が届いています。', related_item_id=friend_request.id, related_item_type='friendship')
        except Exception as e:
            print(f"ERROR: Notification creation failed: {e}")
    return redirect(request.META.get('HTTP_REFERER', reverse_lazy('accounts:user_search')))

@login_required
def friend_requests_received_view(request):
    pending_requests = Friendship.objects.filter(user_to=request.user, status=Friendship.STATUS_PENDING)
    return render(request, 'accounts/friend_requests_received.html', {'pending_requests': pending_requests, 'page_title': '届いた友達申請'})

@login_required
def respond_friend_request_view(request, friendship_id, action):
    friendship = get_object_or_404(Friendship, id=friendship_id, user_to=request.user, status=Friendship.STATUS_PENDING)
    if action == 'accept':
        friendship.status = Friendship.STATUS_ACCEPTED
        friendship.responded_at = timezone.now()
        friendship.save()
        messages.success(request, f'{friendship.user_from.username}さんの友達申請を承認しました。')
        try:
            Notification.objects.create(user=friendship.user_from, notification_type='friend_request_accepted', message=f'{request.user.username}さんがあなたの友達申請を承認しました。', related_item_id=friendship.id, related_item_type='friendship')
        except Exception as e:
            print(f"ERROR: Notification creation failed for acceptance: {e}")
    elif action == 'decline':
        friendship.status = Friendship.STATUS_DECLINED
        friendship.responded_at = timezone.now()
        friendship.save()
        messages.info(request, f'{friendship.user_from.username}さんの友達申請を拒否しました。')
    return redirect(reverse_lazy('accounts:friend_requests_received'))

@login_required
def friend_list_view(request):
    friends_sent = Friendship.objects.filter(user_from=request.user, status=Friendship.STATUS_ACCEPTED)
    friends_received = Friendship.objects.filter(user_to=request.user, status=Friendship.STATUS_ACCEPTED)
    actual_friends = set()
    for fr in friends_sent:
        actual_friends.add(fr.user_to)
    for fr in friends_received:
        actual_friends.add(fr.user_from)
    return render(request, 'accounts/friend_list.html', {'friends_list': list(actual_friends), 'page_title': '友達リスト'})

@login_required
def remove_friend_view(request, friend_id_to_remove):
    friend_to_remove = get_object_or_404(User, id=friend_id_to_remove)
    Friendship.objects.filter((Q(user_from=request.user, user_to=friend_to_remove) | Q(user_from=friend_to_remove, user_to=request.user)) & Q(status=Friendship.STATUS_ACCEPTED)).delete()
    messages.info(request, f'{friend_to_remove.username}さんとの友達関係を解除しました。')
    return redirect(reverse_lazy('accounts:friend_list'))