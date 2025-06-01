# Django 用户认证系统

这是一个基于 Django 的用户认证系统，实现了以下功能：

- 手机号验证码登录
- JWT token 认证
- Cookie 安全的 token 存储
- Token 刷新机制
- 用户登出功能

## 技术栈

- Python 3.x
- Django 4.x
- Django REST framework
- Simple JWT
- Swagger/OpenAPI 文档

## 环境要求

- Python 3.8+
- pip
- virtualenv (推荐)

## 安装步骤

1. 克隆项目
```bash
git clone [项目地址]
cd djangotutorial
```

2. 创建并激活虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的配置信息
```

5. 运行数据库迁移
```bash
python manage.py migrate
```

6. 启动开发服务器
```bash
python manage.py runserver
```

## API 文档

启动服务器后，访问 `/swagger/` 或 `/redoc/` 查看完整的 API 文档。

## 主要功能

### 1. 发送验证码
- 端点：`POST /api/users/send-sms-code/`
- 功能：向指定手机号发送验证码

### 2. 用户登录
- 端点：`POST /api/users/login/`
- 功能：使用手机号和验证码进行登录
- 返回：JWT token（存储在 cookie 中）

### 3. 刷新 Token
- 端点：`POST /api/users/refresh-token/`
- 功能：使用 refresh token 获取新的 access token

### 4. 用户登出
- 端点：`DELETE /api/users/login/`
- 功能：清除认证 cookie，实现登出

## 安全特性

- 使用 HttpOnly cookie 存储 token
- 支持 CSRF 保护
- 验证码有效期限制
- Token 自动刷新机制

## 开发说明

1. 代码规范
   - 遵循 PEP 8 规范
   - 使用 Black 进行代码格式化
   - 使用 isort 进行导入排序

2. 测试
   - 运行测试：`python manage.py test`
   - 测试覆盖率：`coverage run manage.py test`

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

[MIT License](LICENSE)

## 联系方式

如有问题，请提交 Issue 或联系项目维护者。 