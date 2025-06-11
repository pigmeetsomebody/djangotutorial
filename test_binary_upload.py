#!/usr/bin/env python3
"""
二进制图片上传接口测试脚本

演示如何使用新增的二进制图片上传接口：
1. upload-binary-image/  - 支持Base64编码的图片数据
2. upload-raw-binary-image/  - 支持原始二进制图片数据

使用前请确保：
1. Django服务器正在运行
2. 已获取有效的访问令牌
3. 阿里云OSS配置正确
"""

import requests
import base64
import json
import io
from PIL import Image

# 配置
BASE_URL = "http://localhost:8000/api/users"
ACCESS_TOKEN = "your-access-token-here"  # 请替换为真实的访问令牌

# 请求头
HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

def create_test_image():
    """创建一个测试图片（100x100的红色方块）"""
    # 创建一个简单的测试图片
    img = Image.new('RGB', (100, 100), color='red')
    
    # 转换为字节数据
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG')
    img_bytes = img_buffer.getvalue()
    
    return img_bytes

def test_base64_upload():
    """测试Base64编码图片上传"""
    print("=== 测试Base64编码图片上传 ===")
    
    # 创建测试图片
    img_bytes = create_test_image()
    
    # 转换为Base64
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    # 方式1: 纯Base64字符串
    data1 = {
        'image_data': img_base64,
        'filename': 'test_base64_1.jpg',
        'folder': 'test'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload-binary-image/",
            headers=HEADERS,
            json=data1
        )
        print(f"方式1 - 纯Base64: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"方式1失败: {e}")
    
    # 方式2: data:image格式
    data2 = {
        'image_data': f'data:image/jpeg;base64,{img_base64}',
        'filename': 'test_base64_2.jpg',
        'folder': 'test',
        'content_type': 'image/jpeg'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload-binary-image/",
            headers=HEADERS,
            json=data2
        )
        print(f"方式2 - data:image格式: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"方式2失败: {e}")

def test_raw_binary_upload():
    """测试原始二进制数据上传"""
    print("\n=== 测试原始二进制数据上传 ===")
    
    # 创建测试图片
    img_bytes = create_test_image()
    
    # 方式1: multipart/form-data格式
    files = {
        'file': ('test_raw_1.jpg', img_bytes, 'image/jpeg')
    }
    data = {
        'filename': 'test_raw_1.jpg',
        'folder': 'test'
    }
    headers_multipart = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
        # 不设置Content-Type，让requests自动处理multipart
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload-raw-binary-image/",
            headers=headers_multipart,
            files=files,
            data=data
        )
        print(f"方式1 - multipart/form-data: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"方式1失败: {e}")
    
    # 方式2: 原始二进制数据 + 查询参数
    headers_binary = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'image/jpeg',
        'X-Filename': 'test_raw_2.jpg'
    }
    params = {
        'filename': 'test_raw_2.jpg',
        'folder': 'test'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload-raw-binary-image/",
            headers=headers_binary,
            params=params,
            data=img_bytes
        )
        print(f"方式2 - 原始二进制数据: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"方式2失败: {e}")

def test_existing_file_upload():
    """测试上传现有图片文件"""
    print("\n=== 测试传统文件上传（对比） ===")
    
    # 创建测试图片文件
    img_bytes = create_test_image()
    
    files = {
        'image': ('test_traditional.jpg', img_bytes, 'image/jpeg')
    }
    data = {
        'folder': 'test'
    }
    headers_traditional = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload-image/",
            headers=headers_traditional,
            files=files,
            data=data
        )
        print(f"传统文件上传: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"传统上传失败: {e}")

def main():
    """主函数"""
    print("开始测试二进制图片上传接口...")
    print(f"服务器地址: {BASE_URL}")
    print(f"访问令牌: {ACCESS_TOKEN[:20]}...")
    
    # 测试各种上传方式
    test_base64_upload()
    test_raw_binary_upload()
    test_existing_file_upload()
    
    print("\n测试完成！")

if __name__ == "__main__":
    main() 