from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('send-sms-code/', views.SendSmsCodeView.as_view(), name='send-sms-code'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('refresh-token/', views.RefreshTokenView.as_view(), name='refresh-token'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('upload-image/', views.ImageUploadView.as_view(), name='upload-image'),
    path('upload-images/', views.BatchImageUploadView.as_view(), name='upload-images'),
    path('upload-binary-image/', views.BinaryImageUploadView.as_view(), name='upload-binary-image'),
    path('upload-raw-binary-image/', views.RawBinaryImageUploadView.as_view(), name='upload-raw-binary-image'),
    path('delete-image/', views.DeleteImageView.as_view(), name='delete-image'),
] 