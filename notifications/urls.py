from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('dashboard/', views.dashboard_notifications,
         name='dashboard_notifications'),
    path('all/', views.all_notifications, name='all_notifications'),
    path('mark-read/<int:pk>/', views.mark_as_read, name='mark_as_read'),
    path('delete/<int:pk>/', views.delete_notfification,
         name='delete_notification'),
    path("mark-all-read/", views.mark_all_notifications_read,
         name="mark_all_notifications_read"),
]
