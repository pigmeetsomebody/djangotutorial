import multiprocessing
import os

# 绑定的IP和端口
bind = "0.0.0.0:8001"  # 修改为8001端口

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = 'sync'

# 最大客户端并发数量
worker_connections = 1000

# 进程名称
proc_name = 'djangotutorial'

# 进程pid记录文件
pidfile = 'logs/gunicorn.pid'

# 访问日志文件
accesslog = 'logs/gunicorn_access.log'

# 错误日志文件
errorlog = 'logs/gunicorn_error.log'

# 日志级别
loglevel = 'info'

# 后台运行
daemon = True

# 重载
reload = True

# 超时时间
timeout = 30

# 最大请求数
max_requests = 2000

# 最大请求抖动
max_requests_jitter = 400

# 优雅的重启时间
graceful_timeout = 30

# 是否预加载应用
preload_app = True

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal") 