from django.urls import path
from . import views

urlpatterns = [
    path('settings/', views.settings_dashboard, name="setting_dashboard"),
]
