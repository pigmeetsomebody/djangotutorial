# 阿里云OSS图片上传服务使用说明

## 概述

本项目集成了阿里云OSS（对象存储服务），提供了图片上传、批量上传和删除功能。使用默认凭据链进行身份认证，支持单张和批量图片上传。

## 环境配置

### 1. 安装依赖包

确保以下阿里云相关包已安装：

```bash
pip install alibabacloud-credentials==0.3.2
pip install alibabacloud-oss20190517==1.2.8
pip install alibabacloud-tea-openapi==0.3.7
pip install alibabacloud-tea-util==0.3.11
```

### 2. 环境变量配置

在 `.env` 文件中配置以下环境变量：

```bash
# 阿里云OSS设置
ALIBABA_CLOUD_ACCESS_KEY_ID=your-access-key-id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your-access-key-secret
ALIBABA_CLOUD_REGION_ID=cn-hangzhou
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your-bucket-name
OSS_URL_PREFIX=https://your-bucket-name.oss-cn-hangzhou.aliyuncs.com
```

### 3. 默认凭据链支持

本服务使用阿里云默认凭据链，按以下顺序查找凭据：
1. 环境变量（ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET）
2. 配置文件
3. ECS实例角色

## API接口

### 1. 单张图片上传

**接口地址：** `POST /api/users/upload-image/`

**请求参数：**
- `image`: 图片文件（必填）
- `folder`: 存储文件夹名称（可选，默认为"images"）

**请求示例：**
```bash
curl -X POST \
  -H "Authorization: Bearer your-access-token" \
  -F "image=@/path/to/your/image.jpg" \
  -F "folder=avatars" \
  http://localhost:8000/api/users/upload-image/
```

**响应示例：**
```json
{
    "message": "图片上传成功",
    "data": {
        "file_url": "https://your-bucket.oss-cn-hangzhou.aliyuncs.com/images/2024/01/15/abc123.jpg",
        "object_key": "images/2024/01/15/abc123.jpg",
        "original_filename": "my-image.jpg",
        "size": 123456
    }
}
```

### 2. 批量图片上传

**接口地址：** `POST /api/users/upload-images/`

**请求参数：**
- `images`: 图片文件列表（必填，最多10张）
- `folder`: 存储文件夹名称（可选，默认为"images"）

**请求示例：**
```bash
curl -X POST \
  -H "Authorization: Bearer your-access-token" \
  -F "images=@/path/to/image1.jpg" \
  -F "images=@/path/to/image2.jpg" \
  -F "folder=gallery" \
  http://localhost:8000/api/users/upload-images/
```

**响应示例：**
```json
{
    "message": "批量上传完成，成功2张，失败0张",
    "data": {
        "success_count": 2,
        "failed_count": 0,
        "results": [
            {
                "success": true,
                "file_url": "https://your-bucket.oss-cn-hangzhou.aliyuncs.com/gallery/2024/01/15/def456.jpg",
                "object_key": "gallery/2024/01/15/def456.jpg",
                "original_filename": "image1.jpg",
                "size": 98765
            },
            {
                "success": true,
                "file_url": "https://your-bucket.oss-cn-hangzhou.aliyuncs.com/gallery/2024/01/15/ghi789.jpg",
                "object_key": "gallery/2024/01/15/ghi789.jpg",
                "original_filename": "image2.jpg",
                "size": 87654
            }
        ]
    }
}
```

### 3. 删除图片

**接口地址：** `DELETE /api/users/delete-image/`

**请求参数：**
```json
{
    "object_key": "images/2024/01/15/abc123.jpg"
}
```

**请求示例：**
```bash
curl -X DELETE \
  -H "Authorization: Bearer your-access-token" \
  -H "Content-Type: application/json" \
  -d '{"object_key": "images/2024/01/15/abc123.jpg"}' \
  http://localhost:8000/api/users/delete-image/
```

**响应示例：**
```json
{
    "message": "图片删除成功"
}
```

## 文件存储规则

### 1. 目录结构
```
bucket/
├── images/           # 默认图片文件夹
│   └── 2024/01/15/   # 按年/月/日分组
│       ├── abc123.jpg
│       └── def456.png
├── avatars/          # 头像文件夹
│   └── 2024/01/15/
│       └── ghi789.jpg
└── gallery/          # 相册文件夹
    └── 2024/01/15/
        └── jkl012.jpg
```

### 2. 文件命名
- 使用UUID生成唯一文件名
- 保留原始文件扩展名
- 格式：`{folder}/{YYYY}/{MM}/{DD}/{uuid}.{ext}`

## 支持的图片格式

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

## 文件大小限制

- 单张图片最大：5MB
- 批量上传最多：10张图片

## 错误处理

### 常见错误码

| 状态码 | 错误信息 | 解决方案 |
|--------|----------|----------|
| 400 | 图片文件大小不能超过5MB | 压缩图片或选择更小的文件 |
| 400 | 只支持 JPEG、PNG、GIF、WebP 格式的图片 | 使用支持的图片格式 |
| 401 | 未认证或token已过期 | 重新登录获取有效token |
| 500 | OSS服务未初始化 | 检查阿里云配置是否正确 |

### 错误响应示例

```json
{
    "message": "参数验证失败",
    "errors": {
        "image": ["图片文件大小不能超过5MB"]
    }
}
```

## 前端使用示例

### JavaScript/Ajax
```javascript
// 单张图片上传
function uploadImage(file) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('folder', 'avatars');
    
    fetch('/api/users/upload-image/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('上传成功:', data);
    })
    .catch(error => {
        console.error('上传失败:', error);
    });
}

// 批量图片上传
function uploadMultipleImages(files) {
    const formData = new FormData();
    for (let file of files) {
        formData.append('images', file);
    }
    formData.append('folder', 'gallery');
    
    fetch('/api/users/upload-images/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('批量上传完成:', data);
    })
    .catch(error => {
        console.error('批量上传失败:', error);
    });
}
```

### HTML表单
```html
<!-- 单张图片上传 -->
<form id="upload-form" enctype="multipart/form-data">
    <input type="file" name="image" accept="image/*" required>
    <input type="text" name="folder" placeholder="文件夹名称（可选）">
    <button type="submit">上传图片</button>
</form>

<!-- 批量图片上传 -->
<form id="batch-upload-form" enctype="multipart/form-data">
    <input type="file" name="images" accept="image/*" multiple required>
    <input type="text" name="folder" placeholder="文件夹名称（可选）">
    <button type="submit">批量上传</button>
</form>
```

## 注意事项

1. **认证要求**：所有上传接口都需要用户认证（Bearer Token）
2. **文件安全**：上传的文件会进行格式和大小验证
3. **存储成本**：根据实际存储量和流量产生费用
4. **访问权限**：确保OSS bucket设置了正确的访问权限
5. **HTTPS访问**：建议使用HTTPS访问图片URL以确保安全

## 开发调试

### 1. 查看上传日志
```bash
tail -f django.log | grep "图片上传"
```

### 2. 测试OSS连接
```python
from users.oss_service import oss_service

# 测试上传
with open('test.jpg', 'rb') as f:
    result = oss_service.upload_file(f.read(), 'test.jpg', 'test')
    print(result)
```

### 3. 环境变量检查
```bash
echo $ALIBABA_CLOUD_ACCESS_KEY_ID
echo $OSS_BUCKET_NAME
``` 