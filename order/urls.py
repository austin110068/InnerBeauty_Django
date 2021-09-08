from django.urls import path
from django.conf.urls import url  

from order import views

urlpatterns = [
    path('checkout/', views.checkout),
    path('checkout_success_sms/', views.checkout_success_sms),
    path('orders/', views.OrdersList.as_view()),  
]
