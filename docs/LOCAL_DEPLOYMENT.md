# 微博舆情分析系统 - 本地部署指南（无Docker）

**适用场景**: 本地开发、测试环境、生产环境（无Docker场景）  
**部署难度**: ⭐⭐⭐ 中等  
**预计时间**: 30-60分钟

---

## 📋 环境要求

### 必需软件
| 软件 | 版本要求 | 下载地址 |
|------|----------|----------|
| Python | 3.8 - 3.11 | https://www.python.org/downloads/ |
| MySQL | 5.7+ 或 8.0+ | https://dev.mysql.com/downloads/ |
| Redis | 5.0+ | https://redis.io/download |

### 可选软件
| 软件 | 用途 |
|------|------|
| Node.js 18+ | 前端开发/构建 |
| Git | 代码版本管理 |

---

## 第一步：环境准备

### 1.1 安装Python

**Windows**:
```powershell
# 1. 下载Python安装包并安装
# 2. 验证安装
python --version
pip --version

# 3. 创建虚拟环境（推荐）
python -m venv venv

# 4. 激活虚拟环境
.\venv\Scripts\activate
```

**macOS/Linux**:
```bash
# 使用 pyenv 安装 Python（推荐）
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv global 3.11.0

# 创建虚拟环境
python -m venv venv
source venv/bin/activate
```

### 1.2 安装MySQL

**Windows**:
1. 下载 MySQL Installer: https://dev.mysql.com/downloads/installer/
2. 选择 "Server only" 或 "Full" 安装
3. 记住设置的 root 密码
4. 验证安装:
```powershell
# 添加到环境变量后
mysql --version
mysql -u root -p
```

**macOS**:
```bash
# 使用 Homebrew 安装
brew install mysql
brew services start mysql

# 设置 root 密码
mysql_secure_installation
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql

# 设置 root 密码
sudo mysql_secure_installation
```

### 1.3 安装Redis

**Windows**:
```powershell
# 方法1：使用 Chocolatey
choco install redis-64

# 方法2：使用 WSL
wsl sudo apt install redis-server
wsl sudo service redis-server start

# 方法3：下载 MSYS2 版本
# https://github.com/microsoftarchive/redis/releases
```

**macOS**:
```bash
brew install redis
brew services start redis
```

**Linux**:
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis
sudo systemctl enable redis
```

### 1.4 验证Redis安装
```bash
redis-cli ping
# 应该返回: PONG
```

---

## 第二步：数据库初始化

### 2.1 创建数据库

```bash
# 登录MySQL
mysql -u root -p

# 在MySQL命令行中执行
CREATE DATABASE IF NOT EXISTS wb 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

SHOW DATABASES;
EXIT;
```

### 2.2 导入数据库结构

```bash
# 使用初始化脚本（推荐）
mysql -u root -p wb < database/init_database.sql

# 或者分步导入
# mysql -u root -p wb < database/new.sql
# mysql -u root -p wb < database/user.sql
```

### 2.3 验证数据库

```bash
mysql -u root -p -e "USE wb; SHOW TABLES;"
# 应该显示: article, comments, user, reposts 等表
```

---

## 第三步：项目配置

### 3.1 克隆/解压项目

```bash
# 进入项目目录
cd 基于python微博舆情分析可视化系统

# 确认目录结构
ls
# 应该看到: src/, frontend/, database/, requirements.txt 等
```

### 3.2 创建Python虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 验证虚拟环境
which python  # 应该显示 venv 路径
```

### 3.3 安装Python依赖

```bash
# 升级 pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 验证关键依赖
python -c "import flask; print(flask.__version__)"
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

**依赖安装问题处理**:

```bash
# 如果遇到编译错误，安装系统依赖（Ubuntu/Debian）
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential

# macOS
xcode-select --install
brew install mysql-client

# Windows 如遇到错误，尝试预编译包
pip install --only-binary :all: mysqlclient
```

### 3.4 配置环境变量

**方法1：使用 .env 文件（推荐）**

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件，填入实际配置
```

**.env 文件关键配置**:

