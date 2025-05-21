#!/usr/bin/env python3
"""
本地回填测试脚本：为特定日期生成报告并自动提交到GitHub

此脚本用于测试整个回填流程：
1. 为特定日期生成报告
2. 创建年/月/日目录结构
3. 自动提交到GitHub
"""

import os
import sys
import logging
import subprocess
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入backfill功能
from backfill.backfill_reports import generate_report_for_date

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("local_backfill.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_command(command):
    """
    运行shell命令并返回输出
    
    Args:
        command: 要运行的命令
        
    Returns:
        命令的输出
    """
    logger.info(f"运行命令: {command}")
    try:
        # 设置环境变量PYTHONPATH，确保Python能找到模块
        env = os.environ.copy()
        env['PYTHONPATH'] = current_dir
        
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        logger.info(f"命令输出: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e}")
        logger.error(f"错误输出: {e.stderr}")
        raise

def backfill_report(target_date_str, hours=24, push_to_github=False):
    """
    为特定日期生成回填报告
    
    Args:
        target_date_str: 目标日期字符串 (YYYY-MM-DD)
        hours: 回溯的小时数
        push_to_github: 是否推送到GitHub
        
    Returns:
        (bool, str): 成功状态和报告目录
    """
    logger.info(f"开始为日期 {target_date_str} 生成回填报告...")
    
    try:
        # 解析日期字符串
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        
        # 使用backfill模块生成报告
        success = generate_report_for_date(
            target_date=target_date,
            hours=hours,
            push_to_github=False  # 这里设为False，我们将在后面手动处理GitHub提交
        )
        
        if success:
            # 构建报告目录路径
            year = target_date.year
            month = f"{target_date.month:02d}"
            day = f"{target_date.day:02d}"
            report_dir = os.path.join("reports", str(year), month, day)
            
            if os.path.exists(report_dir):
                logger.info(f"报告生成成功，保存在: {report_dir}")
                return True, report_dir
            else:
                logger.error(f"报告似乎生成成功，但目录不存在: {report_dir}")
                return False, None
        else:
            logger.error("报告生成失败")
            return False, None
    except Exception as e:
        logger.error(f"回填报告生成失败: {e}", exc_info=True)
        return False, None

def verify_directory_structure(report_dir):
    """
    验证目录结构是否正确创建
    
    Args:
        report_dir: 报告目录路径
    
    Returns:
        bool: 是否成功创建
    """
    logger.info(f"验证目录结构: {report_dir}")
    
    # 检查目录是否存在
    if os.path.exists(report_dir) and os.path.isdir(report_dir):
        logger.info(f"目录结构验证成功: {report_dir}")
        
        # 检查目录中是否有报告文件
        report_files = [f for f in os.listdir(report_dir) if f.endswith(".md")]
        if report_files:
            logger.info(f"找到报告文件: {report_files}")
            return True
        else:
            logger.warning(f"目录存在但没有找到报告文件: {report_dir}")
            return False
    else:
        logger.error(f"目录结构验证失败，目录不存在: {report_dir}")
        return False

def commit_to_github(report_dir, date_str):
    """
    将生成的报告提交到GitHub
    
    Args:
        report_dir: 报告目录路径
        date_str: 日期字符串，用于提交信息
        
    Returns:
        bool: 是否成功提交
    """
    logger.info(f"准备提交报告到GitHub: {report_dir}")
    
    try:
        # 确保reports/.gitkeep文件存在
        gitkeep_path = os.path.join("reports", ".gitkeep")
        if not os.path.exists(gitkeep_path):
            Path(gitkeep_path).touch()
            logger.info(f"创建了 {gitkeep_path} 文件")
        
        # 添加所有报告文件，使用-f强制添加被忽略的文件
        run_command(f"git add reports/.gitkeep")
        run_command(f"git add -f {report_dir}")
        
        # 添加latest_report文件
        run_command(f"git add -f reports/latest_report_en.md")
        run_command(f"git add -f reports/latest_report_zh.md")
        
        # 添加README.md和README_CN.md（它们会被自动更新）
        run_command("git add README.md README_CN.md")
        
        # 提交更改
        run_command(f'git commit -m "Add backfilled reports for {date_str}"')
        
        # 推送到GitHub
        run_command("git push")
        
        logger.info("成功提交到GitHub")
        return True
    except Exception as e:
        logger.error(f"提交到GitHub失败: {e}")
        return False

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="为特定日期生成回填报告并提交到GitHub")
    parser.add_argument("--date", required=True, help="目标日期 (YYYY-MM-DD)")
    parser.add_argument("--hours", type=int, default=24, help="回溯的小时数")
    parser.add_argument("--skip-github", action="store_true", help="跳过GitHub提交")
    
    args = parser.parse_args()
    
    logger.info(f"开始为日期 {args.date} 生成回填报告...")
    
    # 步骤1: 生成回填报告
    success, report_dir = backfill_report(args.date, args.hours)
    if not success:
        logger.error("测试失败: 回填报告生成失败")
        return False
    
    # 等待一下，确保文件写入完成
    time.sleep(2)
    
    # 步骤2: 验证目录结构
    if not verify_directory_structure(report_dir):
        logger.error("测试失败: 目录结构验证失败")
        return False
    
    # 步骤3: 提交到GitHub
    if not args.skip_github:
        if not commit_to_github(report_dir, args.date):
            logger.error("测试失败: 提交到GitHub失败")
            return False
    else:
        logger.info("根据参数设置，跳过GitHub提交")
    
    logger.info(f"为日期 {args.date} 的回填报告生成测试成功完成！")
    return True

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.exception(f"测试过程中发生未处理的异常: {e}")
        sys.exit(1)