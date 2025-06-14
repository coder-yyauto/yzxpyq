import multiprocessing

# 绑定的IP和端口
bind = "127.0.0.1:5000"

# 工作进程数，一般设置为CPU核心数的2-4倍
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "sync"

# 超时时间
timeout = 120

# 用户和组，运行进程的用户yzxuser
user = "yzxuser"
group = "yzxuser"

# 进程名称
proc_name = "campus_gunicorn"

# 访问日志和错误日志
accesslog = "/var/log/campus_yzx/campus_access.log"
errorlog = "/var/log/campus_yzx/campus_error.log"
loglevel = "info"

# 是否守护进程
daemon = False

# 工作目录
chdir = "/home/yzxuser/yzxpyq/backend"

# 预加载应用
preload_app = True

# 限制请求行大小
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190 