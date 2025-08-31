# 配置系统使用说明

## 📋 概述

后台管理系统使用JSON配置文件来管理所有配置项，支持Base64编码的敏感信息，提供灵活的数据库切换和环境配置。

## 🔧 配置文件结构

### 主配置文件: `config.json`

```json
{
  "database": {
    "type": "mysql",  // 数据库类型: mysql 或 sqlite
    "sqlite": {
      "path": "data/xiuxing.db"  // SQLite数据库路径
    },
    "mysql": {
      "host": "d3d3LnJvbmdodWF4dWVsZW5nLnNpdGU=",  // Base64编码的主机名
      "port": "MzMwNg==",  // Base64编码的端口
      "user": "cm9vdA==",  // Base64编码的用户名
      "password": "WGlueWFuMTIwM0BA",  // Base64编码的密码
      "password_encoded": true,  // 是否启用Base64编码
      "database": "eGl1eGluZw==",  // Base64编码的数据库名
      "charset": "utf8mb4"
    },
    "pool": {
      "pool_size": 10,
      "max_overflow": 20,
      "pool_timeout": 30,
      "pool_recycle": 3600,
      "pool_pre_ping": true
    }
  },
  "app": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "secret_key": "your-secret-key-here"
  },
  "development": {
    "enabled": false,  // 是否启用开发模式
    "auto_reload": true,
    "watch_directories": ["models", "routes", "templates", "static", "utils"],
    "ignore_patterns": ["*.pyc", "*.log", "*.tmp", "__pycache__/*", "logs/*", "data/*"]
  },
  "upload": {
    "max_file_size": 52428800,  // 50MB
    "allowed_extensions": ["txt", "json", "csv", "xlsx"],
    "upload_folder": "uploads"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/app.log"
  },
  "jwt": {
    "secret_key": "jwt-secret-key-here",
    "access_token_expires_days": 30
  },
  "cors": {
    "origins": ["*"]
  }
}
```

## 🔐 Base64编码支持

### 何时使用Base64编码

设置 `"password_encoded": true` 时，系统会自动解码以下字段：
- `host` - 主机名
- `port` - 端口号  
- `user` - 用户名
- `password` - 密码
- `database` - 数据库名

### Base64编码工具

```bash
# 编码
echo -n "your-string" | base64

# 解码
echo "encoded-string" | base64 -d
```

### 示例

```bash
# 编码示例
echo -n "www.example.com" | base64
# 输出: d3d3LmV4YW1wbGUuY29t

echo -n "3306" | base64  
# 输出: MzMwNg==

echo -n "root" | base64
# 输出: cm9vdA==
```

## 🗄️ 数据库配置

### MySQL配置

```json
{
  "database": {
    "type": "mysql",
    "mysql": {
      "host": "localhost",           // 或Base64编码的主机名
      "port": "3306",               // 或Base64编码的端口
      "user": "root",               // 或Base64编码的用户名
      "password": "password",       // 或Base64编码的密码
      "password_encoded": false,    // 设为true启用Base64解码
      "database": "xiuxing_db",     // 或Base64编码的数据库名
      "charset": "utf8mb4"
    },
    "pool": {
      "pool_size": 10,              // 连接池大小
      "max_overflow": 20,           // 最大溢出连接数
      "pool_timeout": 30,           // 获取连接超时时间(秒)
      "pool_recycle": 3600,         // 连接回收时间(秒)
      "pool_pre_ping": true         // 连接前ping检查
    }
  }
}
```

### SQLite配置

```json
{
  "database": {
    "type": "sqlite",
    "sqlite": {
      "path": "data/xiuxing.db"      // SQLite数据库文件路径
    }
  }
}
```

## 🚀 启动应用

### 开发环境

```bash
# 使用开发配置启动
python run.py

# 或设置环境变量
export FLASK_ENV=development
python run.py
```

### 生产环境

```bash
# 设置生产环境
export FLASK_ENV=production
python run.py

# 或使用Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

## 📊 配置管理API

### 获取配置信息（需登录）

```bash
GET /system/config
Authorization: 管理员登录状态
```

### 重新加载配置（需登录）

```bash
POST /system/config/reload
Authorization: 管理员登录状态
```

### 系统健康检查

```bash
GET /system/health
```

## 🔍 测试配置

使用内置的测试脚本验证配置：

```bash
python test_config.py
```

## 📝 配置优先级

1. 环境变量（最高优先级）
2. `config.json` 文件
3. 默认配置（最低优先级）

### 环境变量覆盖

```bash
# 数据库URL
export DATABASE_URL="mysql+pymysql://user:pass@host:port/db"

# 应用密钥
export SECRET_KEY="production-secret-key"

# JWT密钥
export JWT_SECRET_KEY="jwt-secret-key"

# 运行环境
export FLASK_ENV="production"
```

## 🛠️ 故障排除

### 常见问题

1. **Base64解码失败**
   - 检查编码字符串是否完整
   - 确保 `password_encoded` 设置正确

2. **数据库连接失败**
   - 验证主机名、端口、用户名、密码
   - 检查数据库服务是否运行
   - 确认防火墙设置

3. **配置文件未找到**
   - 确保 `config.json` 在应用根目录
   - 检查文件权限

### 调试模式

启用详细日志输出：

```json
{
  "logging": {
    "level": "DEBUG"
  },
  "development": {
    "enabled": true
  }
}
```

## 📈 性能优化

### 连接池调优

```json
{
  "database": {
    "pool": {
      "pool_size": 20,          // 根据并发量调整
      "max_overflow": 30,       // 高并发时的溢出连接
      "pool_timeout": 30,       // 适当的超时时间
      "pool_recycle": 1800,     // 30分钟回收连接
      "pool_pre_ping": true     // 确保连接有效性
    }
  }
}
```

### 监控连接池状态

```bash
# 获取连接池状态
curl http://localhost:5000/system/db-pool

# 重置连接池
curl -X POST http://localhost:5000/system/db-pool/reset
```

## 🔒 安全建议

1. **生产环境配置**：
   - 使用Base64编码敏感信息
   - 设置强密码
   - 限制CORS来源
   - 使用HTTPS

2. **文件权限**：
   ```bash
   chmod 600 config.json  # 仅所有者可读写
   ```

3. **环境变量**：
   - 生产环境使用环境变量覆盖敏感配置
   - 不要在代码中硬编码敏感信息

---

**南无阿弥陀佛** 🙏

*愿以此功德，回向万界众生*  
*愿众生离苦得乐，究竟解脱*