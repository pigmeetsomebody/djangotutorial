from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.conf import settings

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('手机号必须填写')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=20, unique=True, verbose_name='手机号')
    openid = models.CharField(max_length=64, blank=True, null=True, unique=True, verbose_name='微信OpenID')
    apple_id = models.CharField(max_length=64, blank=True, null=True, unique=True, verbose_name='苹果ID')
    google_id = models.CharField(max_length=64, blank=True, null=True, unique=True, verbose_name='谷歌ID')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone

    def get_tokens_for_user(self):
        """生成用户的 JWT token"""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

class SmsCode(models.Model):
    phone = models.CharField(max_length=20, verbose_name='手机号')
    code = models.CharField(max_length=settings.SMS_CODE_LENGTH, verbose_name='验证码')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    is_used = models.BooleanField(default=False, verbose_name='是否已使用')

    def __str__(self):
        return f"{self.phone} - {self.code}"

    def is_expired(self):
        """判断验证码是否过期"""
        expire_time = self.created_at + timezone.timedelta(minutes=settings.SMS_CODE_EXPIRE_MINUTES)
        return timezone.now() > expire_time

    class Meta:
        verbose_name = '短信验证码'
        verbose_name_plural = '短信验证码'
        ordering = ['-created_at']
