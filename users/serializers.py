from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SmsCode
import random
from django.conf import settings
import logging
import traceback
from django.utils import timezone
import base64
import io
from PIL import Image

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
                'refresh_token': tokens['refresh'],
                'is_new_user': created  # 添加新用户标识字段
            }
        except Exception as e:
            logger.error(f"创建用户或生成token时发生错误: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise


class UserProfileSerializer(serializers.ModelSerializer):
    """用户资料序列化器"""
    class Meta:
        model = User
        fields = ['nickname', 'avatar', 'bio', 'birthday']
        extra_kwargs = {
            'nickname': {'required': False, 'allow_blank': True},
            'avatar': {'required': False, 'allow_blank': True},
            'bio': {'required': False, 'allow_blank': True, 'max_length': 100},
            'birthday': {'required': False, 'allow_null': True},
        }

    def validate_birthday(self, value):
        """验证生日格式"""
        if value and value > timezone.now().date():
            raise serializers.ValidationError('生日不能是未来日期')
        return value

    def validate_bio(self, value):
        """验证个人简介长度"""
        if value and len(value) > 100:
            raise serializers.ValidationError('个人简介不能超过100字')
        return value


class ImageUploadSerializer(serializers.Serializer):
    """图片上传序列化器"""
    image = serializers.ImageField(required=True)
    folder = serializers.CharField(max_length=50, required=False, default='images')
    
    def validate_image(self, value):
        """验证图片文件"""
        # 检查文件大小（最大5MB）
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError('图片文件大小不能超过5MB')
        
        # 检查文件类型
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError('只支持 JPEG、PNG、GIF、WebP 格式的图片')
        
        return value
    
    def validate_folder(self, value):
        """验证文件夹名称"""
        # 只允许字母、数字、下划线和连字符
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError('文件夹名称只能包含字母、数字、下划线和连字符')
        return value


class BatchImageUploadSerializer(serializers.Serializer):
    """批量图片上传序列化器"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        min_length=1,
        max_length=10,  # 最多上传10张图片
        required=True
    )
    folder = serializers.CharField(max_length=50, required=False, default='images')
    
    def validate_images(self, value):
        """验证图片列表"""
        for image in value:
            # 检查文件大小（最大5MB）
            max_size = 5 * 1024 * 1024  # 5MB
            if image.size > max_size:
                raise serializers.ValidationError(f'图片 {image.name} 文件大小不能超过5MB')
            
            # 检查文件类型
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if image.content_type not in allowed_types:
                raise serializers.ValidationError(f'图片 {image.name} 格式不支持，只支持 JPEG、PNG、GIF、WebP 格式')
        
        return value


class BinaryImageUploadSerializer(serializers.Serializer):
    """二进制图片上传序列化器"""
    image_data = serializers.CharField(required=True, help_text="Base64编码的图片数据或二进制数据")
    filename = serializers.CharField(max_length=255, required=True, help_text="文件名")
    folder = serializers.CharField(max_length=50, required=False, default='images')
    content_type = serializers.CharField(max_length=100, required=False, help_text="MIME类型，如image/jpeg")
    
    def validate_image_data(self, value):
        """验证图片数据"""
        try:
            # 如果是base64编码的数据，先解码
            if value.startswith('data:image'):
                # 处理 data:image/jpeg;base64,... 格式
                header, data = value.split(',', 1)
                image_bytes = base64.b64decode(data)
            elif len(value) % 4 == 0:
                # 尝试作为base64解码
                try:
                    image_bytes = base64.b64decode(value)
                except:
                    # 如果解码失败，假设是原始二进制数据
                    image_bytes = value.encode('latin1') if isinstance(value, str) else value
            else:
                # 假设是原始二进制数据
                image_bytes = value.encode('latin1') if isinstance(value, str) else value
            
            # 验证是否为有效图片
            try:
                img = Image.open(io.BytesIO(image_bytes))
                img.verify()
            except Exception:
                raise serializers.ValidationError('无效的图片数据')
            
            # 检查文件大小（最大5MB）
            max_size = 5 * 1024 * 1024  # 5MB
            if len(image_bytes) > max_size:
                raise serializers.ValidationError('图片数据大小不能超过5MB')
                
            return image_bytes
            
        except Exception as e:
            if isinstance(e, serializers.ValidationError):
                raise e
            raise serializers.ValidationError(f'图片数据格式错误: {str(e)}')
    
    def validate_filename(self, value):
        """验证文件名"""
        import re
        # 检查文件扩展名
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        if not any(value.lower().endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError('文件名必须以 .jpg, .jpeg, .png, .gif, .webp 结尾')
        
        # 检查文件名是否包含非法字符
        if not re.match(r'^[a-zA-Z0-9._-]+$', value):
            raise serializers.ValidationError('文件名只能包含字母、数字、点、下划线和连字符')
        
        return value
    
    def validate_folder(self, value):
        """验证文件夹名称"""
        # 只允许字母、数字、下划线和连字符
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError('文件夹名称只能包含字母、数字、下划线和连字符')
        return value


class RawBinaryImageUploadSerializer(serializers.Serializer):
    """原始二进制图片上传序列化器（用于直接上传二进制数据）"""
    filename = serializers.CharField(max_length=255, required=True, help_text="文件名")
    folder = serializers.CharField(max_length=50, required=False, default='images')
    content_type = serializers.CharField(max_length=100, required=False, help_text="MIME类型")
    
    def validate_filename(self, value):
        """验证文件名"""
        import re
        # 检查文件扩展名
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        if not any(value.lower().endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError('文件名必须以 .jpg, .jpeg, .png, .gif, .webp 结尾')
        
        # 检查文件名是否包含非法字符
        if not re.match(r'^[a-zA-Z0-9._-]+$', value):
            raise serializers.ValidationError('文件名只能包含字母、数字、点、下划线和连字符')
        
        return value
    
    def validate_folder(self, value):
        """验证文件夹名称"""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError('文件夹名称只能包含字母、数字、下划线和连字符')
        return value
