from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import parsers
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .serializers import SendSmsCodeSerializer, LoginSerializer, UserProfileSerializer, ImageUploadSerializer, BatchImageUploadSerializer, BinaryImageUploadSerializer, RawBinaryImageUploadSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import traceback
import logging
from django.conf import settings
from datetime import datetime
from rest_framework_simplejwt.tokens import RefreshToken
from .oss_service import oss_service

logger = logging.getLogger(__name__)

# Create your views here.

class SendSmsCodeView(APIView):
    """发送验证码视图"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="发送手机验证码",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone'],
            properties={
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='手机号'),
                'is_test': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否为测试模式（测试模式下验证码固定为123456）'),
            },
        ),
        responses={
            200: openapi.Response(
                description="验证码发送成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'phone': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "请求参数错误",
        },
    )
    def post(self, request):
        serializer = SendSmsCodeSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                'message': '验证码已发送',
                'phone': result['phone']
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def set_auth_cookies(response, access_token, refresh_token):
    """设置认证 cookie"""
    # 设置 access token cookie
    response.set_cookie(
        settings.SIMPLE_JWT['AUTH_COOKIE'],
        access_token,
        expires=datetime.now() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        domain=settings.SIMPLE_JWT['AUTH_COOKIE_DOMAIN']
    )
    
    # 设置 refresh token cookie
    response.set_cookie(
        settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        refresh_token,
        expires=datetime.now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        domain=settings.SIMPLE_JWT['AUTH_COOKIE_DOMAIN']
    )
    
    return response

class LoginView(APIView):
    """验证码登录视图"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="使用手机验证码登录",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone', 'code'],
            properties={
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='手机号'),
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='验证码'),
            },
        ),
        responses={
            200: openapi.Response(
                description="登录成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'phone': openapi.Schema(type=openapi.TYPE_STRING),
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            },
                        ),
                        'token_info': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='访问令牌'),
                                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description='刷新令牌'),
                                'expires_in': openapi.Schema(type=openapi.TYPE_INTEGER, description='过期时间戳'),
                            },
                        ),
                    },
                ),
            ),
            400: "验证码错误或已过期",
        },
    )
    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                try:
                    result = serializer.save()
                    # 获取token的过期时间
                    from rest_framework_simplejwt.tokens import AccessToken
                    access_token = AccessToken(result['access_token'])
                    expires_in = access_token.current_time + access_token.lifetime
                    
                    response = Response({
                        'message': '登录成功',
                        'user': {
                            'phone': result['user'].phone,
                            'id': result['user'].id
                        },
                        'token_info': {
                            'access_token': result['access_token'],
                            'refresh_token': result['refresh_token'],
                            'expires_in': int(expires_in.timestamp())
                        }
                    })
                    
                    # 设置认证 cookie
                    response = set_auth_cookies(
                        response,
                        result['access_token'],
                        result['refresh_token']
                    )
                    
                    return response
                except Exception as e:
                    logger.error(f"登录处理时发生错误: {str(e)}")
                    logger.error(f"错误详情: {traceback.format_exc()}")
                    return Response({
                        'message': '登录处理失败',
                        'error': str(e)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"登录请求处理时发生错误: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return Response({
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """登出视图"""
        response = Response({'message': '登出成功'})
        
        # 清除认证 cookie
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        
        return response

class RefreshTokenView(APIView):
    """刷新 token 视图"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="刷新访问令牌",
        responses={
            200: openapi.Response(
                description="刷新成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            401: "刷新令牌无效或已过期",
        },
    )
    def post(self, request):
        try:
            # 从 cookie 中获取 refresh token
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
            if not refresh_token:
                return Response({
                    'message': '刷新令牌不存在'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # 使用 refresh token 获取新的 access token
            try:
                refresh = RefreshToken(refresh_token)
                access_token = str(refresh.access_token)
                
                # 如果需要刷新 refresh token
                if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
                    refresh_token = str(refresh)
                
                response = Response({
                    'message': '刷新成功'
                })
                
                # 设置新的 cookie
                response = set_auth_cookies(
                    response,
                    access_token,
                    refresh_token
                )
                
                return response
                
            except Exception as e:
                logger.error(f"刷新令牌时发生错误: {str(e)}")
                return Response({
                    'message': '刷新令牌无效或已过期'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            logger.error(f"刷新令牌请求处理时发生错误: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return Response({
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProfileView(APIView):
    """用户资料视图"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="获取用户资料",
        responses={
            200: UserProfileSerializer,
            401: "未认证或token已过期",
        },
    )
    def get(self, request):
        """获取用户资料"""
        try:
            serializer = UserProfileSerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"获取用户资料时发生错误: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return Response({
                'message': '获取用户资料失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="使用POST方法更新用户资料",
        request_body=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            400: "请求参数错误",
            401: "未认证或token已过期",
        },
    )
    def post(self, request):
        """使用POST方法更新用户资料"""
        try:
            serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': '更新成功',
                    'data': serializer.data
                })
            return Response({
                'message': '更新失败',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"更新用户资料时发生错误: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return Response({
                'message': '更新用户资料失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ImageUploadView(APIView):
    """图片上传视图"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="上传图片到阿里云OSS",
        # manual_parameters=[
        #     openapi.Parameter(
        #         'image',
        #         openapi.IN_FORM,
        #         description="图片文件",
        #         type=openapi.TYPE_FILE,
        #         required=True
        #     ),
        #     openapi.Parameter(
        #         'folder',
        #         openapi.IN_FORM,
        #         description="存储文件夹名称（可选，默认为images）",
        #         type=openapi.TYPE_STRING,
        #         required=False
        #     ),
        # ],
        request_body=ImageUploadSerializer,
        responses={
            200: ImageUploadSerializer,
            400: "请求参数错误",
            401: "未认证或token已过期",
            500: "服务器内部错误",
        },
    )
    def post(self, request):
        """上传单张图片"""
        try:
            # 检查OSS服务是否可用
            if not oss_service:
                return Response({
                    'message': 'OSS服务未初始化',
                    'error': '请检查阿里云配置'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 验证请求数据
            serializer = ImageUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'message': '参数验证失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取图片文件和文件夹
            image = serializer.validated_data['image']
            folder = serializer.validated_data.get('folder', 'images')

            # 读取文件内容
            file_content = image.read()

            # 上传到OSS
            result = oss_service.upload_file(
                file_content=file_content,
                filename=image.name,
                folder=folder
            )

            if result.get('success'):
                return Response({
                    'message': '图片上传成功',
                    'data': {
                        'file_url': result['file_url'],
                        'object_key': result['object_key'],
                        'original_filename': result['original_filename'],
                        'size': result['size'],
                    }
                })
            else:
                return Response({
                    'message': '图片上传失败',
                    'error': result.get('error', '未知错误')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"图片上传时发生错误: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return Response({
                'message': '图片上传失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BatchImageUploadView(APIView):
    """批量图片上传视图"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="批量上传图片到阿里云OSS",
        # manual_parameters=[
        #     openapi.Parameter(
        #         'images',
        #         openapi.IN_FORM,
        #         description="图片文件列表（最多10张）",
        #         type=openapi.TYPE_ARRAY,
        #         items=openapi.Items(type=openapi.TYPE_FILE),
        #         required=True
        #     ),
        #     openapi.Parameter(
        #         'folder',
        #         openapi.IN_FORM,
        #         description="存储文件夹名称（可选，默认为images）",
        #         type=openapi.TYPE_STRING,
        #         required=False
        #     ),
        # ],
        request_body=BatchImageUploadSerializer,
        responses={
            200: BatchImageUploadSerializer,
            400: "请求参数错误",
            401: "未认证或token已过期",
            500: "服务器内部错误",
        },
    )
    def post(self, request):
        """批量上传图片"""
        try:
            # 检查OSS服务是否可用
            if not oss_service:
                return Response({
                    'message': 'OSS服务未初始化',
                    'error': '请检查阿里云配置'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 验证请求数据
            serializer = BatchImageUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'message': '参数验证失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取图片文件列表和文件夹
            images = serializer.validated_data['images']
            folder = serializer.validated_data.get('folder', 'images')

            # 批量上传
            results = []
            success_count = 0
            failed_count = 0

            for image in images:
                try:
                    # 读取文件内容
                    file_content = image.read()

                    # 上传到OSS
                    result = oss_service.upload_file(
                        file_content=file_content,
                        filename=image.name,
                        folder=folder
                    )

                    if result.get('success'):
                        success_count += 1
                        results.append({
                            'success': True,
                            'file_url': result['file_url'],
                            'object_key': result['object_key'],
                            'original_filename': result['original_filename'],
                            'size': result['size'],
                        })
                    else:
                        failed_count += 1
                        results.append({
                            'success': False,
                            'original_filename': image.name,
                            'error': result.get('error', '上传失败')
                        })

                except Exception as e:
                    failed_count += 1
                    results.append({
                        'success': False,
                        'original_filename': image.name,
                        'error': str(e)
                    })

            return Response({
                'message': f'批量上传完成，成功{success_count}张，失败{failed_count}张',
                'data': {
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'results': results
                }
            })

        except Exception as e:
            logger.error(f"批量图片上传时发生错误: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return Response({
                'message': '批量图片上传失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteImageView(APIView):
    """删除图片视图"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="删除OSS中的图片",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['object_key'],
            properties={
                'object_key': openapi.Schema(type=openapi.TYPE_STRING, description='OSS对象键'),
            },
        ),
        responses={
            200: openapi.Response(
                description="删除成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "请求参数错误",
            401: "未认证或token已过期",
            500: "服务器内部错误",
        },
    )
    def delete(self, request):
        """删除图片"""
        try:
            # 检查OSS服务是否可用
            if not oss_service:
                return Response({
                    'message': 'OSS服务未初始化',
                    'error': '请检查阿里云配置'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 获取对象键
            object_key = request.data.get('object_key')
            if not object_key:
                return Response({
                    'message': '缺少必要参数',
                    'error': 'object_key 参数不能为空'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 删除文件
            result = oss_service.delete_file(object_key)

            if result.get('success'):
                return Response({
                    'message': '图片删除成功'
                })
            else:
                return Response({
                    'message': '图片删除失败',
                    'error': result.get('error', '未知错误')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"删除图片时发生错误: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return Response({
                'message': '删除图片失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BinaryImageUploadView(APIView):
    """二进制图片上传视图（支持Base64和原始二进制数据）"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="上传Base64编码的图片数据到阿里云OSS",
        request_body=BinaryImageUploadSerializer,
        responses={
            200: BinaryImageUploadSerializer,
            400: "请求参数错误",
            401: "未认证或token已过期", 
            500: "服务器内部错误",
        },
    )
    def post(self, request):
        """上传Base64编码的图片数据"""
        try:
            # 检查OSS服务是否可用
            if not oss_service:
                return Response({
                    'message': 'OSS服务未初始化',
                    'error': '请检查阿里云配置'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 验证请求数据
            serializer = BinaryImageUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'message': '参数验证失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取验证后的数据
            image_bytes = serializer.validated_data['image_data']


            filename = serializer.validated_data['filename']
            folder = serializer.validated_data.get('folder', 'images')

            # 上传到OSS
            result = oss_service.upload_file(
                file_content=image_bytes,
                filename=filename,
                folder=folder
            )

            if result.get('success'):
                return Response({
                    'message': '图片上传成功',
                    'data': {
                        'file_url': result['file_url'],
                        'object_key': result['object_key'],
                        'original_filename': result['original_filename'],
                        'size': result['size'],
                    }
                })
            else:
                return Response({
                    'message': '图片上传失败',
                    'error': result.get('error', '未知错误')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"二进制图片上传时发生错误: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return Response({
                'message': '图片上传失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RawBinaryImageUploadView(APIView):
    """原始二进制图片上传视图（直接接收二进制数据）"""
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.FileUploadParser]

    @swagger_auto_schema(
        operation_description="直接上传原始二进制图片数据到阿里云OSS",
        request_body=RawBinaryImageUploadSerializer,
        responses={
            200: RawBinaryImageUploadSerializer,
            400: "请求参数错误",
            401: "未认证或token已过期",
            500: "服务器内部错误",
        },
    )
    def post(self, request):
        """上传原始二进制图片数据"""
        try:
            # 检查OSS服务是否可用
            if not oss_service:
                return Response({
                    'message': 'OSS服务未初始化',
                    'error': '请检查阿里云配置'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 获取请求体中的二进制数据
            if hasattr(request, 'FILES') and request.FILES:
                # 如果是multipart/form-data格式
                image_data = None
                for file_obj in request.FILES.values():
                    image_data = file_obj.read()
                    break
                
                # 获取表单参数
                filename = request.POST.get('filename')
                folder = request.POST.get('folder', 'images')
                content_type = request.POST.get('content_type')
                
            elif hasattr(request, 'body') and request.body:
                # 如果是原始二进制数据
                image_data = request.body
                
                # 从查询参数或头部获取文件名
                filename = request.GET.get('filename') or request.META.get('HTTP_X_FILENAME')
                folder = request.GET.get('folder', 'images')
                content_type = request.content_type
                
            else:
                return Response({
                    'message': '未找到图片数据',
                    'error': '请在请求体中提供图片的二进制数据'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证参数
            if not filename:
                return Response({
                    'message': '缺少必要参数',
                    'error': 'filename 参数不能为空'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 使用序列化器验证参数
            serializer = RawBinaryImageUploadSerializer(data={
                'filename': filename,
                'folder': folder,
                'content_type': content_type or 'application/octet-stream'
            })
            
            if not serializer.is_valid():
                return Response({
                    'message': '参数验证失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证图片数据大小
            max_size = 5 * 1024 * 1024  # 5MB
            if len(image_data) > max_size:
                return Response({
                    'message': '图片数据大小不能超过5MB'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证是否为有效图片（可选）
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_data))
                img.verify()
            except Exception:
                return Response({
                    'message': '无效的图片数据'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 上传到OSS
            result = oss_service.upload_file(
                file_content=image_data,
                filename=filename,
                folder=folder
            )

            if result.get('success'):
                return Response({
                    'message': '图片上传成功',
                    'data': {
                        'file_url': result['file_url'],
                        'object_key': result['object_key'],
                        'original_filename': result['original_filename'],
                        'size': result['size'],
                    }
                })
            else:
                return Response({
                    'message': '图片上传失败',
                    'error': result.get('error', '未知错误')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"原始二进制图片上传时发生错误: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return Response({
                'message': '图片上传失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

