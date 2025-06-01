#!/bin/bash

# 设置环境变量
export DJANGO_DEBUG=False
export DJANGO_SECRET_KEY='your-secret-key-here'  # 请修改为安全的密钥
export DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost,your-server-ip'  # 请修改为您的服务器IP
export DJANGO_CORS_ALLOWED_ORIGINS='http://127.0.0.1:8001,http://localhost:8001,http://your-server-ip'  # 修改为8001端口
export DJANGO_LOG_LEVEL=INFO

# 创建必要的目录
mkdir -p logs
mkdir -p static
mkdir -p media
mkdir -p staticfiles

# 收集静态文件
python manage.py collectstatic --noinput

# 数据库迁移
python manage.py migrate

# 停止现有的Gunicorn进程
if [ -f logs/gunicorn.pid ]; then
    kill -TERM $(cat logs/gunicorn.pid)
    rm logs/gunicorn.pid
fi

# 启动Gunicorn
gunicorn -c gunicorn_config.py djangotutorial.wsgi:application

# 检查Gunicorn是否成功启动
if [ $? -eq 0 ]; then
    echo "Gunicorn started successfully"
else
    echo "Failed to start Gunicorn"
    exit 1
fi

# 重启Nginx
sudo systemctl restart nginx

echo "Deployment completed successfully" 