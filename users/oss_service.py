"""
阿里云OSS服务封装
"""
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from django.conf import settings
import alibabacloud_oss_v2 as oss  # 导入阿里云OSS V2 SDK
import oss2
from oss2 import OBJECT_ACL_PUBLIC_READ

logger = logging.getLogger(__name__)


class AlibabaCloudOSSService:
    """阿里云OSS服务类"""
    
    def __init__(self):
        """初始化OSS客户端"""
        try:
            # 配置OSS客户端
            credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
            cfg = oss.config.load_default()
            cfg.credentials_provider = credentials_provider
            cfg.endpoint = getattr(settings, 'OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
            cfg.region = getattr(settings, 'OSS_REGION_ID', 'cn-hangzhou')
            # 初始化OSS客户端
            self.oss_client = oss.Client(cfg)
            self.bucket_name = getattr(settings, 'OSS_BUCKET_NAME', '')
            self.url_prefix = getattr(settings, 'OSS_URL_PREFIX', '')
            # 初始化OSS bucket
            access_key_id = os.environ.get('OSS_ACCESS_KEY_ID')
            access_key_secret = os.environ.get('OSS_ACCESS_KEY_SECRET')
            auth = oss2.auth.Auth(access_key_id, access_key_secret)
            self.oss_bucket = oss2.Bucket(auth, cfg.endpoint, self.bucket_name)
            logger.info("阿里云OSS客户端初始化成功")
            
        except Exception as e:
            logger.error(f"初始化阿里云OSS客户端失败: {str(e)}")
            raise
    
    def generate_object_key(self, filename: str, folder: str = 'uploads') -> str:
        """
        生成对象存储的key
        
        Args:
            filename: 原始文件名
            folder: 存储文件夹
            
        Returns:
            生成的对象key
        """
        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        # 按日期分组
        date_path = datetime.now().strftime('%Y/%m/%d')
        
        # 完整的对象key
        object_key = f"{folder}/{date_path}/{unique_filename}"
        
        return object_key
    
    def upload_file(self, file_content: bytes, filename: str, folder: str = 'uploads') -> Dict[str, Any]:
        """
        上传文件到OSS
        
        Args:
            file_content: 文件内容（字节）
            filename: 原始文件名
            folder: 存储文件夹
            
        Returns:
            包含文件信息的字典
        """
        try:
            # 生成对象key
            object_key = self.generate_object_key(filename, folder)
            logger.info(f"upload to bucket_name: {self.bucket_name}, object_key: {object_key}")
            # 创建上传请求
            # request = oss.PutObjectRequest(
            #     bucket=self.bucket_name,
            #     key=object_key,          # 对象在OSS中的路径/文件名
            #     body=file_content,           # 直接传入二进制内容
            #     # content_type='image/png'        # 可选：指定MIME类型
            # )
            # # 执行上传
            # result = self.oss_client.put_object(request)
            result = self.oss_bucket.put_object(object_key, file_content, headers={'x-oss-object-acl': OBJECT_ACL_PUBLIC_READ})
            logger.info(f"result: {result}")

            if result.status==200:
                logger.info(f"文件上传成功: {result}")
                return {
                    'success': True,
                    'object_key': object_key,
                    'file_url': self.get_file_url(object_key),
                    'original_filename': filename,
                    'size': len(file_content),
                }
            else:
                logger.error(f"文件上传失败: {result}")
                return {
                    'success': False,
                    'error': result.status_code
                }
            
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_file(self, object_key: str) -> Dict[str, Any]:
        """
        删除OSS中的文件
        
        Args:
            object_key: 对象key
            
        Returns:
            删除结果
        """
        try:
            # 创建删除请求
            
            # 执行删除
            result = self.oss_client.delete_object(
                oss.DeleteObjectRequest(
                    bucket=self.bucket_name,
                    key=object_key
                )
            )
            if result.status_code == 200:
                logger.info(f"文件删除成功: {object_key}")
                return {
                    'success': True,
                    'object_key': object_key
                }
            else:
                logger.error(f"文件删除失败: {result}")
                return {
                    'success': False,
                    'error': result.status_code
                }
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_url(self, object_key: str) -> str:
        """
        获取文件的访问URL
        
        Args:
            object_key: 对象key
            
        Returns:
            文件访问URL
        """
        return f"{self.url_prefix}/{object_key}"


# 创建全局OSS服务实例
try:
    oss_service = AlibabaCloudOSSService()
except Exception as e:
    logger.error(f"创建OSS服务实例失败: {str(e)}")
    oss_service = None 