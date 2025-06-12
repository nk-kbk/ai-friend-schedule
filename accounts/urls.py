from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/delete/', views.account_delete_view, name='account_delete'),
    
    path('search/', views.user_search_view, name='user_search'),
    path('friend-request/send/<int:user_id_to>/', views.send_friend_request_view, name='send_friend_request'),
    path('friend-request/received/', views.friend_requests_received_view, name='friend_requests_received'),
    path('friend-request/respond/<int:friendship_id>/<str:action>/', views.respond_friend_request_view, name='respond_friend_request'),
    path('friends/', views.friend_list_view, name='friend_list'),
    path('friend/remove/<int:friend_id_to_remove>/', views.remove_friend_view, name='remove_friend'),
]