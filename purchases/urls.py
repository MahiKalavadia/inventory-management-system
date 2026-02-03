from django.urls import path
from . import views

app_name = "purchases"


urlpatterns = [
    path('purchase-dahsboard/', views.purchase_dashboard,
         name='purchase_dashboard'),
    path('request/create/', views.create_purchase_request,
         name='create_request'),
    path('request/<int:pk>/approve/',
         views.approve_request, name='approve_purchase_request'),
    path('request/<int:pk>/reject/',
         views.reject_request, name='reject_purchase_request'),
    path('order/<int:pk>/status/<str:status>/',
         views.update_order_status, name='update_order_status'),
]
