import mysql.connector
from mysql.connector import pooling
import os
from datetime import datetime
from timestamp_manager import get_timestamp_manager
import pandas as pd
import time
import os
from logger_config import get_crypto_logger

# 配置日志
logger = get_crypto_logger('database')

class CryptoDatabase:
    def __init__(self):
        """初始化数据库连接池"""
        self.pool_config = {
            'pool_name': 'crypto_pool',
            'pool_size': 3,
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'crypto_user'),
            'password': os.getenv('DB_PASSWORD', 'crypto_pass_2024'),
            'database': os.getenv('DB_NAME', 'crypto_monitoring'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'charset': 'utf8mb4',
            'autocommit': True,
            'use_unicode': True,
            'time_zone': '+00:00'  # 设置数据库连接使用UTC时区
        }
        
        self.connection_pool = None
        self.connection = None
        self.cursor = None
        self.timestamp_manager = get_timestamp_manager()
        
        # 初始化连接池
        self._init_connection_pool()
    
    def _init_connection_pool(self):
        """初始化连接池"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 先尝试关闭现有连接池
                if self.connection_pool:
                    try:
                        # 关闭连接池中的所有连接
                        for _ in range(self.pool_config['pool_size']):
                            try:
                                conn = self.connection_pool.get_connection()
                                if conn.is_connected():
                                    conn.close()
                            except:
                                pass
                    except:
                        pass
                    self.connection_pool = None
                
                # 创建新的连接池
                self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(**self.pool_config)
                logger.info("数据库连接池初始化成功")
                return True
                
            except mysql.connector.Error as err:
                logger.error(f"连接池初始化失败 (尝试 {attempt + 1}/{max_retries}): {err}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    self.connection_pool = None
                    return False
            except Exception as e:
                logger.error(f"连接池初始化异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.connection_pool = None
                    return False
        
        return False
        # 不抛出异常，允许应用程序继续运行
    
    def get_connection(self):
        """从连接池获取连接，带重试机制"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if not self.connection_pool:
                    logger.warning("连接池未初始化，尝试重新初始化")
                    if not self._init_connection_pool():
                        logger.error("连接池重新初始化失败")
                        return None
                
                connection = self.connection_pool.get_connection()
                
                # 健康检查
                if connection and connection.is_connected():
                    try:
                        connection.ping(reconnect=True, attempts=3, delay=1)
                        return connection
                    except mysql.connector.Error:
                        if connection:
                            connection.close()
                        continue
                else:
                    if connection:
                        connection.close()
                    continue
                        
            except mysql.connector.Error as err:
                logger.warning(f"获取连接失败 (尝试 {attempt + 1}/{max_retries}): {err}")
                if "Too many connections" in str(err):
                    # 如果是连接过多错误，等待更长时间
                    time.sleep(retry_delay * 3)
                    # 尝试重新初始化连接池
                    if attempt == max_retries - 1:
                        logger.info("尝试重新初始化连接池以解决连接过多问题")
                        self._init_connection_pool()
                else:
                    time.sleep(retry_delay)
                
                if attempt < max_retries - 1:
                    retry_delay *= 2
                    
            except Exception as e:
                logger.warning(f"获取连接异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
        
        logger.error("无法获取数据库连接")
        return None
    
    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = self.get_connection()
            if self.connection is None:
                logger.error("无法获取数据库连接")
                return False
            self.cursor = self.connection.cursor(buffered=True)
            logger.info("成功连接到 MariaDB 数据库")
            return True
        except mysql.connector.Error as err:
            logger.error(f"数据库连接错误: {err}")
            self.connection = None
            self.cursor = None
            return False
        except Exception as e:
            logger.error(f"连接过程中发生未知错误: {e}")
            self.connection = None
            self.cursor = None
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            try:
                if self.connection.is_connected():
                    self.connection.close()
                    logger.info("数据库连接已关闭")
            except:
                # 连接可能已经关闭或无效
                pass
    
    def execute_query(self, query, params=None, fetch=False):
        """执行SQL查询，带重试机制"""
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                # 检查连接状态
                connection_valid = False
                if self.connection:
                    try:
                        connection_valid = self.connection.is_connected()
                    except:
                        connection_valid = False
                
                if not connection_valid:
                    if not self.connect():
                        logger.warning(f"重连失败 (尝试 {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                        else:
                            return False
                
                # 确保cursor存在
                if not self.cursor:
                    logger.error("数据库游标未初始化")
                    return False
                
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
                
                if fetch:
                    result = self.cursor.fetchall()
                    return result
                else:
                    self.connection.commit()
                    return True
                    
            except mysql.connector.Error as err:
                error_code = err.errno if hasattr(err, 'errno') else None
                
                # 连接相关错误，尝试重连
                if error_code in (2006, 2013, 2027):  # 连接丢失、服务器断开、数据包错误
                    logger.warning(f"连接错误 (尝试 {attempt + 1}/{max_retries}): {err}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        try:
                            self.connect()
                        except:
                            pass
                        continue
                
                logger.error(f"SQL执行错误: {err}")
                if self.connection:
                    self.connection.rollback()
                return False
            except Exception as e:
                logger.error(f"未知错误: {e}")
                return False
        
        logger.error(f"查询执行失败，已重试 {max_retries} 次")
        return False
    
    def clear_database(self):
        """清空数据库中的所有表"""
        try:
            # 获取所有表名
            self.cursor.execute("SHOW TABLES")
            tables = self.cursor.fetchall()
            
            # 禁用外键检查
            self.cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # 删除所有表
            for table in tables:
                table_name = table[0]
                self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                logger.info(f"删除表: {table_name}")
            
            # 重新启用外键检查
            self.cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            self.connection.commit()
            
            logger.info("数据库清空完成")
            return True
        except mysql.connector.Error as err:
            logger.error(f"清空数据库错误: {err}")
            return False
    
    def create_tables(self):
        """创建数据库表结构"""
        
        # 创建加密货币基本信息表
        crypto_info_table = """
        CREATE TABLE IF NOT EXISTS crypto_info (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL UNIQUE,
            name VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        
        # 创建当前价格表
        current_prices_table = """
        CREATE TABLE IF NOT EXISTS current_prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            price DECIMAL(30, 15) NOT NULL,
            change_24h DECIMAL(30, 15),
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_symbol (symbol),
            INDEX idx_timestamp (timestamp),
            FOREIGN KEY (symbol) REFERENCES crypto_info(symbol) ON DELETE CASCADE
        )
        """
        
        # 创建分钟级历史数据表
        minute_data_table = """
        CREATE TABLE IF NOT EXISTS minute_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            date TIMESTAMP NOT NULL,
            open_price DECIMAL(30, 15) NOT NULL,
            high_price DECIMAL(30, 15) NOT NULL,
            low_price DECIMAL(30, 15) NOT NULL,
            close_price DECIMAL(30, 15) NOT NULL,
            volume DECIMAL(30, 15) DEFAULT 0,
            quote_volume DECIMAL(30, 15) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_symbol_date (symbol, date),
            INDEX idx_symbol (symbol),
            INDEX idx_date (date),
            FOREIGN KEY (symbol) REFERENCES crypto_info(symbol) ON DELETE CASCADE
        )
        """
        
        # 创建小时级历史数据表
        hour_data_table = """
        CREATE TABLE IF NOT EXISTS hour_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            date TIMESTAMP NOT NULL,
            open_price DECIMAL(30, 15) NOT NULL,
            high_price DECIMAL(30, 15) NOT NULL,
            low_price DECIMAL(30, 15) NOT NULL,
            close_price DECIMAL(30, 15) NOT NULL,
            volume DECIMAL(30, 15) DEFAULT 0,
            quote_volume DECIMAL(30, 15) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_symbol_date (symbol, date),
            INDEX idx_symbol (symbol),
            INDEX idx_date (date),
            FOREIGN KEY (symbol) REFERENCES crypto_info(symbol) ON DELETE CASCADE
        )
        """
        
        # 创建天级历史数据表
        day_data_table = """
        CREATE TABLE IF NOT EXISTS day_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            date TIMESTAMP NOT NULL,
            open_price DECIMAL(30, 15) NOT NULL,
            high_price DECIMAL(30, 15) NOT NULL,
            low_price DECIMAL(30, 15) NOT NULL,
            close_price DECIMAL(30, 15) NOT NULL,
            volume DECIMAL(30, 15) DEFAULT 0,
            quote_volume DECIMAL(30, 15) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_symbol_date (symbol, date),
            INDEX idx_symbol (symbol),
            INDEX idx_date (date),
            FOREIGN KEY (symbol) REFERENCES crypto_info(symbol) ON DELETE CASCADE
        )
        """
        
        tables = [
            ("crypto_info", crypto_info_table),
            ("current_prices", current_prices_table),
            ("minute_data", minute_data_table),
            ("hour_data", hour_data_table),
            ("day_data", day_data_table)
        ]
        
        for table_name, table_sql in tables:
            if self.execute_query(table_sql):
                logger.info(f"成功创建表: {table_name}")
            else:
                logger.error(f"创建表失败: {table_name}")
                return False
        
        return True
    
    def insert_crypto_info(self, symbol, name):
        """插入加密货币基本信息"""
        query = """
        INSERT INTO crypto_info (symbol, name) 
        VALUES (%s, %s) 
        ON DUPLICATE KEY UPDATE name = VALUES(name), updated_at = CURRENT_TIMESTAMP
        """
        return self.execute_query(query, (symbol, name))
    
    def insert_current_price(self, symbol, price, change_24h, timestamp):
        """插入当前价格数据"""
        query = """
        INSERT INTO current_prices (symbol, price, change_24h, timestamp) 
        VALUES (%s, %s, %s, %s)
        """
        return self.execute_query(query, (symbol, price, change_24h, timestamp))
    
    def insert_historical_data(self, timeframe, symbol, date, open_price, high_price, 
                             low_price, close_price, volume=0, quote_volume=0):
        """插入历史数据"""
        table_map = {
            'minute': 'minute_data',
            'hour': 'hour_data',
            'day': 'day_data'
        }
        
        if timeframe not in table_map:
            logger.error(f"不支持的时间范围: {timeframe}")
            return False
        
        table_name = table_map[timeframe]
        query = f"""
        INSERT INTO {table_name} 
        (symbol, date, open_price, high_price, low_price, close_price, volume, quote_volume) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        open_price = VALUES(open_price),
        high_price = VALUES(high_price),
        low_price = VALUES(low_price),
        close_price = VALUES(close_price),
        volume = VALUES(volume),
        quote_volume = VALUES(quote_volume)
        """
        
        return self.execute_query(query, (symbol, date, open_price, high_price, 
                                        low_price, close_price, volume, quote_volume))
    
    def get_latest_prices(self, connection=None):
        """获取最新价格数据"""
        query = """
        SELECT ci.name, cp.symbol, cp.price, cp.change_24h, cp.timestamp
        FROM current_prices cp
        JOIN crypto_info ci ON cp.symbol = ci.symbol
        WHERE cp.id IN (
            SELECT MAX(id) FROM current_prices GROUP BY symbol
        )
        ORDER BY cp.timestamp DESC
        """
        
        if connection:
            # 使用传入的连接
            try:
                cursor = connection.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                cursor.close()
                return result
            except Exception as e:
                logger.error(f"使用连接池执行查询失败: {str(e)}")
                return []
        else:
            # 使用原有的execute_query方法（向后兼容）
            return self.execute_query(query, fetch=True)
    
    def get_historical_data(self, timeframe, symbol=None, limit=100, connection=None):
        """获取历史数据"""
        table_map = {
            'minute': 'minute_data',
            'hour': 'hour_data',
            'day': 'day_data'
        }
        
        if timeframe not in table_map:
            return []
        
        table_name = table_map[timeframe]
        
        if symbol:
            query = f"""
            SELECT symbol, date, open_price, high_price, low_price, close_price, volume
            FROM {table_name}
            WHERE symbol = %s
            ORDER BY date DESC
            LIMIT %s
            """
            params = (symbol, limit)
        else:
            query = f"""
            SELECT symbol, date, open_price, high_price, low_price, close_price, volume
            FROM {table_name}
            ORDER BY date DESC
            LIMIT %s
            """
            params = (limit,)
        
        if connection:
            # 使用传入的连接
            try:
                cursor = connection.cursor()
                cursor.execute(query, params)
                result = cursor.fetchall()
                cursor.close()
                return result
            except Exception as e:
                logger.error(f"使用连接池执行查询失败: {str(e)}")
                return []
        else:
            # 使用原有的execute_query方法（向后兼容）
            return self.execute_query(query, params, fetch=True)
    
    def get_latest_price(self, symbol):
        """获取单个加密货币的最新价格"""
        query = """
        SELECT ci.name, cp.symbol, cp.price, cp.change_24h, cp.timestamp
        FROM current_prices cp
        JOIN crypto_info ci ON cp.symbol = ci.symbol
        WHERE cp.symbol = %s
        ORDER BY cp.timestamp DESC
        LIMIT 1
        """
        
        result = self.execute_query(query, (symbol,), fetch=True)
        if result and len(result) > 0:
            row = result[0]
            # 使用统一的时间戳管理器处理时间戳
            unified_timestamp = self.timestamp_manager.ensure_utc(row[4]) if row[4] else None
            return {
                'name': row[0],
                'symbol': row[1],
                'price': float(row[2]),
                'change_24h': float(row[3]) if row[3] else 0,
                'timestamp': self.timestamp_manager.to_iso(unified_timestamp) if unified_timestamp else None,
                'timestamp_ms': self.timestamp_manager.to_timestamp(unified_timestamp) if unified_timestamp else None
            }
        return None
    
    def get_chart_data(self, symbol, timeframe='hour'):
        """获取图表数据"""
        table_map = {
            'minute': 'minute_data',
            'hour': 'hour_data',
            'day': 'day_data'
        }
        
        if timeframe not in table_map:
            return []
        
        table_name = table_map[timeframe]
        query = f"""
        SELECT date, open_price, high_price, low_price, close_price, volume
        FROM {table_name}
        WHERE symbol = %s
        ORDER BY date DESC
        LIMIT 100
        """
        
        result = self.execute_query(query, (symbol,), fetch=True)
        if result:
            chart_data = []
            for row in result:
                # 使用统一的时间戳管理器处理时间戳
                unified_date = self.timestamp_manager.ensure_utc(row[0]) if row[0] else None
                chart_data.append({
                    'date': self.timestamp_manager.to_iso(unified_date) if unified_date else None,
                    'timestamp_ms': self.timestamp_manager.to_timestamp(unified_date) if unified_date else None,
                    'open': float(row[1]),
                    'high': float(row[2]),
                    'low': float(row[3]),
                    'close': float(row[4]),
                    'volume': float(row[5]) if row[5] else 0
                })
            return chart_data
        return []
    
    def get_price_history(self, symbol, timeframe='24h'):
        """获取价格历史"""
        # 根据timeframe确定查询的表和时间范围
        if timeframe == '24h':
            table_name = 'hour_data'
            limit = 24
        elif timeframe == '7d':
            table_name = 'day_data'
            limit = 7
        elif timeframe == '30d':
            table_name = 'day_data'
            limit = 30
        else:
            table_name = 'hour_data'
            limit = 24
        
        query = f"""
        SELECT date, close_price
        FROM {table_name}
        WHERE symbol = %s
        ORDER BY date DESC
        LIMIT %s
        """
        
        result = self.execute_query(query, (symbol, limit), fetch=True)
        if result:
            history = []
            for row in result:
                # 使用统一的时间戳管理器处理时间戳
                unified_date = self.timestamp_manager.ensure_utc(row[0]) if row[0] else None
                history.append({
                    'date': self.timestamp_manager.to_iso(unified_date) if unified_date else None,
                    'timestamp_ms': self.timestamp_manager.to_timestamp(unified_date) if unified_date else None,
                    'price': float(row[1])
                })
            return history
        return []
    
    def get_kline_data(self, symbol):
        """获取K线数据"""
        query = """
        SELECT date, open_price, high_price, low_price, close_price, volume
        FROM hour_data
        WHERE symbol = %s
        ORDER BY date DESC
        LIMIT 100
        """
        
        result = self.execute_query(query, (symbol,), fetch=True)
        if result:
            kline_data = []
            for row in result:
                # 使用统一的时间戳管理器处理时间戳
                unified_date = self.timestamp_manager.ensure_utc(row[0]) if row[0] else None
                kline_data.append({
                    'date': self.timestamp_manager.to_iso(unified_date) if unified_date else None,
                    'timestamp_ms': self.timestamp_manager.to_timestamp(unified_date) if unified_date else None,
                    'open': float(row[1]),
                    'high': float(row[2]),
                    'low': float(row[3]),
                    'close': float(row[4]),
                    'volume': float(row[5]) if row[5] else 0
                })
            return kline_data
        return []
    
    def get_analysis_data(self, symbol):
        """获取分析数据"""
        # 获取最新价格
        latest_price = self.get_latest_price(symbol)
        if not latest_price:
            return {}
        
        # 获取历史数据进行简单分析
        history = self.get_price_history(symbol, '24h')
        if not history:
            return latest_price
        
        prices = [item['price'] for item in history]
        if prices:
            analysis = {
                'current_price': latest_price['price'],
                'max_24h': max(prices),
                'min_24h': min(prices),
                'avg_24h': sum(prices) / len(prices),
                'volatility': (max(prices) - min(prices)) / min(prices) * 100 if min(prices) > 0 else 0
            }
            analysis.update(latest_price)
            return analysis
        
        return latest_price

def rebuild_database():
    """重建数据库结构"""
    db = CryptoDatabase()
    
    if not db.connect():
        return False
    
    try:
        # 清空数据库
        logger.info("开始清空数据库...")
        if not db.clear_database():
            return False
        
        # 创建表结构
        logger.info("开始创建表结构...")
        if not db.create_tables():
            return False
        
        # 插入基本的加密货币信息
        cryptocurrencies = {
            "BTC": "Bitcoin",
            "ETH": "Ethereum"
        }
        
        for symbol, name in cryptocurrencies.items():
            if not db.insert_crypto_info(symbol, name):
                logger.error(f"插入加密货币信息失败: {symbol}")
                return False
            logger.info(f"成功插入加密货币信息: {name} ({symbol})")
        
        logger.info("数据库重建完成")
        return True
        
    finally:
        db.disconnect()

if __name__ == "__main__":
    logger.info("开始重建数据库")
    if rebuild_database():
        logger.info("数据库重建成功")
    else:
        logger.error("数据库重建失败")