```ini
# ========== Flask 配置 ==========
SECRET_KEY=your-very-long-secret-key-here-at-least-32-characters
JWT_SECRET_KEY=your-jwt-secret-key-here-at-least-32-characters
JWT_EXPIRATION_HOURS=24
FLASK_ENV=production
DEBUG=False

# ========== 数据库配置 ==========
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_NAME=wb
DB_POOL_SIZE=10

# ========== Redis 配置 ==========
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ========== 爬虫配置 ==========
WEIBO_COOKIE=your-weibo-cookie-here
SPIDER_TIMEOUT=45
SPIDER_DELAY=15
SPIDER_MAX_RETRIES=3
SPIDER_USE_PROXY=False

# 禁用独立服务（本地部署使用本地模式）
SPIDER_SERVICE_ENABLED=False
NLP_SERVICE_ENABLED=False

# ========== 日志配置 ==========
LOG_LEVEL=INFO

# ========== 跨域配置 ==========
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# ========== 管理员配置 ==========
ADMIN_USERS=admin
AUTO_CREATE_DEMO_ADMIN=True
DEMO_ADMIN_USERNAME=admin
DEMO_ADMIN_PASSWORD=Admin123!
```

**方法2：使用环境变量（Linux/macOS）**

```bash
# 导出环境变量
export SECRET_KEY="your-secret-key"
export DB_PASSWORD="your-db-password"
# ... 其他变量

# 验证
env | grep SECRET_KEY
```

**方法3：使用环境变量（Windows PowerShell）**

```powershell
$env:SECRET_KEY="your-secret-key"
$env:DB_PASSWORD="your-db-password"
# ... 其他变量

# 验证
Get-ChildItem Env: | Where-Object { $_.Name -like "SECRET*" }
```

---

## 第四步：启动后端服务

### 4.1 验证配置

```bash
# 激活虚拟环境
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# 验证数据库连接
python -c "
from src.database import db_session
from src.config.settings import Config
print(f'DB_HOST: {Config.DB_HOST}')
print(f'DB_NAME: {Config.DB_NAME}')
"
```

### 4.2 启动主应用

```bash
# 方式1：使用 Flask 开发服务器（仅开发）
$env:FLASK_APP="src/app.py"  # PowerShell
export FLASK_APP=src/app.py   # Linux/macOS

flask run --host=0.0.0.0 --port=5000

# 方式2：使用 Python 直接运行（推荐）
python src/app.py

# 方式3：使用 Gunicorn（生产环境，Linux/macOS）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "src.app:app"

# 方式4：使用 Waitress（生产环境，Windows）
pip install waitress
waitress-serve --listen=0.0.0.0:5000 src.app:app
```

### 4.3 验证后端启动

```bash
# 测试健康检查端点
curl http://localhost:5000/health

# 应该返回: {"status": "ok", ...}
```

### 4.4 启动 Celery 任务队列（可选，用于异步任务）

**终端1：启动 Worker**
```bash
# 激活虚拟环境
cd 基于python微博舆情分析可视化系统
.\venv\Scripts\activate

# 启动 Celery Worker
celery -A src.tasks.celery_config worker --loglevel=info -Q spider,sentiment,default
```

**终端2：启动 Beat（定时任务）**
```bash
# 激活虚拟环境
celery -A src.tasks.celery_config beat --loglevel=info
```

---

## 第五步：前端部署

### 5.1 安装Node.js依赖

```bash
# 进入前端目录
cd frontend

# 安装依赖（推荐使用pnpm或yarn）
npm install
# 或
pnpm install
# 或
yarn install
```

### 5.2 配置前端API地址

编辑 `frontend/.env` 或 `frontend/.env.local`:

```ini
# API 基础地址
VITE_API_BASE_URL=http://localhost:5000

# WebSocket 地址（如使用）
VITE_WS_URL=ws://localhost:5000
```

### 5.3 开发模式启动

```bash
# 启动开发服务器
npm run dev

# 访问 http://localhost:3000
```

### 5.4 生产模式构建

```bash
# 构建生产版本
npm run build

# 构建输出在 dist/ 目录
```

### 5.5 使用Nginx部署前端（生产环境）

**安装Nginx**:

```bash
# Windows: 下载 http://nginx.org/en/download.html
# macOS:
brew install nginx

# Linux:
sudo apt install nginx  # Ubuntu/Debian
sudo yum install nginx  # CentOS/RHEL
```

**Nginx配置** (`nginx.conf`):

```nginx
server {
    listen 80;
    server_name localhost;

    # 前端静态文件
    location / {
        root /path/to/your/project/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    # 数据API代理
    location /getAllData/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**启动Nginx**:

```bash
# Windows
start nginx
nginx -s reload  # 重载配置

# macOS/Linux
sudo nginx
sudo nginx -s reload
```

---

## 第六步：验证部署

### 6.1 访问系统

```bash
# 浏览器访问
http://localhost:3000    # 前端（开发模式）
http://localhost:80      # 前端（Nginx）
http://localhost:5000    # 后端API
```

### 6.2 测试关键功能

```bash
# 1. 测试API
curl http://localhost:5000/api/auth/me

