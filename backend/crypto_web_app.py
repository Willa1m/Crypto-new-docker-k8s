from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
import os
import threading
import schedule
import time
import pytz
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
from crypto_db import CryptoDatabase
from crypto_analyzer import CryptoAnalyzer
from simple_redis_manager import CryptoCacheManager
from logger_config import get_crypto_logger
# 导入后台处理模块
from data_processor import run_data_processing
from crypto_analyzer import run_analysis
from realtime_processor import run_realtime_processor_once
from kline_processor import run_kline_processing

# 配置日志
logger = get_crypto_logger(__name__)

class CryptoWebApp:
    def __init__(self):
        # 获取项目根目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 在Docker环境中，使用绝对路径
        if os.path.exists('/app/frontend/templates'):
            template_folder = '/app/frontend/templates'
            static_folder = '/app/frontend/static'
        else:
            # 本地开发环境
            project_root = os.path.dirname(current_dir)
            template_folder = os.path.join(project_root, 'frontend', 'templates')
            static_folder = os.path.join(project_root, 'frontend', 'static')
        
        self.app = Flask(__name__, 
                        template_folder=template_folder,
                        static_folder=static_folder)
        CORS(self.app)
        
        # 初始化限流器
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri="memory://"
        )
        
        self.db = CryptoDatabase()
        self.analyzer = CryptoAnalyzer()
        
        # 初始化Redis缓存管理器
        try:
            self.redis_manager = CryptoCacheManager()
            logger.info("Redis缓存管理器初始化成功")
        except Exception as e:
            logger.warning(f"Redis缓存管理器初始化失败: {e}")
            self.redis_manager = None
        
        # 初始化后台调度器
        self.is_running = False
        self.scheduler_thread = None
        
        self.setup_routes()
    
    def setup_routes(self):
        """设置路由"""
        # 页面路由
        self.app.route('/')(self.index)
        self.app.route('/bitcoin')(self.bitcoin)
        self.app.route('/ethereum')(self.ethereum)
        self.app.route('/kline')(self.kline)
        
        # API路由（带限流）
        self.app.route('/api/health', methods=['GET'])(self.api_health_check)
        self.app.route('/api/latest_prices')(self.limiter.limit("30 per minute")(self.api_latest_prices))
        self.app.route('/api/price_history')(self.limiter.limit("20 per minute")(self.api_price_history))
        self.app.route('/api/chart_data')(self.limiter.limit("20 per minute")(self.api_chart_data))
        self.app.route('/api/btc_chart')(self.api_btc_chart)
        self.app.route('/api/eth_chart')(self.api_eth_chart)
        self.app.route('/api/kline_chart')(self.api_kline_chart)
        self.app.route('/api/analysis')(self.limiter.limit("10 per minute")(self.api_analysis))
        self.app.route('/api/btc_data')(self.limiter.limit("15 per minute")(self.api_btc_data))
        self.app.route('/api/eth_data')(self.limiter.limit("15 per minute")(self.api_eth_data))
        self.app.route('/api/kline_data')(self.limiter.limit("10 per minute")(self.api_kline_data))
        self.app.route('/api/refresh_charts', methods=['POST'])(self.limiter.limit("5 per minute")(self.api_refresh_charts))
        self.app.route('/api/system/status')(self.api_system_status)
        
        # 缓存管理API
        self.app.route('/api/cache/stats')(self.api_cache_stats)
        self.app.route('/api/cache/clear', methods=['POST'])(self.api_clear_cache)
        
        # 错误处理
        self.app.errorhandler(404)(self.not_found)
        self.app.errorhandler(500)(self.internal_error)
        
        # 限流错误处理
        @self.app.errorhandler(429)
        def ratelimit_handler(e):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': '请求过于频繁，请稍后再试',
                'retry_after': getattr(e, 'retry_after', None)
            }), 429
    
    def process_chart_data(self, data, symbol):
        """处理图表数据，计算三条曲线：价格、成交量、波动率"""
        if not data:
            return {
                'price_data': [],
                'volume_data': [],
                'volatility_data': []
            }
        
        # 过滤指定symbol的数据
        filtered_data = [item for item in data if item['symbol'] == symbol]
        
        if not filtered_data:
            return {
                'price_data': [],
                'volume_data': [],
                'volatility_data': []
            }
        
        # 按时间排序
        filtered_data.sort(key=lambda x: x['date'])
        
        # 准备三条曲线的数据
        price_data = []
        volume_data = []
        volatility_data = []
        
        # 计算移动平均和波动率的窗口大小
        window_size = min(10, len(filtered_data))
        
        for i, item in enumerate(filtered_data):
            # 价格数据
            price_data.append({
                'date': item['date'],
                'timestamp_ms': item.get('timestamp_ms'),
                'price': item['close'],
                'high': item['high'],
                'low': item['low'],
                'open': item['open']
            })
            
            # 成交量数据
            volume_data.append({
                'date': item['date'],
                'timestamp_ms': item.get('timestamp_ms'),
                'volume': item['volume']
            })
            
            # 计算波动率（使用滑动窗口）
            if i >= window_size - 1:
                # 获取窗口内的价格数据
                window_prices = [filtered_data[j]['close'] for j in range(i - window_size + 1, i + 1)]
                
                # 计算标准差作为波动率
                mean_price = sum(window_prices) / len(window_prices)
                variance = sum((price - mean_price) ** 2 for price in window_prices) / len(window_prices)
                volatility = variance ** 0.5
                
                volatility_data.append({
                    'date': item['date'],
                    'timestamp_ms': item.get('timestamp_ms'),
                    'volatility': volatility,
                    'volatility_percent': (volatility / mean_price) * 100 if mean_price > 0 else 0
                })
        
        return {
            'price_data': price_data,
            'volume_data': volume_data,
            'volatility_data': volatility_data
        }
    
    def calculate_24h_change(self, symbol, current_price, connection):
        """基于历史数据计算24小时变化"""
        try:
            # 获取24小时前的价格数据（从hour_data表获取24小时前的数据）
            query = """
            SELECT close_price 
            FROM hour_data 
            WHERE symbol = %s 
            AND date <= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY date DESC 
            LIMIT 1
            """
            
            cursor = connection.cursor()
            cursor.execute(query, (symbol,))
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0]:
                price_24h_ago = float(result[0])
                # 计算24小时变化百分比: (当前价格 - 24小时前价格) / 24小时前价格 * 100
                change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
                logger.info(f"{symbol}: 当前价格 ${current_price:.2f}, 24h前价格 ${price_24h_ago:.2f}, 计算变化 {change_24h:.2f}%")
                return change_24h
            else:
                logger.warning(f"{symbol}: 没有找到24小时前的价格数据，使用API提供的变化值")
                return None
                
        except Exception as e:
            logger.error(f"计算{symbol}的24小时变化时出错: {str(e)}")
            return None

    def get_latest_prices(self):
        """从缓存或数据库获取最新价格"""
        # 首先尝试从Redis缓存获取
        if self.redis_manager:
            try:
                cached_prices = self.redis_manager.get_latest_prices()
                if cached_prices:
                    logger.info("从Redis缓存获取最新价格数据")
                    return cached_prices
                else:
                    logger.info("Redis缓存中没有最新价格数据，从数据库获取")
            except Exception as e:
                logger.warning(f"从Redis缓存获取价格数据失败: {e}")
        
        # 从数据库获取数据
        connection = None
        try:
            # 从连接池获取连接
            connection = self.db.get_connection()
            if not connection:
                logger.error("数据库连接失败")
                return []
            
            # 使用连接获取数据
            data = self.db.get_latest_prices(connection=connection)
            
            if not data or len(data) == 0:
                logger.warning("数据库中没有价格数据")
                return []
            
            # 转换数据格式并重新计算24小时变化
            result = []
            for item in data:
                name, symbol, price, api_change_24h, timestamp = item
                current_price = float(price)
                
                # 尝试基于历史数据计算24小时变化
                calculated_change = self.calculate_24h_change(symbol, current_price, connection)
                
                # 如果计算成功，使用计算值；否则使用API提供的值
                change_24h = calculated_change if calculated_change is not None else (float(api_change_24h) if api_change_24h is not None else 0.0)
                
                result.append({
                    'name': name,
                    'symbol': symbol,
                    'price': current_price,
                    'change_24h': change_24h,
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(timestamp, 'strftime') else str(timestamp)
                })
            
            # 将数据缓存到Redis（缓存60秒）
            if self.redis_manager and result:
                try:
                    self.redis_manager.cache_latest_prices(result)
                    logger.info("最新价格数据已缓存到Redis")
                except Exception as e:
                    logger.warning(f"缓存价格数据到Redis失败: {e}")
            
            return result
        except Exception as e:
            logger.error(f"获取最新价格时出错: {str(e)}")
            return []
        finally:
            # 确保连接被正确释放回连接池
            if connection:
                try:
                    connection.close()
                except:
                    pass
    

    
    def get_chart_data(self, timeframe, symbol=None, limit=100):
        """从缓存或数据库获取图表数据"""
        # 首先尝试从Redis缓存获取
        if self.redis_manager and symbol:
            try:
                cached_data = self.redis_manager.get_chart_data(symbol, timeframe)
                if cached_data:
                    logger.info(f"从Redis缓存获取{symbol}的{timeframe}图表数据")
                    return cached_data
                else:
                    logger.info(f"Redis缓存中没有{symbol}的{timeframe}图表数据，从数据库获取")
            except Exception as e:
                logger.warning(f"从Redis缓存获取图表数据失败: {e}")
        
        # 从数据库获取数据
        try:
            if not symbol:
                logger.warning("未指定symbol，无法获取图表数据")
                return []
            
            # 直接使用数据库的get_chart_data方法，它已经包含了时间戳处理逻辑
            if self.db.connect():
                data = self.db.get_chart_data(symbol, timeframe)
                self.db.disconnect()
                
                if not data or len(data) == 0:
                    logger.warning(f"数据库中没有{symbol}的{timeframe}级数据")
                    return []
                
                # 数据库已经返回了正确格式的数据，包含timestamp_ms字段
                result = []
                for item in data:
                    result.append({
                        'symbol': symbol,
                        'date': item['date'],
                        'timestamp_ms': item['timestamp_ms'],
                        'open': item['open'],
                        'high': item['high'],
                        'low': item['low'],
                        'close': item['close'],
                        'volume': item['volume']
                    })
                
                # 将数据缓存到Redis（缓存5分钟）
                if self.redis_manager and result:
                    try:
                        self.redis_manager.cache_chart_data(symbol, timeframe, result)
                        logger.info(f"{symbol}的{timeframe}图表数据已缓存到Redis")
                    except Exception as e:
                        logger.warning(f"缓存图表数据到Redis失败: {e}")
                
                return result
            else:
                logger.error("数据库连接失败")
                return []
        except Exception as e:
            logger.error(f"获取图表数据时出错: {str(e)}")
            return []
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        if not self.redis_manager:
            return {
                'status': 'disabled',
                'message': 'Redis缓存未启用'
            }
        
        try:
            stats = self.redis_manager.get_cache_stats()
            return {
                'status': 'active',
                'stats': stats
            }
        except Exception as e:
            logger.error(f"获取缓存统计信息失败: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def clear_cache(self, cache_type=None):
        """清理缓存"""
        if not self.redis_manager:
            return {
                'success': False,
                'message': 'Redis缓存未启用'
            }
        
        try:
            if cache_type == 'prices':
                # 清理价格缓存
                result = self.redis_manager.clear_price_cache()
            elif cache_type == 'charts':
                # 清理图表缓存
                result = self.redis_manager.clear_chart_cache()
            else:
                # 清理所有缓存
                result = self.redis_manager.clear_all_cache()
            
            return {
                'success': True,
                'cleared_keys': result,
                'message': f'成功清理{cache_type or "所有"}缓存'
            }
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    # 路由处理函数
    def index(self):
        """主页"""
        return render_template('index.html')
    
    def bitcoin(self):
        """比特币页面"""
        return render_template('bitcoin.html')
    
    def ethereum(self):
        """以太坊页面"""
        return render_template('ethereum.html')
    
    def kline(self):
        """K线图页面"""
        return render_template('kline.html')
    
    def api_health_check(self):
        """健康检查端点"""
        return jsonify({'status': 'healthy', 'timestamp': datetime.now(pytz.UTC).isoformat()})
    
    def api_latest_prices(self):
        """获取最新价格API"""
        try:
            # 先从缓存获取
            if self.redis_manager:
                btc_price = self.redis_manager.get_price('BTC')
                eth_price = self.redis_manager.get_price('ETH')
                
                if btc_price and eth_price:
                    return jsonify({'success': True, 'data': [btc_price, eth_price]})
            
            # 从数据库获取
            prices = self.get_latest_prices()
            return jsonify({
                'success': True,
                'data': prices
            })
        except Exception as e:
            logger.error(f"获取最新价格失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def api_price_history(self):
        """获取价格历史"""
        try:
            crypto = request.args.get('crypto', 'BTC')
            timeframe = request.args.get('timeframe', '24h')
            
            # 从数据库获取价格历史
            if self.db.connect():
                history = self.db.get_price_history(crypto, timeframe)
                self.db.disconnect()
                return jsonify({'success': True, 'data': history if history else []})
            else:
                return jsonify({'success': False, 'error': '数据库连接失败'}), 500
        except Exception as e:
            logger.error(f"获取价格历史失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def api_chart_data(self):
        """API: 获取图表数据"""
        try:
            timeframe = request.args.get('timeframe', 'hour')
            symbol = request.args.get('symbol')
            limit = int(request.args.get('limit', 100))
            
            data = self.get_chart_data(timeframe, symbol, limit)
            return jsonify({
                'success': True,
                'data': data
            })
        except Exception as e:
            logger.error(f"API获取图表数据时出错: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def api_btc_chart(self):
        """获取BTC图表数据"""
        try:
            timeframe = request.args.get('timeframe', 'hour')
            limit = int(request.args.get('limit', 100))
            chart_data = self.get_chart_data(timeframe, 'BTC', limit)
            return jsonify({'success': True, 'data': chart_data})
        except Exception as e:
            logger.error(f"获取BTC图表数据失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def api_eth_chart(self):
        """获取ETH图表数据"""
        try:
            timeframe = request.args.get('timeframe', 'hour')
            limit = int(request.args.get('limit', 100))
            chart_data = self.get_chart_data(timeframe, 'ETH', limit)
            return jsonify({'success': True, 'data': chart_data})
        except Exception as e:
            logger.error(f"获取ETH图表数据失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def api_kline_chart(self):
        """获取K线图表数据"""
        try:
            symbol = request.args.get('symbol', 'BTC')
            timeframe = request.args.get('timeframe', 'hour')
            
            if self.db.connect():
                kline_data = self.db.get_kline_data(symbol, timeframe)
                self.db.disconnect()
                return jsonify({'success': True, 'data': kline_data if kline_data else []})
            else:
                return jsonify({'success': False, 'error': '数据库连接失败'}), 500
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def api_analysis(self):
        """获取分析报告"""
        try:
            if self.db.connect():
                analysis_data = self.db.get_analysis_data()
                self.db.disconnect()
                return jsonify({'success': True, 'data': analysis_data if analysis_data else {}})
            else:
                return jsonify({'success': False, 'error': '数据库连接失败'}), 500
        except Exception as e:
            logger.error(f"获取分析数据失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def api_system_status(self):
        """获取系统状态"""
        try:
            # 检查数据库连接
            db_status = 'disconnected'
            if self.db:
                try:
                    if self.db.connect():
                        db_status = 'connected'
                        self.db.disconnect()
                except Exception:
                    db_status = 'disconnected'
            
            # 检查Redis连接
            redis_status = 'disconnected'
            if self.redis_manager:
                try:
                    # 检查Redis管理器是否有有效连接
                    if hasattr(self.redis_manager, 'redis') and self.redis_manager.redis:
                        self.redis_manager.redis.ping()
                        redis_status = 'connected'
                except Exception:
                    redis_status = 'disconnected'
            
            status = {
                'database': db_status,
                'redis': redis_status,
                'timestamp': datetime.now(pytz.UTC).isoformat()
            }
            return jsonify({'success': True, 'data': status})
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def not_found(self, error):
        """404错误处理"""
        return jsonify({'error': 'Not Found', 'message': 'The requested resource was not found'}), 404
    
    def internal_error(self, error):
        """500错误处理"""
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal Server Error', 'message': 'An internal error occurred'}), 500
    
    def api_btc_data(self):
        """API: 获取比特币数据（三条曲线）"""
        try:
            timeframe = request.args.get('timeframe', 'hour')
            limit = int(request.args.get('limit', 100))
            
            # 获取原始数据
            raw_data = self.get_chart_data(timeframe, 'BTC', limit)
            
            # 处理数据，生成三条曲线
            processed_data = self.process_chart_data(raw_data, 'BTC')
            
            return jsonify({
                'success': True,
                'data': processed_data
            })
        except Exception as e:
            logger.error(f"API获取比特币数据时出错: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def api_eth_data(self):
        """API: 获取以太坊数据（三条曲线）"""
        try:
            timeframe = request.args.get('timeframe', 'hour')
            limit = int(request.args.get('limit', 100))
            
            # 获取原始数据
            raw_data = self.get_chart_data(timeframe, 'ETH', limit)
            
            # 处理数据，生成三条曲线
            processed_data = self.process_chart_data(raw_data, 'ETH')
            
            return jsonify({
                'success': True,
                'data': processed_data
            })
        except Exception as e:
            logger.error(f"API获取以太坊数据时出错: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def api_refresh_charts(self):
        """API: 刷新图表"""
        try:
            # 运行分析器生成新的图表
            self.analyzer.run_analysis()
            
            return jsonify({
                'success': True,
                'message': '图表已刷新'
            })
        except Exception as e:
            logger.error(f"API刷新图表时出错: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def api_cache_stats(self):
        """API: 获取缓存统计信息"""
        try:
            stats = self.get_cache_stats()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"API获取缓存统计信息时出错: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def api_clear_cache(self):
        """API: 清理缓存"""
        try:
            cache_type = request.json.get('type') if request.json else None
            result = self.clear_cache(cache_type)
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 400
        except Exception as e:
            logger.error(f"API清理缓存时出错: {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        try:
            if not self.redis_manager:
                return {
                    'status': 'error',
                    'message': 'Redis管理器未初始化'
                }
            
            stats = self.redis_manager.get_cache_stats()
            return {
                'status': 'success',
                'data': stats
            }
        except Exception as e:
            logger.error(f"获取缓存统计信息失败: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def clear_cache(self, cache_type=None):
        """清理缓存"""
        try:
            if not self.redis_manager:
                return {
                    'success': False,
                    'message': 'Redis管理器未初始化'
                }
            
            if cache_type == 'all' or cache_type is None:
                # 清理所有缓存
                success = self.redis_manager.clear_all_cache()
                if success:
                    return {
                        'success': True,
                        'message': '所有缓存已清理'
                    }
                else:
                    return {
                        'success': False,
                        'message': '清理缓存失败'
                    }
            else:
                return {
                    'success': False,
                    'message': f'不支持的缓存类型: {cache_type}'
                }
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    

    
    def api_kline_data(self):
        """API: 获取K线数据"""
        try:
            from kline_backend import kline_backend
            
            symbol = request.args.get('symbol', 'BTC')
            timeframe = request.args.get('timeframe', 'hour')
            limit = int(request.args.get('limit', 100))
            
            # 使用新的后端处理模块获取数据
            data = kline_backend.get_kline_data_with_indicators(symbol, timeframe, limit)
            
            return jsonify({
                'success': True,
                'data': data
            })
        except Exception as e:
            logger.error(f"API获取K线数据时出错: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def schedule_tasks(self):
        """设置定时任务"""
        logger.info("设置定时任务")
        
        # 每2分钟运行一次数据收集
        schedule.every(2).minutes.do(self.run_data_collection_task)
        
        # 每30秒运行一次实时数据处理
        schedule.every(30).seconds.do(self.run_realtime_task)
        
        # 每小时运行一次分析
        schedule.every().hour.do(self.run_analysis_task)
        
        # 每天凌晨2点运行完整处理
        schedule.every().day.at("02:00").do(self.run_full_processing)
        
        logger.info("定时任务设置完成")
    
    def run_realtime_task(self):
        """运行实时数据处理任务"""
        logger.info("执行实时数据处理任务")
        try:
            if run_realtime_processor_once():
                logger.info("实时数据处理任务完成")
            else:
                logger.error("实时数据处理任务失败")
        except Exception as e:
            logger.error(f"实时数据处理任务异常: {str(e)}")
    
    def run_data_collection_task(self):
        """运行数据收集任务"""
        logger.info("执行定时数据收集任务")
        try:
            if run_data_processing():
                logger.info("定时数据收集任务完成")
            else:
                logger.error("定时数据收集任务失败")
        except Exception as e:
            logger.error(f"定时数据收集任务异常: {str(e)}")
    
    def run_analysis_task(self):
        """运行分析任务"""
        logger.info("执行定时分析任务")
        try:
            if run_analysis():
                logger.info("定时分析任务完成")
            else:
                logger.error("定时分析任务失败")
        except Exception as e:
            logger.error(f"定时分析任务异常: {str(e)}")
    
    def run_full_processing(self):
        """运行完整处理流程"""
        logger.info("执行完整处理流程")
        try:
            # 数据处理
            if run_data_processing():
                logger.info("完整数据处理完成")
            else:
                logger.error("完整数据处理失败")
            
            # 分析报告
            if run_analysis():
                logger.info("完整分析报告生成完成")
            else:
                logger.error("完整分析报告生成失败")
                
        except Exception as e:
            logger.error(f"完整处理流程异常: {str(e)}")
    
    def run_scheduler(self):
        """运行调度器"""
        logger.info("启动任务调度器")
        self.is_running = True
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # 每30秒检查一次
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在停止系统...")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"调度器运行异常: {str(e)}")
                time.sleep(60)  # 出错后等待1分钟再继续
    
    def start_background_scheduler(self):
        """启动后台调度器"""
        if not self.scheduler_thread or not self.scheduler_thread.is_alive():
            self.schedule_tasks()
            self.scheduler_thread = threading.Thread(target=self.run_scheduler)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            logger.info("后台调度器已启动")
        else:
            logger.info("后台调度器已在运行中")
    
    def stop_background_scheduler(self):
        """停止后台调度器"""
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
            logger.info("后台调度器已停止")
    
    def get_local_ip(self):
        """获取本机局域网IP地址"""
        try:
            import socket
            # 创建一个UDP socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 连接到一个远程地址（不会真正发送数据）
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    def run(self, debug=True, host='0.0.0.0', port=5000, enable_scheduler=True):
        """运行应用"""
        local_ip = self.get_local_ip()
        
        print("\n" + "="*60)
        print("🚀 加密货币监控系统 - Web服务器已启动")
        print("="*60)
        print(f"📍 本地访问地址: http://127.0.0.1:{port}")
        print(f"🌐 局域网访问地址: http://{local_ip}:{port}")
        print(f"📱 手机访问地址: http://{local_ip}:{port}")
        print("\n💡 让其他人访问的方法:")
        print(f"   1. 同一局域网用户可直接访问: http://{local_ip}:{port}")
        print(f"   2. 手机连接同一WiFi后访问: http://{local_ip}:{port}")
        print("   3. 外网访问需要配置路由器端口转发")
        
        if enable_scheduler:
            print("\n🔄 后台服务状态:")
            print("   ✅ 实时数据处理: 每30秒执行")
            print("   ✅ 数据收集任务: 每5分钟执行")
            print("   ✅ 分析任务: 每小时执行")
            print("   ✅ 完整处理: 每天凌晨2点执行")
        
        print("="*60)
        
        logger.info(f"启动Web应用，本地地址: http://127.0.0.1:{port}")
        logger.info(f"启动Web应用，局域网地址: http://{local_ip}:{port}")
        
        # 启动后台调度器
        if enable_scheduler:
            self.start_background_scheduler()
        
        try:
            self.app.run(debug=debug, host=host, port=port)
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止系统...")
        finally:
            if enable_scheduler:
                self.stop_background_scheduler()

# 创建全局应用实例，供其他模块导入
crypto_app = CryptoWebApp()
app = crypto_app.app  # Flask 应用对象

if __name__ == '__main__':
    crypto_app.run(debug=False, host='0.0.0.0', port=8000)