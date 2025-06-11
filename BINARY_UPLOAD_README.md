# 二进制图片上传接口使用说明

## 概述

现在系统支持3种图片上传方式：

1. **传统文件上传** (`/api/users/upload-image/`) - 支持multipart/form-data文件上传
2. **Base64上传** (`/api/users/upload-binary-image/`) - 支持Base64编码的图片数据  
3. **原始二进制上传** (`/api/users/upload-raw-binary-image/`) - 支持原始二进制数据

## 1. Base64编码上传

**接口地址:** `POST /api/users/upload-binary-image/`

**请求格式:** JSON

**请求参数:**
```json
{
    "image_data": "base64编码的图片数据",
    "filename": "文件名.jpg", 
    "folder": "存储文件夹（可选）",
    "content_type": "image/jpeg（可选）"
}
```

**支持的数据格式:**
- 纯Base64字符串: `iVBORw0KGgoAAAANSUhEUgAA...`
- Data URL格式: `data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAA...`

**示例 (curl):**
```bash
curl -X POST \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "iVBORw0KGgoAAAANSUhEUgAA...",
    "filename": "test.jpg",
    "folder": "images"
  }' \
  http://localhost:8000/api/users/upload-binary-image/
```

**示例 (JavaScript):**
```javascript
// 从文件读取并转换为Base64
const fileInput = document.getElementById('file');
const file = fileInput.files[0];
const reader = new FileReader();

reader.onload = function() {
    const base64Data = reader.result.split(',')[1]; // 移除data:image/...;base64,前缀
    
    fetch('/api/users/upload-binary-image/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            image_data: base64Data,
            filename: file.name,
            folder: 'uploads'
        })
    });
};

reader.readAsDataURL(file);
```

## 2. 原始二进制数据上传

**接口地址:** `POST /api/users/upload-raw-binary-image/`

### 方式A: Multipart Form Data

**请求参数:**
- `file`: 图片文件
- `filename`: 文件名
- `folder`: 存储文件夹（可选）

**示例 (curl):**
```bash
curl -X POST \
  -H "Authorization: Bearer your-token" \
  -F "file=@image.jpg" \
  -F "filename=image.jpg" \
  -F "folder=uploads" \
  http://localhost:8000/api/users/upload-raw-binary-image/
```

### 方式B: 原始二进制数据

**请求头:**
- `Content-Type`: `image/jpeg` 或相应的MIME类型
- `X-Filename`: 文件名（可选）

**查询参数:**
- `filename`: 文件名
- `folder`: 存储文件夹（可选）

**示例 (curl):**
```bash
curl -X POST \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: image/jpeg" \
  -H "X-Filename: image.jpg" \
  --data-binary @image.jpg \
  "http://localhost:8000/api/users/upload-raw-binary-image/?filename=image.jpg&folder=uploads"
```

**示例 (JavaScript):**
```javascript
// 方式A: FormData
const formData = new FormData();
formData.append('file', file);
formData.append('filename', file.name);
formData.append('folder', 'uploads');

fetch('/api/users/upload-raw-binary-image/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`
    },
    body: formData
});

// 方式B: 原始二进制
fetch(`/api/users/upload-raw-binary-image/?filename=${file.name}&folder=uploads`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': file.type,
        'X-Filename': file.name
    },
    body: file
});
```

## 3. 接口对比

| 特性 | 传统文件上传 | Base64上传 | 原始二进制上传 |
|------|-------------|------------|----------------|
| 请求格式 | multipart/form-data | application/json | multipart或binary |
| 数据编码 | 无需编码 | Base64编码 | 无需编码 |
| 传输大小 | 原始大小 | +33%开销 | 原始大小 |
| 易用性 | 简单 | 适合JSON API | 灵活 |
| 适用场景 | 表单上传 | 前端canvas/blob | 移动端/API |

## 4. 响应格式

所有接口成功时返回相同格式：

```json
{
    "message": "图片上传成功",
    "data": {
        "file_url": "https://bucket.oss-cn-hangzhou.aliyuncs.com/images/2024/01/15/abc123.jpg",
        "object_key": "images/2024/01/15/abc123.jpg", 
        "original_filename": "test.jpg",
        "size": 12345
    }
}
```

## 5. 限制和注意事项

- **文件大小限制:** 最大5MB
- **支持格式:** JPEG、PNG、GIF、WebP
- **认证要求:** 需要有效的Bearer Token
- **文件名要求:** 只能包含字母、数字、点、下划线、连字符
- **Base64限制:** 需要考虑33%的大小增长

## 6. 错误处理

常见错误响应：

```json
{
    "message": "参数验证失败",
    "errors": {
        "image_data": ["图片数据大小不能超过5MB"]
    }
}
```

```json
{
    "message": "图片上传失败", 
    "error": "无效的图片数据"
}
``` 