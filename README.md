# 🚀 Crypto Monitoring Plus - 企业级加密货币监控系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0-red.svg)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 一个功能完整的企业级加密货币实时监控和分析系统，采用前后端一体化架构，提供实时价格追踪、技术指标分析和交互式图表展示。

## 📋 目录

- [✨ 功能特性](#-功能特性)
- [🏗️ 系统架构](#️-系统架构)
- [🚀 快速开始](#-快速开始)
- [📦 安装部署](#-安装部署)
- [⚙️ 配置说明](#️-配置说明)
- [🎯 使用指南](#-使用指南)
- [📚 API文档](#-api文档)
- [🔧 开发指南](#-开发指南)
- [📁 项目结构](#-项目结构)
- [🔄 更新日志](#-更新日志)
- [📄 许可证](#-许可证)

## ✨ 功能特性

### 🔥 核心功能
- **实时价格监控**: 支持Bitcoin (BTC)、Ethereum (ETH)等主流加密货币
- **多时间维度数据**: 分钟级、小时级、日级数据采集和存储
- **技术指标分析**: 移动平均线、RSI、MACD、布林带等技术指标
- **交互式图表**: 基于Chart.js的高性能K线图和价格走势图
- **实时数据推送**: 自动数据更新机制
- **智能缓存**: Redis缓存机制，提升数据访问速度

### 🌐 Web界面特性
- **响应式设计**: 完美支持桌面、平板和移动设备
- **现代化UI**: 采用现代化设计语言，用户体验优秀
- **多页面支持**: 主页、比特币详情、以太坊详情、K线分析页面
- **实时更新**: 无需刷新页面即可获取最新数据
- **数据一致性**: 所有图表数据完全同步，确保信息准确性

### 🔧 技术特性
- **前后端一体化**: Flask提供API和页面服务
- **高性能数据库**: MySQL存储历史数据，Redis缓存热点数据
- **数据同步保证**: 统一的数据查询机制，确保所有图表显示一致
- **API参数化**: 支持动态时间框架和数据量控制
- **错误处理**: 完善的异常处理和日志记录
- **扩展性**: 易于添加新的加密货币和数据源

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Flask Web Application                        │
│                 (crypto_web_app.py:8000)                       │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │    Frontend Pages   │    │         Backend API             │ │
│  │  - 主页 (/)         │    │  - /api/latest_prices           │ │
│  │  - 比特币 (/bitcoin)│    │  - /api/chart_data              │ │
│  │  - 以太坊 (/ethereum)│   │  - /api/btc_chart               │ │
│  │  - K线图 (/kline)   │    │  - /api/eth_chart               │ │
│  └─────────────────────┘    │  - /api/kline_data              │ │
│                              └─────────────────────────────────┘ │
└─────────────────┬───────────────────────┬───────────────────────┘
                  │                       │
                  ▼                       ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│        Redis 缓存           │ │       MySQL 数据库          │
│    - 实时数据缓存           │ │    - 历史数据存储           │
│    - 图表数据缓存           │ │    - 分钟/小时级数据        │
│    - 性能优化               │ │    - 统一排序机制           │
└─────────────────────────────┘ └─────────────────────────────┘
                  │                       │
                  └───────────┬───────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │      外部数据源             │
                │    - CoinDesk API           │
                │    - Binance API            │
                │    - 定时数据采集           │
                └─────────────────────────────┘
```

## 🚀 快速开始

### 前置要求
- Python 3.8+
- MySQL 8.0+
- Redis 7.0+
- 4GB+ 可用内存

### 一键启动
```bash
# 1. 克隆项目
git clone <repository-url>
cd Crypto_Upgrade

# 2. 进入后端目录
cd backend

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库和Redis连接

# 5. 启动服务
python crypto_web_app.py

# 6. 访问应用
# 主页: http://localhost:8000
# API文档: http://localhost:8000/api/health
```

### 验证部署
```bash
# 检查服务状态
curl http://localhost:8000/api/health

# 测试API连接
curl http://localhost:8000/api/latest_prices

# 访问页面
# 主页: http://localhost:8000/
# 比特币: http://localhost:8000/bitcoin
# 以太坊: http://localhost:8000/ethereum
# K线图: http://localhost:8000/kline
```

## 📦 安装部署

### 环境配置
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 数据库配置
```sql
-- 创建数据库
CREATE DATABASE crypto_monitoring CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'crypto_user'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON crypto_monitoring.* TO 'crypto_user'@'%';
FLUSH PRIVILEGES;
```

### Redis配置
```bash
# 启动Redis服务
redis-server

# 测试Redis连接
redis-cli ping
```

## ⚙️ 配置说明

### 环境变量配置 (.env)
```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=crypto_monitoring
DB_USER=crypto_user
DB_PASSWORD=your_password

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# API配置
COINDESK_API_URL=https://api.coindesk.com/v1/bpi/currentprice.json
BINANCE_API_URL=https://api.binance.com/api/v3/ticker/price

# 系统配置
FLASK_ENV=production
LOG_LEVEL=INFO
DATA_UPDATE_INTERVAL=60
CACHE_TTL=300
```

## 🎯 使用指南

### Web界面使用

#### 主页功能 (/)
- **实时价格展示**: 显示BTC和ETH的实时价格
- **价格变化趋势**: 24小时价格变化百分比
- **快速导航**: 快速访问各个功能模块

#### 比特币详情页 (/bitcoin)
- **价格历史图表**: 可选择不同时间周期的价格走势
- **技术指标分析**: 移动平均线等技术指标
- **交易量分析**: 成交量变化趋势

#### 以太坊详情页 (/ethereum)
- **ETH专用图表**: 以太坊价格和技术指标
- **对比分析**: 与比特币的对比数据

#### K线分析页 (/kline)
- **交互式K线图**: 支持缩放、平移操作
- **多时间周期**: 分钟、小时、日线数据
- **技术指标叠加**: 可在图表上叠加多种技术指标

### API使用示例

#### 获取实时价格
```bash
curl -X GET "http://localhost:8000/api/latest_prices" \
     -H "Content-Type: application/json"
```

#### 获取图表数据
```bash
# 获取BTC分钟级数据
curl -X GET "http://localhost:8000/api/chart_data?symbol=BTC&timeframe=minute&limit=100" \
     -H "Content-Type: application/json"

# 获取BTC小时级数据
curl -X GET "http://localhost:8000/api/btc_chart?timeframe=hour&limit=24" \
     -H "Content-Type: application/json"
```

#### 获取K线数据
```bash
curl -X GET "http://localhost:8000/api/kline_data?symbol=BTC&timeframe=minute&limit=100" \
     -H "Content-Type: application/json"
```

## 📚 API文档

### 端点列表

#### 页面路由
| 路由 | 方法 | 描述 | 模板 |
|------|------|------|------|
| `/` | GET | 主页 | `templates/index.html` |
| `/bitcoin` | GET | 比特币详情页 | `templates/bitcoin.html` |
| `/ethereum` | GET | 以太坊详情页 | `templates/ethereum.html` |
| `/kline` | GET | K线图页面 | `templates/kline.html` |

#### API路由
| 路由 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/api/health` | GET | 健康检查 | 无 |
| `/api/latest_prices` | GET | 最新价格 | 无 |
| `/api/chart_data` | GET | 图表数据 | `symbol`, `timeframe`, `limit` |
| `/api/btc_chart` | GET | BTC图表 | `timeframe`, `limit` |
| `/api/eth_chart` | GET | ETH图表 | `timeframe`, `limit` |
| `/api/kline_data` | GET | K线数据 | `symbol`, `timeframe`, `limit` |

### 响应格式
```json
{
  "success": true,
  "data": {
    "symbol": "BTC",
    "price": 115611.85,
    "change_24h": 0.38,
    "timestamp_ms": 1755599280000,
    "date": "2025-08-19T18:25:00+00:00"
  },
  "message": "Success"
}
```

## 🔧 开发指南

### 项目结构
```
Crypto_Upgrade/
├── backend/                    # 后端服务
│   ├── crypto_web_app.py      # 主应用程序
│   ├── crypto_db.py           # 数据库操作
│   ├── crypto_scraper.py      # 数据采集
│   ├── crypto_analyzer.py     # 技术分析
│   ├── data_processor.py      # 数据处理
│   ├── requirements.txt       # Python依赖
│   └── .env.example           # 环境变量示例
├── frontend/                   # 前端资源
│   ├── static/                # 静态文件
│   │   ├── css/              # 样式文件
│   │   ├── js/               # JavaScript文件
│   │   └── icons/            # 图标资源
│   └── templates/             # HTML模板
│       ├── index.html        # 主页
│       ├── bitcoin.html      # 比特币页面
│       ├── ethereum.html     # 以太坊页面
│       └── kline.html        # K线图页面
├── logs/                      # 日志文件
├── docs/                      # 文档
└── README.md                  # 项目说明
```

### 添加新功能

#### 添加新的加密货币
```python
# 1. 在 crypto_scraper.py 中添加数据源
def get_new_crypto_price(self):
    # 实现新币种价格获取逻辑
    pass

# 2. 在 crypto_web_app.py 中添加API端点
@app.route('/api/new_crypto_chart', methods=['GET'])
def api_new_crypto_chart():
    # 实现新币种图表API
    pass

# 3. 在前端添加页面和图表
# 创建 templates/new_crypto.html
# 添加相应的JavaScript逻辑
```

### 测试指南
```bash
# 运行基本测试
python -m pytest tests/

# 测试API端点
curl http://localhost:8000/api/health

# 测试页面访问
curl http://localhost:8000/
```

## 🔄 更新日志

### v2.1.0 (2025-08-20)
#### 🚀 重大更新
- **数据同步问题修复**: 解决了K线图与其他图表数据不一致的问题
- **API参数化**: `api_btc_chart`和`api_eth_chart`现在支持动态时间框架
- **数据库查询优化**: 统一使用`ORDER BY date DESC`确保获取最新数据

#### 🔧 技术改进
- 修复`crypto_db.py`中`get_chart_data`和`get_kline_data`方法
- 修复`crypto_web_app.py`中图表API的硬编码问题
- 所有API端点现在返回一致的时间戳(1755599280000)

#### ✅ 验证结果
- 所有图表显示一致的最新数据(2025-08-19 18:25:00)
- API响应时间优化
- 数据准确性得到保证

#### 🐛 已知问题
- `/favicon.ico` 返回404错误 (计划在下个版本修复)

### v2.0.0 (2025-01-18)
#### 🎉 初始版本
- 实现基础的加密货币监控功能
- 支持BTC和ETH价格追踪
- 提供Web界面和API服务
- 集成Redis缓存和MySQL存储

## 📞 联系我们

- **项目仓库**: [GitHub Repository]
- **问题反馈**: [Issues]
- **技术支持**: [Support Email]

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

感谢以下开源项目和服务：
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Chart.js](https://www.chartjs.org/) - 图表库
- [MySQL](https://www.mysql.com/) - 数据库
- [Redis](https://redis.io/) - 缓存系统
- [CoinDesk API](https://www.coindesk.com/api) - 价格数据源

---

<div align="center">
  <p>如果这个项目对您有帮助，请给我们一个 ⭐️</p>
  <p>Made with ❤️ by the Crypto Monitoring Team</p>
</div>