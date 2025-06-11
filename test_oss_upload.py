#!/usr/bin/env python
"""
阿里云OSS上传功能测试脚本
"""
import os
import sys
import django

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangotutorial.settings')
django.setup()

from users.oss_service import oss_service

def test_oss_credentials():
    """测试OSS凭据是否正确配置"""
    print("=== 测试OSS凭据配置 ===")
    
    if not oss_service:
        print("❌ OSS服务初始化失败")
        return False
    
    print("✅ OSS服务初始化成功")
    print(f"Bucket名称: {oss_service.bucket_name}")
    print(f"URL前缀: {oss_service.url_prefix}")
    
    return True

def test_file_upload():
    """测试文件上传功能"""
    print("\n=== 测试文件上传功能 ===")
    
    if not oss_service:
        print("❌ OSS服务未初始化")
        return False
    
    # 创建一个测试图片内容（模拟PNG文件头）
    test_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    
    try:
        # 测试上传
        result = oss_service.upload_file(
            file_content=test_content,
            filename='test_image.png',
            folder='test'
        )
        
        if result.get('success'):
            print("✅ 文件上传成功")
            print(f"文件URL: {result['file_url']}")
            print(f"对象键: {result['object_key']}")
            print(f"文件大小: {result['size']} 字节")
            
            # 测试删除
            print("\n=== 测试文件删除功能 ===")
            delete_result = oss_service.delete_file(result['object_key'])
            
            if delete_result.get('success'):
                print("✅ 文件删除成功")
            else:
                print(f"❌ 文件删除失败: {delete_result.get('error')}")
            
            return True
        else:
            print(f"❌ 文件上传失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 上传测试发生异常: {str(e)}")
        return False

def main():
    """主函数"""
    print("开始测试阿里云OSS功能...")
    
    # 测试凭据配置
    credentials_ok = test_oss_credentials()
    
    if not credentials_ok:
        print("\n❌ 凭据配置测试失败，请检查环境变量配置")
        return
    
    # 测试文件上传
    upload_ok = test_file_upload()
    
    if upload_ok:
        print("\n🎉 所有测试通过！阿里云OSS功能正常")
    else:
        print("\n❌ 上传测试失败，请检查配置和网络连接")

if __name__ == '__main__':
    main() 