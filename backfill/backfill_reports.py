#!/usr/bin/env python3
"""
Backfill Reports Script

此脚本用于补充生成特定日期范围内的缺失报告，不修改现有代码。
它通过调用现有的report_generation.py脚本并传递特定日期参数来实现。
"""

import os
import sys
import argparse
import subprocess
import logging
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入MongoDB客户端（用于检查现有报告）
from database.mongodb import MongoDBClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backfill/backfill.log"),
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

def generate_report_for_date(target_date: datetime, hours: int = 24, push_to_github: bool = False) -> bool:
    """
    为特定日期生成报告
    
    Args:
        target_date: 目标日期
        hours: 回溯的小时数
        push_to_github: 是否推送到GitHub
        
    Returns:
        是否成功生成报告
    """
    try:
        # 创建临时环境变量文件，添加REFERENCE_DATE
        env_file = "backfill/temp_env.json"
        reference_date_str = target_date.strftime("%Y-%m-%d %H:%M:%S")
        
        # 将日期信息写入临时文件
        with open(env_file, "w") as f:
            json.dump({
                "reference_date": reference_date_str,
                "hours": hours
            }, f)
        
        # 构建命令 - 使用绝对路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cmd = [
            "python", 
            "-c", 
            f"""
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append("{project_root}")

# 导入report_generation模块
from report_generation import generate_report

# 读取临时环境变量
with open("{env_file}", "r") as f:
    env_data = json.load(f)

# 解析日期
reference_date = datetime.strptime(env_data["reference_date"], "%Y-%m-%d %H:%M:%S")
hours = env_data["hours"]

# 生成报告
report = generate_report(
    hours=hours,
    save_to_db=True,
    save_to_file=True,
    push_to_github={str(push_to_github).lower() == 'true'},
    reference_date=reference_date
)

print(f"成功为 {{reference_date}} 生成报告")
            """
        ]
        
        # 执行命令
        logger.info(f"正在为 {reference_date_str} 生成报告...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 检查结果
        if result.returncode == 0:
            logger.info(f"成功为 {reference_date_str} 生成报告")
            logger.debug(f"输出: {result.stdout}")
            return True
        else:
            logger.error(f"为 {reference_date_str} 生成报告失败")
            logger.error(f"错误: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"为 {reference_date_str} 生成报告时出错: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(env_file):
            os.remove(env_file)

def backfill_reports(start_date_str: str, end_date_str: str, interval_hours: int = 24, push_to_github: bool = False, force: bool = False):
    """
    补充生成指定日期范围内的报告
    
    Args:
        start_date_str: 开始日期 (YYYY-MM-DD)
        end_date_str: 结束日期 (YYYY-MM-DD)
        interval_hours: 报告间隔小时数
        push_to_github: 是否推送到GitHub
        force: 是否强制重新生成已存在的报告
    """
    try:
        # 解析日期字符串
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        logger.info(f"开始补充生成报告，日期范围: {start_date_str} 到 {end_date_str}")
        
        # 如果不是强制模式，查找缺失的日期
        if not force:
            dates_to_generate = find_missing_dates(start_date, end_date, interval_hours)
            logger.info(f"找到 {len(dates_to_generate)} 个缺失的日期")
        else:
            # 强制模式下，生成所有日期的报告
            dates_to_generate = []
            current_date = start_date
            while current_date <= end_date:
                dates_to_generate.append(current_date)
                current_date += timedelta(hours=interval_hours)
            logger.info(f"强制模式: 将生成 {len(dates_to_generate)} 个日期的报告")
        
        # 生成报告
        success_count = 0
        for date in dates_to_generate:
            if generate_report_for_date(date, hours=interval_hours, push_to_github=push_to_github):
                success_count += 1
        
        logger.info(f"补充生成完成，成功: {success_count}/{len(dates_to_generate)}")
    
    except Exception as e:
        logger.error(f"补充生成报告时出错: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="补充生成缺失的报告")
    
    # 修改参数，使 start 和 end 不再是必需的
    parser.add_argument("--start", help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--interval", type=int, default=24, help="报告间隔小时数")
    parser.add_argument("--push", action="store_true", help="推送报告到GitHub")
    parser.add_argument("--force", action="store_true", help="强制重新生成已存在的报告")
    parser.add_argument("--single-date", help="单独生成特定日期的报告 (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    # 如果指定了单独日期，只生成该日期的报告
    if args.single_date:
        try:
            target_date = datetime.strptime(args.single_date, "%Y-%m-%d")
            logger.info(f"生成特定日期的报告: {args.single_date}")
            
            # 为特定时间生成报告
            success = generate_report_for_date(
                target_date=target_date,
                hours=args.interval,
                push_to_github=args.push
            )
            
            if success:
                logger.info(f"成功生成 {args.single_date} 的报告")
            else:
                logger.error(f"生成 {args.single_date} 的报告失败")
        except ValueError:
            logger.error(f"无效的日期格式: {args.single_date}，请使用 YYYY-MM-DD 格式")
    # 否则，检查是否提供了 start 和 end
    elif args.start and args.end:
        backfill_reports(args.start, args.end, args.interval, args.push, args.force)
    else:
        parser.error("必须提供 --single-date 或同时提供 --start 和 --end 参数")
    # 示例用法:
    # 1. 生成特定日期的报告:
    #    python backfill/backfill_reports.py --single-date 2023-09-15
    #
    # 2. 生成日期范围内的报告:
    #    python backfill/backfill_reports.py --start 2023-09-01 --end 2023-09-15
    #
    # 3. 生成日期范围内的报告并推送到GitHub:
    #    python backfill/backfill_reports.py --start 2023-09-01 --end 2023-09-15 --push
    #
    # 4. 强制重新生成特定日期的报告:
    #    python backfill/backfill_reports.py --single-date 2023-09-15 --force

if __name__ == "__main__":
    main() 