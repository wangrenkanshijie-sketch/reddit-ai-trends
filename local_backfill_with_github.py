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
        
        # 初始化服务
        from services.reddit_collection.collector import RedditDataCollector
        from services.llm_processing.report_processor import ReportProcessor
        from database.mongodb import MongoDBClient
        from config import REPORT_CONFIG
        from report_generation import create_report_directory_structure, update_readme_with_latest_report
        
        # 使用Reddit收集器获取数据
        reddit_collector = RedditDataCollector()
        report_processor = ReportProcessor()
        mongodb_client = MongoDBClient()
        
        # 计算时间范围
        end_time = target_date
        start_time_range = end_time - timedelta(hours=hours)
        logger.info(f"收集帖子，时间范围: {start_time_range} 到 {end_time}")
        
        # 使用配置中的subreddits
        subreddits = REPORT_CONFIG.get('subreddits', [])
        posts_per_subreddit = REPORT_CONFIG.get('posts_per_subreddit', 30)
        languages = REPORT_CONFIG.get('languages', ["en", "zh"])
        
        # 收集所有帖子
        all_posts = []
        for subreddit in subreddits:
            posts = reddit_collector.get_subreddit_posts(
                subreddit=subreddit,
                limit=posts_per_subreddit,
                time_filter="week"
            )
            # 根据时间范围过滤帖子
            filtered_by_time = []
            for post in posts:
                post_time = post.get('created_utc')
                if isinstance(post_time, str):
                    try:
                        post_time = datetime.fromisoformat(post_time.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                if post_time and start_time_range <= post_time <= end_time:
                    filtered_by_time.append(post)
            
            all_posts.extend(filtered_by_time)
        
        # 过滤评论数大于10的帖子
        filtered_posts = [post for post in all_posts if post.get('num_comments', 0) > 10]
        logger.info(f"过滤后得到 {len(filtered_posts)} 个帖子")
        
        # 获取周报和月报数据
        weekly_posts = reddit_collector.get_weekly_popular_posts(subreddits)
        monthly_posts = reddit_collector.get_monthly_popular_posts(subreddits)
        
        # 获取上一个报告作为比较
        previous_report = mongodb_client.get_latest_report()
        
        # 生成多语言报告
        reports = report_processor.generate_multilingual_reports(
            filtered_posts, 
            previous_report, 
            weekly_posts, 
            monthly_posts,
            languages,
            save_to_file=False  # 我们将自己处理文件保存
        )
        
        # 创建目录结构
        year = target_date.year
        month = f"{target_date.month:02d}"
        day = f"{target_date.day:02d}"
        report_dir = os.path.join("reports", str(year), month, day)
        os.makedirs(report_dir, exist_ok=True)
        logger.info(f"创建目录: {report_dir}")
        
        # 保存报告到文件
        report_paths = {}
        date_str = target_date.strftime("%Y%m%d")
        
        for lang, report in reports.items():
            # 获取报告内容
            report_content = None
            if isinstance(report, dict):
                if "content" in report:
                    report_content = report["content"]
            else:
                report_content = report
            
            if report_content:
                # 获取当前日期字符串格式
                current_date = datetime.now().strftime("%Y-%m-%d")
                # 获取目标日期字符串格式
                target_date_formatted = target_date.strftime("%Y-%m-%d")
                
                # 替换日期 - 英文格式
                report_content = report_content.replace(f"- {current_date}", f"- {target_date_formatted}")
                report_content = report_content.replace(f"Report - {current_date}", f"Report - {target_date_formatted}")
            
            # 创建文件名，去掉时间戳部分
            filename = f"report_{date_str}_{lang}.md"
            filepath = os.path.join(report_dir, filename)
            
            # 保存报告到文件
            with open(filepath, "w", encoding="utf-8") as f:
                # 处理不同格式的报告
                if isinstance(report, dict):
                    if "content" in report:
                        f.write(report["content"])
                    else:
                        f.write(str(report))
                else:
                    f.write(report)
            
            logger.info(f"保存 {lang} 报告到 {filepath}")
            
            # 创建最新报告的符号链接
            latest_path = os.path.join("reports", f"latest_report_{lang}.md")
            if os.path.exists(latest_path):
                try:
                    os.remove(latest_path)
                except Exception as e:
                    logger.warning(f"无法删除旧链接: {e}")
            
            # 复制文件而不是创建符号链接
            try:
                import shutil
                shutil.copy2(filepath, latest_path)
                logger.info(f"复制文件到: {latest_path}")
            except Exception as e:
                logger.error(f"复制文件失败: {e}")
            
            report_paths[lang] = filepath
        
        # 更新README文件
        update_readme_with_latest_report(report_paths)
        
        # 保存到MongoDB
        if isinstance(reports, dict):
            mongodb_client.save_report(reports, filtered_posts, weekly_posts, monthly_posts)
            logger.info("保存报告到MongoDB")
        
        logger.info(f"报告成功生成在: {report_dir}")
        return True, report_dir
        
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