#!/usr/bin/env python3
"""
二进制图片上传演示脚本
"""

import requests
import base64
import json

# 配置
BASE_URL = "http://localhost:8000/api/users"
ACCESS_TOKEN = "your-token-here"  # 替换为真实token

def demo_base64_upload():
    """演示Base64上传"""
    print("=== Base64上传演示 ===")
    
    # 读取图片文件并转换为Base64
    with open('test.jpg', 'rb') as f:
        img_data = f.read()
        img_base64 = base64.b64encode(img_data).decode('utf-8')
    
    # 发送请求
    data = {
        'image_data': img_base64,
        'filename': 'demo.jpg',
        'folder': 'demo'
    }
    
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        f"{BASE_URL}/upload-binary-image/",
        headers=headers,
        json=data
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

def demo_raw_binary_upload():
    """演示原始二进制上传"""
    print("\n=== 原始二进制上传演示 ===")
    
    # 读取图片文件
    with open('test.jpg', 'rb') as f:
        img_data = f.read()
    
    # 使用multipart形式上传
    files = {'file': ('demo2.jpg', img_data, 'image/jpeg')}
    data = {'filename': 'demo2.jpg', 'folder': 'demo'}
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    
    response = requests.post(
        f"{BASE_URL}/upload-raw-binary-image/",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

if __name__ == "__main__":
    print("请先替换ACCESS_TOKEN变量为真实的访问令牌")
    print("并确保当前目录有test.jpg文件")
    # demo_base64_upload()
    # demo_raw_binary_upload() 