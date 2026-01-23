from django.urls import path
from . import views

urlpatterns = [
    path('purchase/dashboard/', views.purchase_dashboard,
         name='purchase_dashboard'),
]
