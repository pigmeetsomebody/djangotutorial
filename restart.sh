#!/bin/bash

# 停止现有的 Gunicorn 进程
if [ -f logs/gunicorn.pid ]; then
    echo "Stopping Gunicorn..."
    kill -TERM $(cat logs/gunicorn.pid)
    rm logs/gunicorn.pid
    sleep 2
fi

# 重启 Nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx

# 启动 Gunicorn
echo "Starting Gunicorn..."
gunicorn -c gunicorn_config.py djangotutorial.wsgi:application

# 检查 Gunicorn 是否成功启动
if [ $? -eq 0 ]; then
    echo "Gunicorn started successfully"
else
    echo "Failed to start Gunicorn"
    exit 1
fi

echo "Service restart completed" 