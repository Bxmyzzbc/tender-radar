"""
定时任务调度器
每天18:00自动运行爬虫
"""

import time
import logging
import subprocess
import sys
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Scheduler:
    """定时任务调度器"""
    
    def __init__(self, hour: int = 18, minute: int = 0):
        """
        Args:
            hour: 运行小时（24小时制）
            minute: 运行分钟
        """
        self.target_hour = hour
        self.target_minute = minute
    
    def get_next_run_time(self) -> datetime:
        """计算下次运行时间"""
        now = datetime.now()
        target = now.replace(hour=self.target_hour, minute=self.target_minute, second=0, microsecond=0)
        
        # 如果今天已过，则设为明天
        if now >= target:
            target = target.replace(day=now.day + 1)
        
        return target
    
    def wait_until_next_run(self):
        """等待到下次运行时间"""
        while True:
            now = datetime.now()
            target = self.get_next_run_time()
            
            if now >= target:
                break
            
            delta = (target - now).total_seconds()
            hours = int(delta // 3600)
            minutes = int((delta % 3600) // 60)
            
            logger.info(f"下次运行时间: {target.strftime('%Y-%m-%d %H:%M')}, "
                       f"等待 {hours}小时{minutes}分钟")
            
            # 每小时检查一次
            time.sleep(min(3600, delta))
    
    def run(self):
        """运行调度器"""
        logger.info(f"=== 定时任务启动 ===")
        logger.info(f"设置运行时间: 每天 {self.target_hour:02d}:{self.target_minute:02d}")
        
        while True:
            try:
                # 等待到运行时间
                self.wait_until_next_run()
                
                # 运行爬虫
                logger.info("=== 开始执行爬虫任务 ===")
                
                # 获取当前脚本所在目录
                script_dir = os.path.dirname(os.path.abspath(__file__))
                main_script = os.path.join(script_dir, "main.py")
                
                # 运行主程序
                result = subprocess.run(
                    [sys.executable, main_script, "--pages", "5"],
                    capture_output=False
                )
                
                if result.returncode == 0:
                    logger.info("=== 爬虫任务执行成功 ===")
                else:
                    logger.error(f"=== 爬虫任务执行失败，退出码: {result.returncode} ===")
                
                # 执行完成后继续等待下一个周期
                
            except KeyboardInterrupt:
                logger.info("收到中断信号，退出调度器")
                break
            except Exception as e:
                logger.error(f"调度器异常: {e}")
                # 发生异常后等待1分钟再继续
                time.sleep(60)


def run_once():
    """单次运行（不等待）"""
    logger.info("=== 单次运行模式 ===")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, "main.py")
    
    result = subprocess.run(
        [sys.executable, main_script, "--pages", "5"],
        capture_output=False
    )
    
    return result.returncode == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="定时任务调度器")
    parser.add_argument("--hour", type=int, default=18, help="运行小时(24小时制)")
    parser.add_argument("--minute", type=int, default=0, help="运行分钟")
    parser.add_argument("--once", action="store_true", help="单次运行，不等待")
    
    args = parser.parse_args()
    
    if args.once:
        run_once()
    else:
        scheduler = Scheduler(hour=args.hour, minute=args.minute)
        scheduler.run()
