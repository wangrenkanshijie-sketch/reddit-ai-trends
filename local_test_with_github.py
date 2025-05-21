#!/usr/bin/env python3
"""
本地测试脚本：生成报告、创建目录结构并自动提交到GitHub

此脚本用于测试整个流程：
1. 生成报告
2. 创建年/月/日目录结构
3. 自动提交到GitHub
"""

import os
import sys
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入服务
from services.reddit_collection.collector import RedditDataCollector
from services.llm_processing.report_processor import ReportProcessor
from database.mongodb import MongoDBClient
from config import REPORT_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("local_test.log"),
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

def generate_report():
    """
    直接生成报告，不通过调用外部脚本
    """
    logger.info("开始生成报告...")
    try:
        # 初始化服务
        reddit_collector = RedditDataCollector()
        report_processor = ReportProcessor()
        mongodb_client = MongoDBClient()
        
        # 使用配置中的subreddits
        subreddits = REPORT_CONFIG['subreddits']
        languages = ["en", "zh"]
        
        # 收集数据
        logger.info(f"从以下subreddits收集数据: {subreddits}")
        
        # 收集所有帖子
        all_posts = []
        for subreddit in subreddits:
            logger.info(f"从r/{subreddit}收集数据")
            posts = reddit_collector.get_subreddit_posts(
                subreddit=subreddit,
                limit=REPORT_CONFIG.get('posts_per_subreddit', 10),
                time_filter="day"
            )
            
            # 过滤评论数大于10的帖子
            filtered_posts = [post for post in posts if post.get('num_comments', 0) > 10]
            logger.info(f"从r/{subreddit}收集到{len(filtered_posts)}个评论数>10的帖子")
            
            all_posts.extend(filtered_posts)
        
        # 收集每周热门帖子
        logger.info("收集每周热门帖子")
        weekly_posts = reddit_collector.get_weekly_popular_posts(
            subreddits=subreddits,
            limit=20
        )
        logger.info(f"收集到{len(weekly_posts)}个每周热门帖子")
        
        # 收集每月热门帖子
        logger.info("收集每月热门帖子")
        monthly_posts = reddit_collector.get_monthly_popular_posts(
            subreddits=subreddits,
            limit=20
        )
        logger.info(f"收集到{len(monthly_posts)}个每月热门帖子")
        
        # 生成多语言报告内容，但不保存文件
        logger.info(f"生成以下语言的报告: {', '.join(languages)}")
        
        reports = report_processor.generate_multilingual_reports(
            posts=all_posts,
            weekly_posts=weekly_posts,
            monthly_posts=monthly_posts,
            languages=languages,
            save_to_file=False  # 不要在ReportProcessor中保存文件
        )
        
        # 创建年/月/日目录结构
        now = datetime.now()
        year_dir = str(now.year)
        month_dir = f"{now.month:02d}"
        day_dir = f"{now.day:02d}"
        
        report_dir = os.path.join("reports", year_dir, month_dir, day_dir)
        os.makedirs(report_dir, exist_ok=True)
        
        # 手动删除目录中的所有.md文件
        for filename in os.listdir(report_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(report_dir, filename)
                try:
                    os.remove(file_path)
                    logger.info(f"删除旧文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除文件失败: {e}")
        
        # 保存报告到文件
        report_paths = {}
        
        # 获取当前日期，格式为YYYYMMDD
        date_str = now.strftime("%Y%m%d")
        
        for lang, report in reports.items():
            # 创建带日期的文件名：report_YYYYMMDD_lang.md
            filename = f"report_{date_str}_{lang}.md"
            filepath = os.path.join(report_dir, filename)
            
            # 写入内容到文件
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report["content"])
            logger.info(f"创建报告文件: {filepath}")
            
            # 创建最新报告的符号链接或复制文件
            latest_path = os.path.join("reports", f"latest_report_{lang}.md")
            if os.path.exists(latest_path):
                try:
                    os.remove(latest_path)
                except Exception as e:
                    logger.error(f"删除旧链接失败: {e}")
            
            # 在Windows上，直接复制文件而不是创建符号链接
            try:
                import shutil
                shutil.copy2(filepath, latest_path)
                logger.info(f"复制文件到: {latest_path}")
            except Exception as e:
                logger.error(f"复制文件失败: {e}")
            
            report_paths[lang] = filepath
        
        # 更新README文件
        from report_generation import update_readme_with_latest_report
        update_readme_with_latest_report(report_paths)
        
        # 保存到MongoDB
        for lang, report in reports.items():
            report_id = mongodb_client.insert_report(report)
            logger.info(f"保存{lang}报告到MongoDB，ID: {report_id}")
        
        logger.info("报告生成成功")
        return True, report_dir
    except Exception as e:
        logger.error(f"报告生成失败: {e}", exc_info=True)
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

def commit_to_github(report_dir):
    """
    将生成的报告提交到GitHub
    
    Args:
        report_dir: 报告目录路径
    
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
        current_date = datetime.now().strftime("%Y-%m-%d")
        run_command(f'git commit -m "Add reports for {current_date}"')
        
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
    logger.info("开始测试流程...")
    
    # 步骤1: 生成报告
    success, report_dir = generate_report()
    if not success:
        logger.error("测试失败: 报告生成失败")
        return False
    
    # 等待一下，确保文件写入完成
    time.sleep(2)
    
    # 步骤2: 验证目录结构
    if not verify_directory_structure(report_dir):
        logger.error("测试失败: 目录结构验证失败")
        return False
    
    # 步骤3: 提交到GitHub
    if not commit_to_github(report_dir):
        logger.error("测试失败: 提交到GitHub失败")
        return False
    
    logger.info("测试成功完成！")
    return True

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.exception(f"测试过程中发生未处理的异常: {e}")
        sys.exit(1) 
