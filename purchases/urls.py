from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.purchase_dashboard, name='purchase_dashboard'),
    path('request/<int:product_id>/', views.create_purchase_request,
         name='create_purchase_request'),
    path('approve/<int:pr_id>/<str:action>/',
         views.approve_purchase_request, name='approve_purchase_request'),
]
