from crypto_scraper import scrape_all_crypto_data
from crypto_db import CryptoDatabase
from timestamp_manager import get_timestamp_manager
from datetime import datetime, timedelta
import pandas as pd
import time
from logger_config import get_crypto_logger

logger = get_crypto_logger('data_processor')

class DataProcessor:
    def __init__(self):
        self.db = CryptoDatabase()
        self.timestamp_manager = get_timestamp_manager()
    
    def process_and_store_data(self):
        """处理并存储抓取的数据"""
        logger.info("开始数据处理和存储流程")
        
        # 连接数据库
        if not self.db.connect():
            logger.error("数据库连接失败")
            return False
        
        try:
            # 抓取数据
            logger.info("开始抓取加密货币数据")
            current_data, historical_data = scrape_all_crypto_data()
            
            # 存储当前价格数据
            if current_data:
                logger.info("开始存储当前价格数据")
                for data in current_data:
                    success = self.db.insert_current_price(
                        data['symbol'],
                        data['price'],
                        data['change_24h'],
                        data['timestamp']
                    )
                    if success:
                        logger.info(f"成功存储 {data['name']} 当前价格: ${data['price']:,.2f}")
                    else:
                        logger.error(f"存储 {data['name']} 当前价格失败")
            
            # 存储历史数据
            for timeframe, df in historical_data.items():
                if not df.empty:
                    logger.info(f"开始存储 {timeframe} 级历史数据，共 {len(df)} 条记录")
                    
                    for _, row in df.iterrows():
                        success = self.db.insert_historical_data(
                            timeframe,
                            row['symbol'],
                            row['date'],
                            row['open'],
                            row['high'],
                            row['low'],
                            row['close'],
                            row['volume'],
                            row['quote_volume']
                        )
                        
                        if not success:
                            logger.error(f"存储历史数据失败: {row['symbol']} - {row['date']}")
                    
                    logger.info(f"完成存储 {timeframe} 级历史数据")
            
            logger.info("数据处理和存储完成")
            return True
            
        except Exception as e:
            logger.error(f"数据处理过程中发生错误: {str(e)}")
            return False
        
        finally:
            self.db.disconnect()
    
    def get_summary_statistics(self):
        """获取数据统计摘要"""
        if not self.db.connect():
            return None
        
        try:
            stats = {}
            
            # 获取最新价格
            latest_prices = self.db.get_latest_prices()
            stats['latest_prices'] = latest_prices
            
            # 获取各时间范围的数据量统计
            for timeframe in ['minute', 'hour', 'day']:
                data = self.db.get_historical_data(timeframe, limit=1000)
                stats[f'{timeframe}_data_count'] = len(data) if data else 0
            
            return stats
            
        finally:
            self.db.disconnect()

def run_data_processing():
    """运行数据处理流程"""
    processor = DataProcessor()
    
    # 处理和存储数据
    if processor.process_and_store_data():
        logger.info("数据处理成功")
        
        # 获取统计信息
        stats = processor.get_summary_statistics()
        if stats:
            logger.info("=== 数据统计摘要 ===")
            
            if stats['latest_prices']:
                logger.info("最新价格:")
                for price_data in stats['latest_prices']:
                    name, symbol, price, change_24h, timestamp = price_data
                    logger.info(f"  {name} ({symbol}): ${float(price):,.2f}, 24h变化: {float(change_24h):.2f}%")
            
            logger.info("历史数据统计:")
            for timeframe in ['minute', 'hour', 'day']:
                count = stats.get(f'{timeframe}_data_count', 0)
                logger.info(f"  {timeframe}级数据: {count} 条记录")
        
        return True
    else:
        logger.error("数据处理失败")
        return False

if __name__ == "__main__":
    logger.info("启动数据处理程序")
    success = run_data_processing()
    if success:
        logger.info("数据处理程序执行成功")
    else:
        logger.error("数据处理程序执行失败")