# 📁 项目结构整理说明

## 🎯 整理目标
将原本散乱的文件按功能分类，提高项目的可维护性和可读性。

## 📂 新的文件夹结构

### 📋 核心业务逻辑 (`core/`)
- `crypto_analyzer.py` - 加密货币分析器
- `crypto_db.py` - 数据库操作
- `crypto_db_backup.py` - 数据库备份
- `crypto_scraper.py` - 数据爬虫
- `crypto_web_app.py` - Web应用主程序
- `data_processor.py` - 数据处理器
- `kline_backend.py` - K线后端服务
- `kline_processor.py` - K线数据处理
- `main.py` - 主程序入口
- `simple_redis_manager.py` - Redis管理器

### 🚀 部署相关 (`deployment/`)
- `Dockerfile.*` - 各服务的Docker文件
- `docker-compose.yml` - Docker编排文件
- `deploy-k3s.sh` - K3s部署脚本
- `k3d.exe` - K3d工具
- `k8s/` - Kubernetes配置文件
- `nginx/` - Nginx配置和脚本

### 📚 文档 (`docs/`)
- `README.md` - 项目说明
- `PROJECT_STRUCTURE.md` - 项目结构说明
- `DEPLOYMENT.md` - 部署文档
- `SECURITY.md` - 安全文档
- `Cloudflare_Tunnel_成功指南.md` - Cloudflare隧道指南
- `guides/` - 详细指南文档

### 🔧 脚本工具 (`scripts/`)
- `build-and-push.bat` - Windows构建推送脚本
- `build-and-push.sh` - Linux构建推送脚本
- `cloudflare_tunnel.py` - Cloudflare隧道脚本
- `network_stress_test.py` - 网络压力测试

### ⚙️ 配置文件 (`config/`)
- `.env.example` - 环境变量示例
- `.gitignore` - Git忽略文件
- `requirements.txt` - Python依赖

### 💾 数据存储 (`data/`)
- `kline_data/` - K线数据文件
- `mysql/` - MySQL数据目录
- `redis/` - Redis数据目录

### 🧪 测试文件 (`tests/`)
- `stress_tests/` - 压力测试相关文件

### 📝 日志文件 (`logs/`)
- `*.log` - 各种系统日志文件

### 🌐 前端资源 (保持原位置)
- `frontend/` - 前端源码
- `static/` - 静态资源
- `templates/` - 模板文件
- `backend/` - 后端API

## 🎉 整理效果

### ✅ 优点：
1. **清晰的功能分类** - 每个文件夹都有明确的用途
2. **便于维护** - 相关文件集中管理
3. **易于查找** - 按功能快速定位文件
4. **规范化结构** - 符合项目开发最佳实践

### 📋 使用建议：
1. 开发时主要关注 `core/` 文件夹
2. 部署时查看 `deployment/` 文件夹
3. 文档查阅在 `docs/` 文件夹
4. 配置修改在 `config/` 文件夹
5. 测试相关在 `tests/` 文件夹

## 🔄 后续维护
- 新增功能文件放入对应的功能文件夹
- 定期清理 `logs/` 文件夹中的旧日志
- 保持文件夹结构的一致性