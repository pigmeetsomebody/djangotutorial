from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('send-sms-code/', views.SendSmsCodeView.as_view(), name='send-sms-code'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('refresh-token/', views.RefreshTokenView.as_view(), name='refresh-token'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
] 