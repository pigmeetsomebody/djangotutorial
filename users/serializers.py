from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SmsCode
import random
from django.conf import settings
import logging
import traceback

logger = logging.getLogger(__name__)

User = get_user_model()

class SendSmsCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, required=True)
    is_test = serializers.BooleanField(default=False, required=False)  # 添加测试模式标志

    def validate_phone(self, value):
        """验证手机号格式"""
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError("请输入正确的手机号")
        return value

    def create(self, validated_data):
        """生成并保存验证码"""
        phone = validated_data['phone']
        is_test = validated_data.get('is_test', False)
        
        # 测试模式下使用固定验证码
        if is_test:
            code = '123456'
        else:
            # 生成6位随机验证码
            code = ''.join(random.choices('0123456789', k=settings.SMS_CODE_LENGTH))
        
        # 保存验证码
        SmsCode.objects.create(phone=phone, code=code)
        
        # 非测试模式下才发送短信
        if not is_test:
            # TODO: 调用短信服务发送验证码
            pass
            
        return {'phone': phone, 'code': code}

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, required=True)
    code = serializers.CharField(max_length=6, required=True)

    def validate_phone(self, value):
        """验证手机号格式"""
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError("请输入正确的手机号")
        return value

    def validate(self, data):
        """验证验证码"""
        phone = data['phone']
        code = data['code']
        
        logger.info(f"开始验证登录请求 - 手机号: {phone}")
        
        # 查找最新的验证码记录
        try:
            # 先查看所有匹配的记录
            all_codes = SmsCode.objects.filter(
                phone=phone,
                code=code,
                is_used=False
            ).order_by('-created_at')
            logger.info(f"找到 {all_codes.count()} 条匹配的记录")
            for sms in all_codes:
                logger.info(f"记录ID: {sms.id}, 手机号: {sms.phone}, 验证码: {sms.code}, 创建时间: {sms.created_at}, 是否使用: {sms.is_used}")
            
            sms_code = all_codes.latest('created_at')
            logger.info(f"使用最新记录: ID={sms_code.id}")
        except SmsCode.DoesNotExist:
            logger.warning(f"未找到匹配的验证码记录 - 手机号: {phone}, 验证码: {code}")
            raise serializers.ValidationError({"code": "验证码错误"})
        
        # 验证码是否过期
        if sms_code.is_expired():
            logger.warning(f"验证码已过期 - 手机号: {phone}, 验证码: {code}")
            raise serializers.ValidationError({"code": "验证码已过期"})
        
        # 将验证码对象添加到验证数据中
        data['sms_code'] = sms_code
        return data

    def create(self, validated_data):
        """处理登录逻辑"""
        try:
            phone = validated_data['phone']
            sms_code = validated_data['sms_code']
            
            # 标记验证码已使用
            sms_code.is_used = True
            sms_code.save()
            logger.info(f"验证码已标记为使用 - ID: {sms_code.id}")
            
            # 获取或创建用户
            user, created = User.objects.get_or_create(phone=phone)
            logger.info(f"用户{'创建' if created else '获取'}成功 - ID: {user.id}")
            
            # 生成 token
            tokens = user.get_tokens_for_user()
            logger.info(f"Token生成成功 - 用户ID: {user.id}")
            
            return {
                'user': user,
                'access_token': tokens['access'],
                'refresh_token': tokens['refresh']
            }
        except Exception as e:
            logger.error(f"创建用户或生成token时发生错误: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise 