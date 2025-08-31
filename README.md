# 修行记录后台管理系统

基于Flask开发的佛教修行记录后台管理系统，支持佛号经文、回向文本和修行记录的管理，并提供API接口供Flutter移动应用数据同步。

## 功能特性

### 🧘‍♂️ 核心功能
- **佛号经文管理**: 支持佛号和经文的增删改查，包含注音功能
- **回向文管理**: 管理回向文本和模板
- **修行记录追踪**: 记录用户的修行进度和统计
- **用户管理**: 管理移动应用用户
- **统计分析**: 提供详细的修行统计报表

### 🔧 技术特性
- **数据库兼容**: 支持MySQL和SQLite数据库
- **连接池优化**: 内置数据库连接池，支持连接监控和自动重连
- **API接口**: 提供RESTful API供Flutter应用同步数据
- **JWT认证**: 移动应用API使用JWT Token认证
- **Web管理**: 基于Bootstrap的响应式后台管理界面
- **数据同步**: 与Flutter应用数据库结构完全一致
- **系统监控**: 提供数据库连接池状态和系统健康检查

## 项目结构

```
backend/
├── app.py                 # Flask应用主文件
├── config.py             # 配置文件
├── requirements.txt      # Python依赖
├── models/              # 数据模型
│   ├── __init__.py
│   ├── user.py          # 用户模型
│   ├── chanting.py      # 佛号经文模型
│   ├── dedication.py    # 回向文模型
│   ├── chanting_record.py # 修行记录模型
│   ├── daily_stats.py   # 每日统计模型
│   └── dedication_template.py # 回向文模板模型
├── routes/              # 路由文件
│   ├── auth.py          # 认证路由
│   ├── main.py          # 主页路由
│   ├── chanting.py      # 佛号经文管理
│   ├── dedication.py    # 回向文管理
│   ├── records.py       # 修行记录管理
│   ├── stats.py         # 统计报表
│   └── api.py           # API接口
├── templates/           # HTML模板
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   └── auth/
└── static/             # 静态文件
    ├── css/
    ├── js/
    └── images/
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置数据库

#### 使用SQLite（开发环境）
无需额外配置，默认使用SQLite数据库。

#### 使用MySQL（生产环境）
1. 创建MySQL数据库：
```sql
CREATE DATABASE xiuxing_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 设置环境变量：
```bash
export DATABASE_URL="mysql+pymysql://username:password@localhost/xiuxing_db"
export SECRET_KEY="your-secret-key"
export JWT_SECRET_KEY="your-jwt-secret-key"
```

### 3. 运行应用

```bash
python app.py
```

访问 http://localhost:5000

### 4. 默认管理员账户

- 用户名: `admin`
- 密码: `admin123`

## API文档

### 认证接口

#### 用户登录
```
POST /api/auth/login
Content-Type: application/json

{
    "username": "用户名",
    "password": "密码"
}
```

#### 用户注册
```
POST /api/auth/register
Content-Type: application/json

{
    "username": "用户名",
    "password": "密码",
    "nickname": "昵称",
    "avatar": "头像",
    "avatar_type": "emoji"
}
```

### 佛号经文接口

#### 获取佛号经文列表
```
GET /api/chantings?type=buddhaNam&page=1&per_page=20
Authorization: Bearer <token>
```

#### 创建佛号经文
```
POST /api/chantings
Authorization: Bearer <token>
Content-Type: application/json

{
    "title": "标题",
    "content": "内容",
    "pronunciation": "注音",
    "type": "buddhaNam"
}
```

### 修行记录接口

#### 获取修行记录
```
GET /api/chanting-records?page=1&per_page=20
Authorization: Bearer <token>
```

#### 创建修行记录
```
POST /api/chanting-records
Authorization: Bearer <token>
Content-Type: application/json

{
    "chanting_id": 1
}
```

### 每日统计接口

#### 更新每日统计
```
POST /api/daily-stats
Authorization: Bearer <token>
Content-Type: application/json

{
    "chanting_id": 1,
    "count": 108,
    "date": "2024-01-01"
}
```

#### 增加念诵次数
```
POST /api/daily-stats/increment
Authorization: Bearer <token>
Content-Type: application/json

{
    "chanting_id": 1,
    "increment": 1
}
```

## 数据库设计

### 用户表 (users)
- id: 主键
- username: 用户名
- password: 密码哈希
- avatar: 头像
- avatar_type: 头像类型 (emoji/image)
- nickname: 昵称
- created_at: 创建时间

### 佛号经文表 (chantings)
- id: 主键
- title: 标题
- content: 内容
- pronunciation: 注音
- type: 类型 (buddhaNam/sutra)
- is_built_in: 是否内置
- is_deleted: 逻辑删除标记
- created_at/updated_at: 时间戳

### 修行记录表 (chanting_records)
- id: 主键
- chanting_id: 佛号经文ID
- user_id: 用户ID
- created_at/updated_at: 时间戳

### 每日统计表 (daily_stats)
- id: 主键
- chanting_id: 佛号经文ID
- user_id: 用户ID
- count: 念诵次数
- date: 统计日期
- created_at/updated_at: 时间戳

### 系统监控接口

#### 健康检查
```
GET /system/health
```

#### 数据库连接池状态（需登录）
```
GET /system/db-pool
Authorization: 管理员登录
```

#### 重置连接池（需登录）
```
POST /system/db-pool/reset
Authorization: 管理员登录
```

## 连接池配置

### 开发环境（SQLite）
SQLite不支持连接池，系统会自动禁用连接池配置。

### 生产环境（MySQL）
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,           # 连接池大小
    'pool_timeout': 30,        # 获取连接超时时间
    'pool_recycle': 1800,      # 连接回收时间（秒）
    'pool_pre_ping': True,     # 连接前ping检查
    'max_overflow': 30,        # 超出pool_size后最多创建的连接数
    'pool_reset_on_return': 'commit',
}
```

### 连接池监控
- 自动健康检查
- 连接状态监控
- 异常自动重连
- 系统资源监控

## 部署说明

### 生产环境配置

1. 设置环境变量：
```bash
export FLASK_ENV=production
export DATABASE_URL="mysql+pymysql://username:password@localhost/xiuxing_db"
export SECRET_KEY="production-secret-key"
export JWT_SECRET_KEY="production-jwt-secret-key"
```

2. 使用Gunicorn运行：
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. 配置Nginx反向代理（可选）

### 数据库优化建议

1. **MySQL配置优化**：
```sql
# my.cnf
[mysqld]
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
max_connections = 200
wait_timeout = 28800
interactive_timeout = 28800
```

2. **连接池调优**：
   - 根据并发量调整 `pool_size`
   - 监控连接使用情况
   - 定期检查慢查询日志

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Flutter应用集成

1. 在Flutter应用中配置API基础URL
2. 使用返回的JWT Token进行API认证
3. 定期调用同步接口更新本地数据

## 开发说明

### 添加新功能

1. 在 `models/` 中添加数据模型
2. 在 `routes/` 中添加路由处理
3. 在 `templates/` 中添加HTML模板
4. 更新 `app.py` 注册新的蓝图

### 数据库迁移

使用Flask-Migrate进行数据库版本管理：

```bash
flask db init
flask db migrate -m "描述"
flask db upgrade
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

---

**南无阿弥陀佛** 🙏

*愿以此功德，回向万界众生*  
*愿众生离苦得乐，究竟解脱*