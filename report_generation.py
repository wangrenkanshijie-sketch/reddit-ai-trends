#!/usr/bin/env python3
"""
Reddit Post Trend Report Generation

This script generates reports on trending posts from Reddit AI communities.
"""

import os
import sys
import logging
import argparse
import schedule
import time
from datetime import datetime, timedelta
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_collection.reddit_collector import RedditDataCollector
from services.llm_processing.groq_client import GroqClient
from services.report_processor import ReportProcessor
from database.mongodb import MongoDBClient
from config import REPORT_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("report_generation.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_report_directory_structure(base_dir: str = "reports") -> str:
    """
    Create a directory structure for reports based on year/month/day.
    
    Args:
        base_dir: Base directory for reports
        
    Returns:
        Path to the created directory
    """
    now = datetime.now()
    year_dir = str(now.year)
    month_dir = f"{now.month:02d}"
    day_dir = f"{now.day:02d}"
    
    # Create the directory structure
    report_dir = os.path.join(base_dir, year_dir, month_dir, day_dir)
    os.makedirs(report_dir, exist_ok=True)
    
    logger.info(f"Created report directory: {report_dir}")
    return report_dir

def update_readme_with_latest_report(report_paths: Dict[str, str]) -> None:
    """
    Update both English and Chinese README files with links to the latest reports.
    
    Args:
        report_paths: Dictionary mapping language codes to report file paths
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    # Update English README
    update_english_readme(report_paths, date_str)
    
    # Update Chinese README
    update_chinese_readme(report_paths, date_str)
    
    logger.info(f"Updated README.md and README_CN.md with links to latest reports")

def update_english_readme(report_paths: Dict[str, str], date_str: str) -> None:
    """
    Update the English README.md with links to the latest reports.
    
    Args:
        report_paths: Dictionary mapping language codes to report file paths
        date_str: Current date string
    """
    readme_path = "README.md"
    
    # Read existing README to preserve language switcher
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Extract language switcher if it exists
            language_switcher = ""
            if "[English](README.md) | [中文](README_CN.md)" in content:
                language_switcher = "[English](README.md) | [中文](README_CN.md)\n\n"
    except FileNotFoundError:
        language_switcher = "[English](README.md) | [中文](README_CN.md)\n\n"
    
    # Create README content
    readme_content = f"# Reddit AI Trend Reports\n\n"
    readme_content += language_switcher
    readme_content += f"Automatically generate trend reports from AI-related Reddit communities, supporting both English and Chinese languages. Stay up-to-date with the latest developments in the AI field through daily reports.\n\n"
    readme_content += f"## Latest Reports ({date_str})\n\n"
    
    for lang, path in report_paths.items():
        lang_name = "English" if lang == "en" else "Chinese"
        relative_path = os.path.relpath(path, ".")
        readme_content += f"- [{lang_name} Report]({relative_path})\n"
    
    # Read the rest of the original README
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            original_content = f.read()
            # Find the position after the "Latest Reports" section
            features_section_start = original_content.find("## Features")
            if features_section_start != -1:
                readme_content += "\n" + original_content[features_section_start:]
    except FileNotFoundError:
        # If README doesn't exist, add a basic about section
        readme_content += "\n## About\n\n"
        readme_content += "This repository contains daily reports on trending posts from Reddit AI communities.\n"
        readme_content += "Reports are generated automatically every day at 6:00 AM US Central Time.\n"
    
    # Write to README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

def update_chinese_readme(report_paths: Dict[str, str], date_str: str) -> None:
    """
    Update the Chinese README_CN.md with links to the latest reports.
    
    Args:
        report_paths: Dictionary mapping language codes to report file paths
        date_str: Current date string
    """
    readme_path = "README_CN.md"
    
    # Read existing README to preserve language switcher
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Extract language switcher if it exists
            language_switcher = ""
            if "[English](README.md) | [中文](README_CN.md)" in content:
                language_switcher = "[English](README.md) | [中文](README_CN.md)\n\n"
    except FileNotFoundError:
        language_switcher = "[English](README.md) | [中文](README_CN.md)\n\n"
    
    # Create README content
    readme_content = f"# Reddit AI 趋势报告\n\n"
    readme_content += language_switcher
    readme_content += f"自动从Reddit AI相关社区生成趋势报告，支持英文和中文双语。通过每日报告，随时了解AI领域的最新发展。\n\n"
    readme_content += f"## 最新报告 ({date_str})\n\n"
    
    for lang, path in report_paths.items():
        lang_name = "英文" if lang == "en" else "中文"
        relative_path = os.path.relpath(path, ".")
        readme_content += f"- [{lang_name}报告]({relative_path})\n"
    
    # Read the rest of the original README
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            original_content = f.read()
            # Find the position after the introduction
            features_section_start = original_content.find("## 功能特点")
            if features_section_start != -1:
                readme_content += "\n" + original_content[features_section_start:]
    except FileNotFoundError:
        # If README doesn't exist, add a basic about section
        readme_content += "\n## 关于\n\n"
        readme_content += "此仓库包含来自Reddit AI社区的每日趋势报告。\n"
        readme_content += "报告每天在美国中部时间早上6:00自动生成。\n"
    
    # Write to README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

def generate_report(languages: List[str] = None) -> Dict[str, str]:
    """
    Generate a report on trending posts from Reddit AI communities.
    
    Args:
        languages: List of language codes to generate reports for
        
    Returns:
        Dictionary mapping language codes to report file paths
    """
    if languages is None:
        languages = REPORT_CONFIG.get('languages', ['en', 'zh'])
    
    logger.info(f"Starting report generation for languages: {languages}")
    start_time = time.time()
    
    try:
        # Initialize services
        reddit_collector = RedditDataCollector()
        report_processor = ReportProcessor()
        mongodb_client = MongoDBClient()
        
        # Get subreddits from config
        subreddits = REPORT_CONFIG.get('subreddits', [])
        posts_per_subreddit = REPORT_CONFIG.get('posts_per_subreddit', 100)
        
        # Collect data
        logger.info(f"Collecting data from subreddits: {subreddits}")
        posts_data = reddit_collector.collect_subreddit_data(subreddits, posts_per_subreddit)
        
        # Filter posts with more than 10 comments
        filtered_posts = [post for post in posts_data if post.get('num_comments', 0) > 10]
        logger.info(f"Filtered {len(filtered_posts)} posts with more than 10 comments from {len(posts_data)} total posts")
        
        # Get weekly and monthly popular posts
        weekly_posts = reddit_collector.collect_weekly_popular_posts(subreddits)
        monthly_posts = reddit_collector.collect_monthly_popular_posts(subreddits)
        
        # Get previous report data for comparison
        previous_data = mongodb_client.get_latest_report()
        
        # Generate reports in multiple languages
        reports = report_processor.generate_multilingual_reports(
            filtered_posts, 
            previous_data, 
            weekly_posts, 
            monthly_posts,
            languages
        )
        
        # Create directory structure
        report_dir = create_report_directory_structure()
        
        # Save reports to files
        report_paths = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for lang, report in reports.items():
            # Create filename
            filename = f"report_{timestamp}_{lang}.md"
            filepath = os.path.join(report_dir, filename)
            
            # Save report to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)
            
            # Create symlink for latest report
            latest_path = os.path.join("reports", f"latest_report_{lang}.md")
            if os.path.exists(latest_path):
                if os.path.islink(latest_path):
                    os.unlink(latest_path)
                else:
                    os.remove(latest_path)
            
            # Create relative path for symlink
            rel_path = os.path.relpath(filepath, os.path.dirname(latest_path))
            try:
                os.symlink(rel_path, latest_path)
                logger.info(f"Created symlink from {rel_path} to {latest_path}")
            except Exception as e:
                # On Windows, symlinks might not work without admin privileges
                logger.warning(f"Could not create symlink: {e}. Copying file instead.")
                shutil.copy2(filepath, latest_path)
            
            report_paths[lang] = filepath
            logger.info(f"Saved {lang} report to {filepath}")
        
        # Update README with links to latest reports
        update_readme_with_latest_report(report_paths)
        
        # Save report to MongoDB
        save_to_db = REPORT_CONFIG.get('save_to_mongodb', True)
        if save_to_db:
            mongodb_client.save_report(reports, filtered_posts, weekly_posts, monthly_posts)
            logger.info("Saved report to MongoDB")
        
        end_time = time.time()
        logger.info(f"Report generation completed in {end_time - start_time:.2f} seconds")
        
        return report_paths
    
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise

def schedule_report_generation(interval_hours: int = 24) -> None:
    """
    Schedule report generation to run at specified intervals.
    
    Args:
        interval_hours: Interval in hours between report generation runs
    """
    # Get generation time from config
    generation_time = REPORT_CONFIG.get('generation_time', "06:00")
    
    # Schedule job
    logger.info(f"Scheduling report generation to run daily at {generation_time}")
    schedule.every().day.at(generation_time).do(generate_report)
    
    # Run immediately if interval is 0
    if interval_hours == 0:
        logger.info("Running report generation immediately")
        generate_report()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate reports on trending posts from Reddit AI communities")
    parser.add_argument("--interval", type=int, default=24, help="Interval in hours between report generation runs")
    parser.add_argument("--languages", nargs="+", default=None, help="Languages to generate reports for (e.g., en zh)")
    args = parser.parse_args()
    
    if args.languages:
        # Run once with specified languages
        generate_report(args.languages)
    else:
        # Schedule with default languages from config
        schedule_report_generation(args.interval) 