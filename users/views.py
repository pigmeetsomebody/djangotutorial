from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import SendSmsCodeSerializer, LoginSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import traceback
import logging
from django.conf import settings
from datetime import datetime
from rest_framework_simplejwt.tokens import RefreshToken

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
                    response = Response({
                        'message': '登录成功',
                        'user': {
                            'phone': result['user'].phone,
                            'id': result['user'].id
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
