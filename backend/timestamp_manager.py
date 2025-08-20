#!/usr/bin/env python3
"""
智能时间戳管理器
解决API数据延迟和时间窗口边界问题
"""

from datetime import datetime, timedelta
import pytz
from typing import Dict, Optional, Tuple
from logger_config import get_crypto_logger

# 配置日志
logger = get_crypto_logger(__name__)

class TimestampManager:
    """智能时间戳管理器"""
    
    def __init__(self):
        self.timezone = pytz.UTC
        self.api_delay_estimates = {
            'minute': timedelta(minutes=2),  # 分钟级数据延迟约2分钟
            'hour': timedelta(minutes=5),    # 小时级数据延迟约5分钟
            'day': timedelta(hours=1)        # 日级数据延迟约1小时
        }
        
    def get_current_time(self) -> datetime:
        """获取当前UTC时间"""
        return datetime.now(self.timezone)
    
    def get_expected_latest_timestamp(self, timeframe: str) -> datetime:
        """获取预期的最新数据时间戳"""
        current_time = self.get_current_time()
        delay = self.api_delay_estimates.get(timeframe, timedelta(minutes=5))
        
        # 减去API延迟
        adjusted_time = current_time - delay
        
        # 根据时间范围调整到边界
        if timeframe == 'minute':
            # 调整到分钟边界
            return adjusted_time.replace(second=0, microsecond=0)
        elif timeframe == 'hour':
            # 调整到小时边界
            return adjusted_time.replace(minute=0, second=0, microsecond=0)
        elif timeframe == 'day':
            # 调整到日边界
            return adjusted_time.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # 对于实时数据，不进行边界调整，只减去延迟
            return adjusted_time
    
    def calculate_data_freshness(self, data_timestamp: datetime, timeframe: str) -> Tuple[timedelta, bool]:
        """计算数据新鲜度"""
        current_time = self.get_current_time()
        
        # 如果数据时间戳是字符串，转换为datetime
        if isinstance(data_timestamp, str):
            data_timestamp = datetime.fromisoformat(data_timestamp.replace('Z', '+00:00'))
        
        # 确保时间戳有时区信息
        if data_timestamp.tzinfo is None:
            data_timestamp = data_timestamp.replace(tzinfo=self.timezone)
        
        # 直接计算当前时间与数据时间的差值
        lag = current_time - data_timestamp
        
        # 定义可接受的延迟阈值
        acceptable_thresholds = {
            'minute': timedelta(minutes=5),
            'hour': timedelta(minutes=15),
            'day': timedelta(hours=2)
        }
        
        threshold = acceptable_thresholds.get(timeframe, timedelta(minutes=10))
        is_fresh = lag <= threshold
        
        return lag, is_fresh
    
    def get_interpolated_timestamp(self, timeframe: str) -> datetime:
        """获取插值时间戳（用于填补数据空白）"""
        current_time = self.get_current_time()
        
        if timeframe == 'minute':
            # 返回当前分钟的开始
            return current_time.replace(second=0, microsecond=0)
        elif timeframe == 'hour':
            # 返回当前小时的开始
            return current_time.replace(minute=0, second=0, microsecond=0)
        elif timeframe == 'day':
            # 返回当前日的开始
            return current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return current_time
    
    def should_request_new_data(self, last_update: Optional[datetime], timeframe: str) -> bool:
        """判断是否应该请求新数据"""
        if last_update is None:
            return True
        
        current_time = self.get_current_time()
        
        # 根据时间范围设置更新间隔
        update_intervals = {
            'minute': timedelta(minutes=1),
            'hour': timedelta(minutes=5),
            'day': timedelta(hours=1)
        }
        
        interval = update_intervals.get(timeframe, timedelta(minutes=5))
        
        # 如果距离上次更新超过间隔，则需要更新
        return (current_time - last_update) >= interval
    
    def format_timestamp_for_api(self, timestamp: datetime) -> str:
        """格式化时间戳用于API请求"""
        return timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    def parse_api_timestamp(self, timestamp_str: str) -> datetime:
        """解析API返回的时间戳"""
        try:
            # 尝试多种格式
            formats = [
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    return dt.replace(tzinfo=self.timezone)
                except ValueError:
                    continue
            
            # 如果都失败，尝试ISO格式
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
        except Exception as e:
            logger.error(f"解析时间戳失败: {timestamp_str}, 错误: {str(e)}")
            return self.get_current_time()
    
    def get_data_freshness(self, data_timestamp: datetime, timeframe: str) -> float:
        """获取数据新鲜度（以分钟为单位的延迟时间）"""
        lag, is_fresh = self.calculate_data_freshness(data_timestamp, timeframe)
        return lag.total_seconds() / 60.0  # 转换为分钟
    
    def get_data_quality_score(self, data_timestamp: datetime, timeframe: str) -> float:
        """计算数据质量分数 (0-1)"""
        lag, is_fresh = self.calculate_data_freshness(data_timestamp, timeframe)
        
        if is_fresh:
            return 1.0
        
        # 根据延迟程度计算分数
        max_acceptable_lag = {
            'minute': timedelta(minutes=10),
            'hour': timedelta(minutes=30),
            'day': timedelta(hours=4)
        }
        
        max_lag = max_acceptable_lag.get(timeframe, timedelta(minutes=15))
        
        if lag >= max_lag:
            return 0.0
        
        # 线性衰减
        score = 1.0 - (lag.total_seconds() / max_lag.total_seconds())
        return max(0.0, score)
    
    def log_data_status(self, data_timestamp: datetime, timeframe: str):
        """记录数据状态"""
        lag, is_fresh = self.calculate_data_freshness(data_timestamp, timeframe)
        quality_score = self.get_data_quality_score(data_timestamp, timeframe)
        
        status = "新鲜" if is_fresh else "延迟"
        
        logger.info(f"数据状态 [{timeframe}]: {status}")
        logger.info(f"  - 数据时间: {data_timestamp}")
        logger.info(f"  - 延迟时间: {lag}")
        logger.info(f"  - 质量分数: {quality_score:.2f}")
    
    @staticmethod
    def ensure_utc(dt):
        """确保datetime对象有UTC时区信息"""
        if dt is None:
            return None
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone(pytz.UTC)
    
    @staticmethod
    def to_iso(dt):
        """转换为ISO格式字符串"""
        if dt is None:
            return None
        return dt.isoformat()
    
    @staticmethod
    def to_timestamp(dt):
        """转换为时间戳（毫秒）"""
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)
    
    @staticmethod
    def parse_datetime(dt_str):
        """解析datetime字符串"""
        if dt_str is None:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC)

# 全局实例
timestamp_manager = TimestampManager()

def get_timestamp_manager() -> TimestampManager:
    """获取时间戳管理器实例"""
    return timestamp_manager

def get_unified_timestamp():
    """获取统一的当前时间戳"""
    return timestamp_manager.get_current_time()

def get_unified_datetime():
    """获取统一的当前datetime"""
    return timestamp_manager.get_current_time()

def get_unified_iso():
    """获取统一的ISO格式时间字符串"""
    return timestamp_manager.get_current_time().isoformat()