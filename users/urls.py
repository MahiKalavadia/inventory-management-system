from django.urls import path
from . import views

urlpatterns = [
    path('user/dashboard/', views.user_dashboard,
         name='user_dashboard'),
    path('view-users/', views.view_users, name='view_users'),
    path('users/toggle/<int:user_id>/',
         views.toggle_user_status, name='toggle_user_status'),
    path('add-user/', views.add_user, name='add_user'),
    path('update-user/<int:user_id>/', views.update_user, name='update_user'),
    path('reset-password/<int:user_id>/',
         views.reset_user_password, name='reset_user_password'),
]
