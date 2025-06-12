from django.contrib import admin
from .models import User, Friendship # UserはDjango標準でも可、Friendshipはカスタム

# UserモデルはDjango標準でadminに登録されているので、カスタマイズする場合に記述
# class CustomUserAdmin(admin.ModelAdmin):
#     list_display = ('username', 'email', 'selected_ai_character_id', 'is_staff', 'date_joined')
#     search_fields = ('username', 'email')
# admin.site.unregister(User) # 標準のUserを解除
# admin.site.register(User, CustomUserAdmin) # カスタムUserAdminで登録

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('user_from', 'user_to', 'status', 'requested_at', 'responded_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('user_from__username', 'user_to__username')