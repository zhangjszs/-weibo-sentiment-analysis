# 🚀 部署指南 (Deployment Guide)

本文档提供完整的项目部署和运行指南，包括开发环境和生产环境的部署方法。

## 📋 目录

- [快速开始](#快速开始)
- [环境要求](#环境要求)
- [数据库配置](#数据库配置)
- [依赖安装](#依赖安装)
- [爬虫配置](#爬虫配置)
- [应用启动](#应用启动)
- [生产部署](#生产部署)
- [故障排除](#故障排除)

## ⚡ 快速开始 (本地开发)

### 推荐环境 (Windows) 使用 `start.bat` 一键部署

这是目前系统最推荐的无缝拉起体验方式（本地默认**无需配置 Redis 和 Celery**）。

```powershell
# 1. 准备环境参数
# 复制 .env.example 为 .env，并配置好内网/本地数据库的相关参数和密码
cp .env.example .env

# 2. 从项目根目录直接启动一键脚本
.\start.bat
```
这将在独立窗口分别拉起 Flask和Vite，当你开发完毕时，使用 `.\start.bat stop` 安全停止所有服务。

### 手动部署 (跨平台 Linux/macOS)

```bash
# 1. 环境准备
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 2. 安装依赖
pip install -r requirements.txt

# 3. 数据库初始化
# 登录本地 mysql 并执行数据库导入指令
mysql -u root -p < database/new.sql
mysql -u root -p < database/user.sql
# （其它 sql 详见下文 数据库配置 章节）

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，至少配置：SECRET_KEY / JWT_SECRET_KEY / DB_*

# 5. 分别启动应用
python run.py  # 后端
# 在新终端中：cd frontend && pnpm install && pnpm dev  # 前端
```

### 容器化编排（全栈）

项目根目录提供 `docker-compose.yml`，默认拉起以下服务：
- `mysql`（业务数据库）
- `redis`（任务队列/结果后端）
- `web`（Flask 后端，端口 `5000`）
- `frontend`（Nginx 前端，端口 `3000`）
- `spider-api`、`spider-worker`（端口 `8090`）
- `nlp-api`、`nlp-worker`（端口 `8091`）

启动：
```bash
docker compose up -d --build
```

停止：
```bash
docker compose down
```

仅启动 Spider/NLP 独立服务（宿主机 Flask 模式）：
```bash
docker compose up -d --build redis spider-api spider-worker nlp-api nlp-worker
```

宿主机 `.env` 需启用远程调度配置：
```bash
SPIDER_SERVICE_ENABLED=True
SPIDER_SERVICE_BASE_URL=http://localhost:8090
NLP_SERVICE_ENABLED=True
NLP_SERVICE_BASE_URL=http://localhost:8091
```

## 🔧 环境要求

### 系统要求
- **操作系统**: Windows 10+ / Ubuntu 18.04+ / macOS 10.15+
- **内存**: 至少 4GB RAM
- **磁盘**: 至少 2GB 可用空间

### 软件要求
- **Python**: 3.8 - 3.12
- **MySQL**: 5.7+ (推荐 8.0+)
- **Git**: 2.0+
- **Node.js**: 14+ (可选，用于前端构建)

### Python 依赖包
主要依赖包已在 `requirements.txt` 中列出：
```
Flask==3.1.0
pandas==2.2.3
scikit-learn==1.6.1
jieba==0.42.1
PyMySQL==1.1.1
matplotlib==3.9.2
wordcloud==1.9.3
```

## 🗄️ 数据库配置

### 1. MySQL 安装

#### Windows
```bash
# 使用 Chocolatey 安装
choco install mysql

# 或下载 MSI 安装包
# https://dev.mysql.com/downloads/mysql/
```

#### Ubuntu
```bash
sudo apt update
sudo apt install mysql-server-8.0
sudo mysql_secure_installation
```

#### macOS
```bash
brew install mysql
brew services start mysql
mysql_secure_installation
```

### 2. 数据库初始化

```bash
# 连接到 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE wb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 导入表结构
USE wb;
SOURCE database/new.sql;
SOURCE database/user.sql;
SOURCE database/article.sql;
SOURCE database/comments.sql;

# 创建用户（可选）
CREATE USER 'weibo_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON wb.* TO 'weibo_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 配置文件修改

项目运行配置统一来自根目录 `.env`，不再通过编辑 `src/utils/query.py` 修改数据库连接。至少需要配置：

```bash
DB_HOST=localhost
DB_PORT=3306
DB_USER=weibo_user
DB_PASSWORD=your_password
DB_NAME=wb
SECRET_KEY=replace-me
JWT_SECRET_KEY=replace-me-too
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

安全建议：

- 保持 `AUTO_CREATE_DEMO_ADMIN=False`
- 保持 `DEMO_ADMIN_RESET_PASSWORD=False`
- 生产环境务必设置 `FLASK_ENV=production`

## 📦 依赖安装

### 虚拟环境创建

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 依赖包安装

```bash
# 安装所有依赖
pip install -r requirements.txt

# 验证安装
pip list | grep -E "(Flask|pandas|scikit-learn|jieba)"
```

### Conda 环境（可选）

```bash
# 创建 Conda 环境
conda create -n weibo_env python=3.10
conda activate weibo_env

# 安装依赖
pip install -r requirements.txt
```

## 🕷️ 爬虫配置

### Cookie 配置（重要）

1. **获取 Cookie**
   - 打开浏览器访问 https://weibo.com
   - 按 F12 打开开发者工具
   - 切换到 Network 标签
   - 刷新页面，找到任意 weibo.com 请求
   - 复制 Request Headers 中的 Cookie 值

2. **更新配置文件**
   编辑以下文件中的 Cookie：
   - `spider/config.py`
   - `spider/improved_config.py`
   - `safe_spider_config.txt`

   ```python
   'Cookie': '你的Cookie字符串'
   ```

### 代理配置（可选）

```bash
# 获取免费代理
python spider/proxy_fetcher.py

# 测试代理
python test_spider_system.py
```

## 🌐 应用启动

### 开发模式启动

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，开发环境至少配置：DB_*、SECRET_KEY（可选）、JWT_SECRET_KEY（可选）

# 2. 启动后端
python run.py
```

### 自定义端口启动

```bash
# 通过环境变量或反向代理指定端口；开发直接修改 run.py / 启动命令即可
```

### 后台运行

```bash
# 使用 nohup
nohup python run.py &

# 或使用 screen
screen -S weibo_app
python run.py
# Ctrl+A+D 脱离
```

## 🏭 生产部署

> **注：** 本项目已精简了针对 Redis 和 Celery 的重型架构，所以生产部署相比以往变得非常简单。只要起好一个 WSGI Backend 和一个静态前端网页服务器即可。

### 后端部署 (Gunicorn / uWSGI)

**选项 A: Gunicorn (Linux 推荐)**

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动应用 (-w 4 代表 4 个子进程并发)
# 请确保生产环境的 .env 里已经修改了复杂的 SECRET_KEY 与数据库生产机密
gunicorn -w 4 -b 0.0.0.0:5000 "src.app:app"
```

### 前端 Nginx（SPA 路由回退）

如果前端使用 Nginx 托管构建产物，需要开启 `try_files ... /index.html`，否则用户在生产环境直接访问 `/home` 等路由会出现 404。

本项目已在 `frontend/nginx.conf` 中配置：

```nginx
location / {
  try_files $uri $uri/ /index.html;
}
```

并对 `/api`、`/getAllData` 做反向代理到后端服务，避免跨域与直连后端端口。

### 使用 uWSGI

```bash
# 安装 uWSGI
pip install uwsgi

# 创建配置文件 uwsgi.ini
[uwsgi]
module = src.app:app
master = true
processes = 4
socket = 127.0.0.1:5000
chmod-socket = 664
vacuum = true
die-on-term = true

# 启动
uwsgi --ini uwsgi.ini
```

### Nginx 配置

```nginx
# /etc/nginx/sites-available/weibo_app
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/project/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### SSL 配置（HTTPS）

```nginx
server {
    listen 443 ssl http2;
    server_name your_domain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;

    # ... 其他配置
}
```

### Systemd 服务

创建 `/etc/systemd/system/weibo-app.service`：

```ini
[Unit]
Description=Weibo Opinion Analysis App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project
Environment="PATH=/path/to/your/venv/bin"
ExecStart=/path/to/your/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "src.app:app"
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl start weibo-app
sudo systemctl enable weibo-app

# 查看状态
sudo systemctl status weibo-app

# 查看日志
sudo journalctl -u weibo-app -f
```

## 🔧 故障排除

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查 MySQL 服务状态
sudo systemctl status mysql

# 检查连接
mysql -u your_user -p -h localhost wb

# 测试 Python 连接
python -c "import pymysql; pymysql.connect(host='localhost', user='your_user', password='your_pass', database='wb')"
```

#### 2. 爬虫无法获取数据
- 检查 Cookie 是否过期
- 更新 User-Agent
- 检查网络连接
- 尝试使用代理

#### 3. 应用启动失败
```bash
# 检查端口占用
netstat -tlnp | grep 5000

# 检查 Python 路径
which python
python --version

# 检查依赖
pip check
```

#### 4. 内存不足
```bash
# 检查内存使用
free -h

# 增加交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 日志查看

```bash
# 应用日志
tail -f logs/app.log

# MySQL 日志
tail -f /var/log/mysql/error.log

# 系统日志
journalctl -f
```

### 性能优化

1. **数据库优化**
   ```sql
   -- 添加索引
   CREATE INDEX idx_created_at ON article(created_at);
   CREATE INDEX idx_user_id ON comments(user_id);
   ```

2. **应用优化**
   ```python
   # 启用缓存
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   ```

3. **系统优化**
   ```bash
   # 增加文件描述符限制
   echo "www-data soft nofile 65536" >> /etc/security/limits.conf
   echo "www-data hard nofile 65536" >> /etc/security/limits.conf
   ```

## 📞 获取帮助

如果遇到问题，请：

1. 查看项目 Issues
2. 检查日志文件
3. 提供详细的错误信息
4. 说明你的环境配置

---

**最后更新**: 2025年9月20日
认证说明：

- 登录后后端会写入 `HttpOnly` 认证 Cookie，前端页面刷新后依靠 Cookie 恢复会话。
- 如前后端跨域部署，需保证 `ALLOWED_ORIGINS`、代理与 Cookie 域名配置一致。
