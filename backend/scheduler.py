#!/usr/bin/env python3
"""
加密货币监控系统 - 定时任务调度器
专门用于运行定时任务，独立于Web服务器
"""

from datetime import datetime, timedelta
import time
import signal
import sys
from data_processor import run_data_processing
from realtime_processor import run_realtime_processor
from crypto_analyzer import run_analysis
from kline_processor import run_kline_processing
from crypto_db import CryptoDatabase
from simple_redis_manager import get_cache_manager
from timestamp_manager import get_timestamp_manager
from logger_config import get_crypto_logger

logger = get_crypto_logger('scheduler')

class CryptoScheduler:
    def __init__(self):
        self.is_running = False
    
    def setup_schedule(self):
        """设置定时任务"""
        logger.info("设置定时任务")
        
        # 数据收集任务 - 每1分钟执行一次（优化频率）
        schedule.every(5).minutes.do(self.run_data_collection_task)
        
        # 实时数据处理任务 - 每15秒执行一次（优化频率）
        schedule.every(30).seconds.do(self.run_realtime_task)
        
        # 每小时运行一次分析
        schedule.every().hour.do(self.run_analysis_task)
        
        # 每天凌晨2点运行完整处理
        schedule.every().day.at("02:00").do(self.run_full_processing)
        
        logger.info("定时任务设置完成")
        logger.info("- 数据收集: 每1分钟")
        logger.info("- 实时处理: 每15秒")
        logger.info("- 分析任务: 每小时")
        logger.info("- 完整处理: 每天凌晨2点")
    
    def run_realtime_task(self):
        """运行实时数据处理任务"""
        logger.info("执行实时数据处理任务")
        try:
            if run_realtime_processor():
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
    
    def run(self):
        """运行调度器"""
        logger.info("🚀 启动加密货币监控系统调度器")
        
        # 设置定时任务
        self.setup_schedule()
        
        # 立即运行一次数据收集
        logger.info("执行初始数据收集...")
        self.run_data_collection_task()
        
        self.is_running = True
        logger.info("📊 调度器开始运行...")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(10)  # 每10秒检查一次
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在停止调度器...")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"调度器运行异常: {str(e)}")
                time.sleep(60)  # 出错后等待1分钟再继续
        
        logger.info("🛑 调度器已停止")
    
    def stop(self):
        """停止调度器"""
        logger.info("正在停止调度器...")
        self.is_running = False

def main():
    """主函数"""
    scheduler = CryptoScheduler()
    
    try:
        scheduler.run()
    except KeyboardInterrupt:
        print("\n\n👋 调度器被用户中断，再见！")
    except Exception as e:
        logger.error(f"调度器运行异常: {str(e)}")
        print(f"❌ 调度器运行异常: {str(e)}")

if __name__ == "__main__":
    main()