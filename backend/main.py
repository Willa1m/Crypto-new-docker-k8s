#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本文件仅用于本地测试和开发调试
正式部署时请使用 crypto_web_app.py 作为主要入口

功能说明：
- 提供完整的系统初始化和测试功能
- 包含交互式菜单用于开发调试
- 不参与生产环境的后端服务调用
"""

import signal
import sys
import time
import threading
import schedule
from datetime import datetime

# 导入各个模块
from crypto_scraper import scrape_all_crypto_data as run_data_processing
from crypto_analyzer import run_analysis
from realtime_processor import run_realtime_processor
from crypto_web_app import CryptoWebApp
from crypto_db import CryptoDatabase, rebuild_database
from kline_processor import run_kline_processing
from logger_config import get_crypto_logger

# 配置日志
logger = get_crypto_logger(__name__)

class CryptoSystem:
    def __init__(self):
        self.web_app_process = None
        self.is_running = False
    
    def initialize_system(self):
        """初始化系统"""
        logger.info("=== 加密货币监控系统初始化 ===")
        
        # 1. 重建数据库
        logger.info("步骤 1: 重建数据库结构")
        if not rebuild_database():
            logger.error("数据库重建失败，系统初始化中止")
            return False
        
        # 2. 首次数据抓取和处理
        logger.info("步骤 2: 首次数据抓取和处理")
        if not run_data_processing():
            logger.error("首次数据处理失败，但系统将继续运行")
        
        # 3. 生成初始分析报告
        logger.info("步骤 3: 生成初始分析报告")
        if not run_analysis():
            logger.error("初始分析报告生成失败，但系统将继续运行")
        
        # 4. 生成初始K线数据
        logger.info("步骤 4: 生成初始K线数据")
        if not run_kline_processing():
            logger.error("初始K线数据生成失败，但系统将继续运行")
        
        logger.info("系统初始化完成")
        return True
    
    def schedule_tasks(self):
        """设置定时任务"""
        logger.info("设置定时任务")
        
        # 每5分钟运行一次数据收集
        schedule.every(5).minutes.do(self.run_data_collection_task)
        
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
    
    def start_web_server(self):
        """启动Web服务器"""
        logger.info("启动Web服务器")
        try:
            app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
        except Exception as e:
            logger.error(f"Web服务器启动失败: {str(e)}")
    
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
    
    def stop_system(self):
        """停止系统"""
        logger.info("正在停止系统...")
        self.is_running = False

def print_menu():
    """打印菜单"""
    print("\n" + "="*50)
    print("🚀 加密货币监控系统")
    print("="*50)
    print("1. 初始化系统（重建数据库）")
    print("2. 运行数据抓取和处理")
    print("3. 运行实时数据处理")
    print("4. 生成分析报告")
    print("5. 启动Web服务器")
    print("6. 启动完整系统（推荐）")
    print("7. 查看系统状态")
    print("0. 退出")
    print("="*50)

def show_system_status():
    """显示系统状态"""
    print("\n📊 系统状态:")
    
    # 检查日志文件
    log_files = [
        'crypto_system.log',
        'crypto_scraper.log', 
        'crypto_db.log',
        'data_processor.log',
        'crypto_analyzer.log',
        'crypto_web_app.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f"  ✅ {log_file}: {size} bytes")
        else:
            print(f"  ❌ {log_file}: 不存在")
    
    # 检查输出目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    charts_dir = os.path.join(current_dir, 'static', 'charts')
    if os.path.exists(charts_dir):
        chart_files = os.listdir(charts_dir)
        print(f"  📈 图表文件: {len(chart_files)} 个")
    else:
        print("  📈 图表目录: 不存在")

def main():
    """主函数"""
    system = CryptoSystem()
    
    while True:
        print_menu()
        choice = input("请选择操作 (0-7): ").strip()
        
        if choice == '0':
            print("👋 感谢使用，再见！")
            break
        
        elif choice == '1':
            print("🔄 正在初始化系统...")
            if system.initialize_system():
                print("✅ 系统初始化成功！")
            else:
                print("❌ 系统初始化失败！")
        
        elif choice == '2':
            print("📊 正在运行数据抓取和处理...")
            if run_data_processing():
                print("✅ 数据处理完成！")
            else:
                print("❌ 数据处理失败！")
        
        elif choice == '3':
            print("⚡ 正在运行实时数据处理...")
            if run_realtime_processor():
                print("✅ 实时数据处理完成！")
            else:
                print("❌ 实时数据处理失败！")
        
        elif choice == '4':
            print("📈 正在生成分析报告...")
            if run_analysis():
                print("✅ 分析报告生成完成！")
            else:
                print("❌ 分析报告生成失败！")
        
        elif choice == '5':
            print("🌐 正在启动Web服务器...")
            print("访问 http://localhost:5000 查看系统")
            print("按 Ctrl+C 停止服务器")
            try:
                system.start_web_server()
            except KeyboardInterrupt:
                print("\n🛑 Web服务器已停止")
        
        elif choice == '6':
            print("🚀 正在启动完整系统...")
            
            # 初始化系统
            if not system.initialize_system():
                print("❌ 系统初始化失败，无法启动完整系统")
                continue
            
            # 设置定时任务
            system.schedule_tasks()
            
            print("✅ 系统启动成功！")
            print("🌐 Web服务器: http://localhost:5000")
            print("📊 定时任务已启动")
            print("⚡ 实时数据处理已启动")
            print("按 Ctrl+C 停止系统")
            
            try:
                # 在后台启动Web服务器
                import threading
                web_thread = threading.Thread(target=system.start_web_server)
                web_thread.daemon = True
                web_thread.start()
                
                # 运行调度器
                system.run_scheduler()
                
            except KeyboardInterrupt:
                print("\n🛑 正在停止系统...")
                system.stop_system()
                print("✅ 系统已停止")
        
        elif choice == '7':
            show_system_status()
        
        else:
            print("❌ 无效选择，请重新输入")
        
        if choice != '0':
            input("\n按回车键继续...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断，再见！")
    except Exception as e:
        logger.error(f"系统运行异常: {str(e)}")
        print(f"❌ 系统运行异常: {str(e)}")