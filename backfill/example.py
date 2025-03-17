#!/usr/bin/env python3
"""
Example Script for Backfill Tools

此脚本演示如何使用补充生成工具来检查和生成缺失的报告。
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入补充生成工具
from backfill.check_missing_reports import check_missing_reports
from backfill.backfill_reports import backfill_reports

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    # 获取当前日期
    today = datetime.now()
    
    # 计算过去30天的日期范围
    end_date = today.strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    
    logger.info(f"示例1: 检查过去30天缺失的报告 ({start_date} 到 {end_date})")
    
    # 检查缺失的报告
    output_file = "backfill/missing_reports_last_30_days.txt"
    check_missing_reports(start_date, end_date, output_file=output_file)
    
    # 读取缺失报告列表
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            content = f.read()
            logger.info(f"缺失报告检查结果:\n{content}")
    
    logger.info("\n" + "-" * 50 + "\n")
    
    # 示例2: 补充生成最近7天缺失的报告
    end_date = today.strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    
    logger.info(f"示例2: 补充生成最近7天缺失的报告 ({start_date} 到 {end_date})")
    logger.info("注意: 这只是一个演示，不会实际生成报告。如需生成，请取消下面代码的注释。")
    
    # 取消下面的注释来实际生成报告
    # backfill_reports(start_date, end_date, push_to_github=False)
    
    logger.info("\n" + "-" * 50 + "\n")
    
    # 示例3: 强制重新生成特定日期的报告
    specific_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    logger.info(f"示例3: 强制重新生成特定日期的报告 ({specific_date})")
    logger.info("注意: 这只是一个演示，不会实际生成报告。如需生成，请取消下面代码的注释。")
    
    # 取消下面的注释来实际生成报告
    # backfill_reports(specific_date, specific_date, force=True, push_to_github=False)
    
    logger.info("\n完成演示。")

if __name__ == "__main__":
    main() 