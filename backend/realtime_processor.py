#!/usr/bin/env python3
"""
实时数据处理器
专门处理实时比特币和以太坊价格数据，与历史数据分离存储
"""

from crypto_scraper import scrape_realtime_crypto_data
from crypto_db import CryptoDatabase
from simple_redis_manager import get_cache_manager
from timestamp_manager import get_timestamp_manager
from datetime import datetime
import time
from logger_config import get_crypto_logger

logger = get_crypto_logger('realtime_processor')

class RealtimeDataProcessor:
    def __init__(self):
        self.db = CryptoDatabase()
        self.cache_manager = get_cache_manager()
        self.timestamp_manager = get_timestamp_manager()
    
    def process_and_store_realtime_data(self):
        """处理并存储实时数据"""
        logger.info("开始实时数据处理和存储流程")
        
        # 连接数据库
        if not self.db.connect():
            logger.error("数据库连接失败")
            return False
        
        try:
            # 抓取实时数据
            logger.info("开始抓取实时加密货币数据")
            realtime_data = scrape_realtime_crypto_data()
            
            if not realtime_data:
                logger.warning("没有获取到实时数据")
                return False
            
            # 存储实时价格数据到数据库
            logger.info("开始存储实时价格数据到数据库")
            for data in realtime_data:
                # 检查数据质量
                quality_score = self.timestamp_manager.get_data_quality_score(data['timestamp'], 'minute')
                self.timestamp_manager.log_data_status(data['timestamp'], 'minute')
                
                # 只存储质量分数大于0.5的数据
                if quality_score >= 0.5:
                    success = self.db.insert_current_price(
                        symbol=data['symbol'],
                        price=data['price'],
                        change_24h=data['change_24h'],
                        timestamp=data['timestamp']
                    )
                    
                    if success:
                        logger.info(f"实时数据存储成功: {data['symbol']} - ${data['price']:,.2f} (质量分数: {quality_score:.2f})")
                    else:
                        logger.error(f"实时数据存储失败: {data['symbol']}")
                else:
                    logger.warning(f"数据质量过低，跳过存储: {data['symbol']} (质量分数: {quality_score:.2f})")
            
            # 缓存实时数据到Redis
            logger.info("开始缓存实时数据到Redis")
            
            # 准备可序列化的缓存数据
            cache_ready_data = []
            for data in realtime_data:
                cache_item = {
                    'name': data['name'],
                    'symbol': data['symbol'],
                    'price': data['price'],
                    'change_24h': data['change_24h'],
                    'timestamp': data['timestamp'].isoformat(),
                    'cached_at': self.timestamp_manager.get_current_time().isoformat()
                }
                cache_ready_data.append(cache_item)
            
            # 缓存整体实时价格列表
            if self.cache_manager.cache_realtime_prices(cache_ready_data):
                logger.info("实时价格列表缓存成功")
            else:
                logger.warning("实时价格列表缓存失败")
            
            # 缓存单个币种的实时数据
            for data in realtime_data:
                cache_data = {
                    'symbol': data['symbol'],
                    'name': data['name'],
                    'price': data['price'],
                    'change_24h': data['change_24h'],
                    'timestamp': data['timestamp'].isoformat(),
                    'cached_at': self.timestamp_manager.get_current_time().isoformat()
                }
                
                if self.cache_manager.cache_realtime_price(data['symbol'], cache_data):
                    logger.info(f"实时数据缓存成功: {data['symbol']}")
                else:
                    logger.warning(f"实时数据缓存失败: {data['symbol']}")
            
            logger.info("实时数据处理和存储完成")
            return True
            
        except Exception as e:
            logger.error(f"实时数据处理过程中发生错误: {str(e)}")
            return False
        finally:
            self.db.disconnect()
    
    def get_realtime_data_from_cache(self):
        """从缓存获取实时数据"""
        logger.info("从Redis缓存获取实时数据")
        
        # 尝试获取实时价格列表
        cached_data = self.cache_manager.get_realtime_prices()
        if cached_data:
            logger.info(f"从缓存获取到实时数据: {len(cached_data)} 条")
            return cached_data
        
        logger.info("缓存中没有实时数据")
        return None
    
    def get_realtime_data_from_db(self, limit=10):
        """从数据库获取实时数据"""
        logger.info("从数据库获取实时数据")
        
        if not self.db.connect():
            logger.error("数据库连接失败")
            return None
        
        try:
            data = self.db.get_latest_prices()
            if data:
                logger.info(f"从数据库获取到实时数据: {len(data)} 条")
                return data
            else:
                logger.info("数据库中没有实时数据")
                return None
        except Exception as e:
            logger.error(f"从数据库获取实时数据失败: {str(e)}")
            return None
        finally:
            self.db.disconnect()
    
    def get_realtime_data(self, limit=10):
        """获取实时数据（优先从缓存，然后从数据库）"""
        # 首先尝试从缓存获取
        cached_data = self.get_realtime_data_from_cache()
        if cached_data:
            return cached_data
        
        # 如果缓存没有，从数据库获取
        db_data = self.get_realtime_data_from_db(limit)
        if db_data:
            # 将数据库数据转换为缓存格式并缓存
            cache_data = []
            for row in db_data:
                cache_data.append({
                    'name': row[0],
                    'symbol': row[1],
                    'price': float(row[2]),
                    'change_24h': float(row[3]) if row[3] else 0,
                    'timestamp': row[4].isoformat() if hasattr(row[4], 'isoformat') else str(row[4]),
                    'created_at': row[5].isoformat() if hasattr(row[5], 'isoformat') else str(row[5])
                })
            
            # 缓存数据
            self.cache_manager.cache_realtime_prices(cache_data)
            return cache_data
        
        return None

def run_realtime_processor():
    """运行实时数据处理器"""
    processor = RealtimeDataProcessor()
    
    while True:
        try:
            logger.info("=" * 50)
            logger.info("开始新一轮实时数据处理")
            
            # 处理和存储实时数据
            success = processor.process_and_store_realtime_data()
            
            if success:
                logger.info("实时数据处理成功")
            else:
                logger.error("实时数据处理失败")
            
            # 等待30秒后进行下一轮处理
            logger.info("等待30秒后进行下一轮处理...")
            time.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止实时数据处理")
            break
        except Exception as e:
            logger.error(f"实时数据处理器发生未预期错误: {str(e)}")
            time.sleep(10)  # 发生错误时等待10秒

if __name__ == "__main__":
    logger.info("启动实时数据处理器")
    run_realtime_processor()