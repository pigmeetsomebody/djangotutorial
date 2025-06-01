from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('send-code/', views.SendSmsCodeView.as_view(), name='send_code'),
    path('login/', views.LoginView.as_view(), name='login'),
] 