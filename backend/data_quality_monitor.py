#!/usr/bin/env python3
"""
数据质量监控脚本
监控数据延迟、质量分数和系统健康状态
"""

import time
from datetime import datetime, timedelta
from crypto_db import CryptoDatabase
from timestamp_manager import get_timestamp_manager
import json
from logger_config import get_crypto_logger

# 配置日志
logger = get_crypto_logger(__name__)

class DataQualityMonitor:
    def __init__(self):
        self.db = CryptoDatabase()
        self.timestamp_manager = get_timestamp_manager()
        
    def check_data_freshness(self):
        """检查数据新鲜度"""
        if not self.db.connect():
            logger.error("数据库连接失败")
            return None
            
        try:
            results = {}
            
            for timeframe in ['minute', 'hour', 'day']:
                # 获取最新数据时间戳
                query = f"""
                SELECT MAX(date) as latest_timestamp 
                FROM {timeframe}_data 
                WHERE symbol = 'BTC'
                """
                
                result = self.db.execute_query(query, fetch=True)
                if result and result[0][0]:
                    latest_timestamp = result[0][0]
                    
                    # 计算数据新鲜度
                    freshness = self.timestamp_manager.get_data_freshness(latest_timestamp, timeframe)
                    quality_score = self.timestamp_manager.get_data_quality_score(latest_timestamp, timeframe)
                    
                    # 获取期望的最新时间戳
                    expected_timestamp = self.timestamp_manager.get_expected_latest_timestamp(timeframe)
                    
                    results[timeframe] = {
                        'latest_timestamp': latest_timestamp,
                        'expected_timestamp': expected_timestamp,
                        'freshness_minutes': freshness,
                        'quality_score': quality_score,
                        'status': 'healthy' if quality_score >= 0.7 else 'warning' if quality_score >= 0.5 else 'critical'
                    }
                    
                    logger.info(f"{timeframe}级数据状态: {results[timeframe]['status']} "
                               f"(新鲜度: {freshness:.1f}分钟, 质量分数: {quality_score:.2f})")
                else:
                    results[timeframe] = {
                        'status': 'no_data',
                        'message': '无数据'
                    }
                    logger.warning(f"{timeframe}级数据: 无数据")
            
            return results
            
        except Exception as e:
            logger.error(f"检查数据新鲜度时发生错误: {str(e)}")
            return None
        finally:
            self.db.disconnect()
    
    def check_data_gaps(self):
        """检查数据缺口"""
        if not self.db.connect():
            return None
            
        try:
            gaps = {}
            
            for timeframe in ['minute', 'hour', 'day']:
                # 获取最近的数据时间戳
                query = f"""
                SELECT date 
                FROM {timeframe}_data 
                WHERE symbol = 'BTC' 
                ORDER BY date DESC 
                LIMIT 10
                """
                
                result = self.db.execute_query(query, fetch=True)
                if result and len(result) > 1:
                    timestamps = [row[0] for row in result]
                    
                    # 检查时间间隔
                    expected_interval = {
                        'minute': timedelta(minutes=1),
                        'hour': timedelta(hours=1),
                        'day': timedelta(days=1)
                    }[timeframe]
                    
                    gap_count = 0
                    for i in range(len(timestamps) - 1):
                        actual_interval = timestamps[i] - timestamps[i + 1]
                        if actual_interval > expected_interval * 1.5:  # 允许50%的误差
                            gap_count += 1
                    
                    gaps[timeframe] = {
                        'total_checked': len(timestamps) - 1,
                        'gaps_found': gap_count,
                        'gap_rate': gap_count / (len(timestamps) - 1) if len(timestamps) > 1 else 0
                    }
                    
                    logger.info(f"{timeframe}级数据缺口率: {gaps[timeframe]['gap_rate']:.2%}")
                else:
                    gaps[timeframe] = {'status': 'insufficient_data'}
            
            return gaps
            
        except Exception as e:
            logger.error(f"检查数据缺口时发生错误: {str(e)}")
            return None
        finally:
            self.db.disconnect()
    
    def generate_health_report(self):
        """生成健康报告"""
        logger.info("=== 数据质量健康报告 ===")
        
        # 检查数据新鲜度
        freshness_results = self.check_data_freshness()
        if freshness_results:
            logger.info("数据新鲜度检查:")
            for timeframe, data in freshness_results.items():
                if data.get('status') == 'no_data':
                    logger.warning(f"  {timeframe}: {data['message']}")
                else:
                    logger.info(f"  {timeframe}: {data['status']} "
                               f"(延迟: {data['freshness_minutes']:.1f}分钟)")
        
        # 检查数据缺口
        gap_results = self.check_data_gaps()
        if gap_results:
            logger.info("数据完整性检查:")
            for timeframe, data in gap_results.items():
                if data.get('status') == 'insufficient_data':
                    logger.warning(f"  {timeframe}: 数据不足")
                else:
                    logger.info(f"  {timeframe}: 缺口率 {data['gap_rate']:.2%}")
        
        # 生成总体健康状态
        overall_status = self._calculate_overall_health(freshness_results, gap_results)
        logger.info(f"总体健康状态: {overall_status}")
        
        return {
            'timestamp': datetime.now(),
            'freshness': freshness_results,
            'gaps': gap_results,
            'overall_status': overall_status
        }
    
    def _calculate_overall_health(self, freshness_results, gap_results):
        """计算总体健康状态"""
        if not freshness_results or not gap_results:
            return 'unknown'
        
        critical_count = 0
        warning_count = 0
        healthy_count = 0
        
        for timeframe, data in freshness_results.items():
            status = data.get('status', 'unknown')
            if status == 'critical':
                critical_count += 1
            elif status == 'warning':
                warning_count += 1
            elif status == 'healthy':
                healthy_count += 1
        
        if critical_count > 0:
            return 'critical'
        elif warning_count > 0:
            return 'warning'
        elif healthy_count > 0:
            return 'healthy'
        else:
            return 'unknown'
    
    def run_continuous_monitoring(self, interval_seconds=60):
        """运行连续监控"""
        logger.info(f"开始连续监控，检查间隔: {interval_seconds}秒")
        
        while True:
            try:
                self.generate_health_report()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logger.info("监控已停止")
                break
            except Exception as e:
                logger.error(f"监控过程中发生错误: {str(e)}")
                time.sleep(interval_seconds)

def run_single_check():
    """运行单次检查"""
    monitor = DataQualityMonitor()
    return monitor.generate_health_report()

def run_continuous_monitoring(interval=60):
    """运行连续监控"""
    monitor = DataQualityMonitor()
    monitor.run_continuous_monitoring(interval)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'continuous':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        run_continuous_monitoring(interval)
    else:
        run_single_check()