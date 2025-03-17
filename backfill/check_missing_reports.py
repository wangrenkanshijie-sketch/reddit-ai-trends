#!/usr/bin/env python3
"""
Check Missing Reports Script

此脚本用于检查特定日期范围内缺失的报告，不修改现有代码。
它通过查询MongoDB数据库来确定哪些日期的报告缺失。
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入MongoDB客户端
from database.mongodb import MongoDBClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backfill/check_missing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_existing_report_dates() -> List[datetime]:
    """
    从MongoDB获取所有已存在的报告日期
    
    Returns:
        已存在报告的日期列表
    """
    try:
        # 初始化MongoDB客户端
        mongodb_client = MongoDBClient()
        
        # 获取所有报告
        all_reports = mongodb_client.get_all_reports()
        
        # 提取报告日期
        report_dates = []
        for report in all_reports:
            created_at = report.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except ValueError:
                        # 尝试其他日期格式
                        try:
                            created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            logger.warning(f"无法解析日期: {created_at}")
                            continue
                report_dates.append(created_at.replace(hour=0, minute=0, second=0, microsecond=0))
        
        # 关闭MongoDB连接
        mongodb_client.close()
        
        return report_dates
    
    except Exception as e:
        logger.error(f"获取现有报告日期时出错: {e}")
        return []

def find_missing_dates(start_date: datetime, end_date: datetime, interval_hours: int = 24) -> List[datetime]:
    """
    查找指定日期范围内缺失的报告日期
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        interval_hours: 报告间隔小时数
        
    Returns:
        缺失报告的日期列表
    """
    # 获取现有报告日期
    existing_dates = get_existing_report_dates()
    
    # 检查缺失的日期
    missing_dates = []
    current_date = start_date
    while current_date <= end_date:
        # 将当前日期规范化为当天的00:00:00
        normalized_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if normalized_date not in existing_dates:
            missing_dates.append(current_date)
        
        # 前进到下一个日期
        current_date += timedelta(hours=interval_hours)
    
    return missing_dates

def check_missing_reports(start_date_str: str, end_date_str: str, interval_hours: int = 24, output_file: str = None):
    """
    检查指定日期范围内缺失的报告
    
    Args:
        start_date_str: 开始日期 (YYYY-MM-DD)
        end_date_str: 结束日期 (YYYY-MM-DD)
        interval_hours: 报告间隔小时数
        output_file: 输出文件路径，如果提供则将结果写入文件
    """
    try:
        # 解析日期字符串
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        logger.info(f"开始检查缺失报告，日期范围: {start_date_str} 到 {end_date_str}")
        
        # 查找缺失的日期
        missing_dates = find_missing_dates(start_date, end_date, interval_hours)
        
        # 输出结果
        if missing_dates:
            logger.info(f"找到 {len(missing_dates)} 个缺失的日期:")
            for date in missing_dates:
                logger.info(f"  - {date.strftime('%Y-%m-%d')}")
            
            # 如果提供了输出文件，将结果写入文件
            if output_file:
                with open(output_file, "w") as f:
                    f.write(f"缺失报告日期 ({len(missing_dates)}):\n")
                    for date in missing_dates:
                        f.write(f"{date.strftime('%Y-%m-%d')}\n")
                logger.info(f"结果已写入文件: {output_file}")
        else:
            logger.info("未找到缺失的报告")
            
            # 如果提供了输出文件，将结果写入文件
            if output_file:
                with open(output_file, "w") as f:
                    f.write("未找到缺失的报告\n")
                logger.info(f"结果已写入文件: {output_file}")
    
    except Exception as e:
        logger.error(f"检查缺失报告时出错: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="检查缺失的报告")
    parser.add_argument("--start", required=True, help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--interval", type=int, default=24, help="报告间隔小时数")
    parser.add_argument("--output", help="输出文件路径")
    
    args = parser.parse_args()
    check_missing_reports(args.start, args.end, args.interval, args.output)

if __name__ == "__main__":
    main() 