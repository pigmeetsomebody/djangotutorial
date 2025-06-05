from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken


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
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name='昵称')
    avatar = models.URLField(max_length=255, blank=True, null=True, verbose_name='头像URL')
    bio = models.CharField(max_length=100, blank=True, null=True, verbose_name='个人简介')
    birthday = models.DateField(blank=True, null=True, verbose_name='生日')
    openid = models.CharField(max_length=64, blank=True, null=True, unique=True, verbose_name='微信OpenID')
    apple_id = models.CharField(max_length=64, blank=True, null=True, unique=True, verbose_name='苹果ID')
    google_id = models.CharField(max_length=64, blank=True, null=True, unique=True, verbose_name='谷歌ID')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(default=timezone.now, verbose_name='更新时间')

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone

    def get_tokens_for_user(self):
        """获取用户的 JWT token"""
        refresh = RefreshToken.for_user(self)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }

    def save(self, *args, **kwargs):
        """重写 save 方法，自动更新 updated_at"""
        if not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'


class SmsCode(models.Model):
    phone = models.CharField(max_length=20, verbose_name='手机号')
    code = models.CharField(max_length=settings.SMS_CODE_LENGTH, verbose_name='验证码')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    is_used = models.BooleanField(default=False, verbose_name='是否已使用')
    updated_at = models.DateTimeField(default=timezone.now, verbose_name='更新时间')

    def __str__(self):
        return f"{self.phone} - {self.code}"

    def is_expired(self):
        """检查验证码是否过期"""
        expire_minutes = getattr(settings, 'SMS_CODE_EXPIRE_MINUTES', 5)
        return timezone.now() > self.created_at + timedelta(minutes=expire_minutes)

    def save(self, *args, **kwargs):
        """重写 save 方法，自动更新 updated_at"""
        if not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = '短信验证码'
        verbose_name_plural = '短信验证码'
        ordering = ['-created_at']
