#!/usr/bin/env python3
"""
简化的测试脚本，用于测试Reddit数据收集、解析、存储到数据库和生成Markdown报告的流程。
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入服务
from services.reddit_collection.collector import RedditDataCollector
from services.llm_processing.report_processor import ReportProcessor
from database.mongodb import MongoDBClient
from config import REPORT_CONFIG, REDDIT_COMMUNITIES

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_simple_test():
    """
    运行简化的测试流程，使用配置文件中定义的所有subreddit。
    """
    try:
        logger.info("=== 开始简化测试 ===")
        
        # 初始化服务
        reddit_collector = RedditDataCollector()
        report_processor = ReportProcessor()
        mongodb_client = MongoDBClient()
        
        # 获取所有需要收集的subreddit
        subreddits = []
        
        # 从high_priority和medium_priority中获取具体的subreddit
        if isinstance(REDDIT_COMMUNITIES, dict):
            # 如果REDDIT_COMMUNITIES是字典格式
            for priority, communities in REDDIT_COMMUNITIES.items():
                if isinstance(communities, dict):
                    # 如果communities是字典（如{"LocalLLaMA": 30}）
                    subreddits.extend(communities.keys())
                elif isinstance(communities, list):
                    # 如果communities是列表
                    subreddits.extend(communities)
        else:
            # 如果REDDIT_COMMUNITIES是列表格式
            subreddits = REDDIT_COMMUNITIES
        
        # 确保subreddit列表中没有重复
        subreddits = list(set(subreddits))
        
        logger.info(f"将测试以下subreddit: {', '.join(subreddits)}")
        
        # 步骤1: 收集Reddit数据
        logger.info("步骤1: 从所有配置的subreddit收集数据")
        all_filtered_posts = []
        
        for subreddit in subreddits:
            logger.info(f"从r/{subreddit}收集数据")
            posts = reddit_collector.get_subreddit_posts(
                subreddit=subreddit,
                limit=REPORT_CONFIG.get('posts_per_subreddit', 100),
                time_filter="day"
            )
            
            # 过滤评论数超过10的帖子
            filtered_posts = [post for post in posts if post.get('num_comments', 0) > 10]
            logger.info(f"从r/{subreddit}收集到{len(posts)}个帖子，其中{len(filtered_posts)}个帖子评论数超过10")
            
            all_filtered_posts.extend(filtered_posts)
        
        logger.info(f"总共收集到{len(all_filtered_posts)}个评论数超过10的帖子")
        
        # 步骤2: 收集每周和每月热门帖子
        logger.info("步骤2: 收集每周和每月热门帖子")
        weekly_posts = reddit_collector.get_weekly_popular_posts(
            subreddits=subreddits,
            limit=20
        )
        logger.info(f"收集到{len(weekly_posts)}个每周热门帖子")
        
        monthly_posts = reddit_collector.get_monthly_popular_posts(
            subreddits=subreddits,
            limit=20
        )
        logger.info(f"收集到{len(monthly_posts)}个每月热门帖子")
        
        # 步骤3: 将数据保存到MongoDB
        logger.info("步骤3: 将数据保存到MongoDB")
        
        # 合并所有帖子
        all_posts = all_filtered_posts + weekly_posts + monthly_posts
        
        # 去除重复帖子
        unique_posts = {}
        for post in all_posts:
            post_id = post.get('post_id')
            if post_id:
                unique_posts[post_id] = post
        
        all_posts_to_save = list(unique_posts.values())
        
        # 保存到MongoDB
        result = mongodb_client.insert_or_update_posts(all_posts_to_save)
        logger.info(f"保存了{result['inserted']}个新帖子，更新了{result['updated']}个已有帖子")
        
        # 获取最新报告用于比较
        previous_report = mongodb_client.get_latest_report()
        if previous_report:
            logger.info(f"找到之前的报告，ID: {previous_report.get('report_id')}")
        else:
            logger.info("没有找到之前的报告")
        
        # 步骤4: 生成报告
        logger.info("步骤4: 生成报告")
        report = report_processor.generate_report(
            posts=all_filtered_posts,
            previous_report=previous_report,
            weekly_posts=weekly_posts,
            monthly_posts=monthly_posts
        )
        
        logger.info(f"生成了报告，ID: {report.get('report_id')}")
        logger.info(f"报告内容长度: {len(report.get('content', ''))}")
        
        # 处理报告内容，移除<think>标记中的内容
        content = report.get('content', '')
        cleaned_content = remove_think_blocks(content)
        report['content'] = cleaned_content
        
        # 步骤5: 保存报告到MongoDB
        logger.info("步骤5: 保存报告到MongoDB")
        report_id = mongodb_client.insert_report(report)
        logger.info(f"报告已保存到MongoDB，ID: {report_id}")
        
        # 步骤6: 保存报告到文件
        logger.info("步骤6: 保存报告到文件")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"simple_test_report_{timestamp}.md"
        
        # 创建reports目录（如果不存在）
        os.makedirs("reports", exist_ok=True)
        filepath = os.path.join("reports", filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report["content"])
        
        logger.info(f"报告已保存到文件: {filepath}")
        
        # 关闭MongoDB连接
        mongodb_client.close()
        
        logger.info("=== 简化测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}", exc_info=True)

def remove_think_blocks(text):
    """
    移除文本中<think>标记之间的内容。
    
    Args:
        text: 原始文本
        
    Returns:
        处理后的文本
    """
    import re
    # 使用正则表达式移除<think>...</think>块
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned_text

if __name__ == "__main__":
    run_simple_test() 