# 2. 测试数据接口
curl http://localhost:5000/api/stats/summary

# 3. 测试大屏数据
curl http://localhost:5000/api/bigscreen/stats
```

### 6.3 登录测试

```bash
# 使用默认管理员账号登录
# 用户名: admin
# 密码: Admin123!
# 或使用数据库中配置的账号
```

---

## 第七步：系统服务化（可选，生产环境）

### 7.1 Windows 服务（使用 NSSM）

```powershell
# 下载 NSSM: https://nssm.cc/download
# 安装服务
nssm install WeiboBackend
nssm set WeiboBackend Application C:\path\to\venv\Scripts\python.exe
nssm set WeiboBackend AppDirectory C:\path\to\project
nssm set WeiboBackend AppParameters src\app.py
nssm start WeiboBackend
```

### 7.2 Linux systemd 服务

创建 `/etc/systemd/system/weibo-backend.service`:

```ini
[Unit]
Description=Weibo Sentiment Analysis Backend
After=network.target mysql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
Environment="SECRET_KEY=your-secret-key"
Environment="DB_PASSWORD=your-db-password"
# ... 其他环境变量
ExecStart=/path/to/venv/bin/python src/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable weibo-backend
sudo systemctl start weibo-backend
sudo systemctl status weibo-backend
```

### 7.3 Supervisor（进程管理）

```bash
# 安装
pip install supervisor

# 生成配置
echo_supervisord_conf > supervisord.conf

# 编辑配置，添加程序
```

---

## 常见问题排查

### 问题1：MySQL连接失败

**症状**: `Can't connect to MySQL server`

**解决**:
```bash
# 检查MySQL是否运行
# Windows: 服务管理器查看 MySQL 服务
# Linux/macOS:
sudo systemctl status mysql

# 检查连接信息
mysql -u root -p -h localhost -e "SHOW DATABASES;"

# 检查防火墙
sudo ufw allow 3306  # Ubuntu
```

### 问题2：Redis连接失败

**症状**: `Error connecting to Redis`

**解决**:
```bash
# 检查Redis是否运行
redis-cli ping

# 检查端口
netstat -an | grep 6379  # 或 ss -tlnp | grep 6379
```

### 问题3：Python依赖安装失败

**症状**: `error: Microsoft Visual C++ 14.0 is required`

**解决**:
```bash
# Windows 安装 Visual C++ Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 或使用预编译包
pip install --only-binary :all: -r requirements.txt
```

### 问题4：端口被占用

**症状**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS:
lsof -i :5000
kill -9 <PID>
```

### 问题5：前端API请求失败

**症状**: `404 Not Found` 或 CORS 错误

**解决**:
```bash
# 检查后端是否运行
curl http://localhost:5000/health

# 检查前端配置
# 确认 frontend/.env 中的 VITE_API_BASE_URL 正确

# 检查 CORS 配置
# 确认 .env 中的 ALLOWED_ORIGINS 包含前端地址
```

### 问题6：中文乱码

**症状**: 数据库中中文显示为 `???`

**解决**:
```sql
-- 检查数据库字符集
SHOW CREATE DATABASE wb;
SHOW CREATE TABLE article;

-- 如不正确，重新创建数据库
ALTER DATABASE wb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 性能优化建议

### 1. MySQL优化

编辑 `my.cnf` 或 `my.ini`:

```ini
[mysqld]
# 内存配置（根据服务器内存调整）
innodb_buffer_pool_size = 512M
max_connections = 200

# 字符集
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

### 2. Redis优化

```bash
# 编辑 redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### 3. Python优化

```bash
# 使用 PyPy（高性能Python解释器）
# 或启用 Python 优化模式
python -O src/app.py
```

---

## 目录结构参考

```
基于python微博舆情分析可视化系统/
├── venv/                      # Python虚拟环境
├── src/                       # 后端代码
│   ├── app.py                # 主应用
│   ├── config/               # 配置
│   ├── services/             # 服务层
│   └── ...
├── frontend/                  # 前端代码
│   ├── dist/                 # 构建输出
│   └── ...
├── database/                  # 数据库脚本
│   └── init_database.sql
├── logs/                      # 日志目录
├── .env                       # 环境变量配置
├── requirements.txt           # Python依赖
└── REPAIR_PLAN.md            # 修复计划
```

---

## 📞 获取帮助

如果遇到问题:

1. 查看日志: `logs/app.log`
2. 检查配置: 确保 `.env` 配置正确
3. 查看文档: `docs/` 目录下的文档
4. 运行测试: `pytest tests/ -v`

---

**部署完成！** 🎉

现在你可以访问 http://localhost:3000 使用系统了。
