#!/usr/bin/env python3
"""
Multilingual Report Generation Test Script

This script tests the generation of reports in multiple languages.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import services
from services.reddit_collection.collector import RedditDataCollector
from services.llm_processing.report_processor import ReportProcessor
from database.mongodb import MongoDBClient
from config import REPORT_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("multilingual_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_multilingual_reports():
    """
    Test the generation of reports in multiple languages.
    """
    try:
        logger.info("Starting multilingual report generation test")
        
        # Initialize services
        reddit_collector = RedditDataCollector()
        report_processor = ReportProcessor()
        
        # Use subreddits from config
        subreddits = REPORT_CONFIG['subreddits']
        
        # Collect data from each subreddit
        all_posts = []
        for subreddit in subreddits:
            logger.info(f"Collecting data from r/{subreddit}")
            posts = reddit_collector.get_subreddit_posts(
                subreddit=subreddit,
                limit=REPORT_CONFIG['posts_per_subreddit'],
                time_filter="day"
            )
            
            # Filter posts with more than 10 comments
            filtered_posts = [post for post in posts if post.get('num_comments', 0) > 10]
            logger.info(f"Collected {len(filtered_posts)} posts with >10 comments from r/{subreddit}")
            
            all_posts.extend(filtered_posts)
        
        # Collect weekly popular posts
        logger.info("Collecting weekly popular posts")
        weekly_posts = reddit_collector.get_weekly_popular_posts(
            subreddits=subreddits,
            limit=20
        )
        logger.info(f"Collected {len(weekly_posts)} weekly popular posts")
        
        # Collect monthly popular posts
        logger.info("Collecting monthly popular posts")
        monthly_posts = reddit_collector.get_monthly_popular_posts(
            subreddits=subreddits,
            limit=20
        )
        logger.info(f"Collected {len(monthly_posts)} monthly popular posts")
        
        # Generate reports in multiple languages
        languages = ["en", "zh"]
        logger.info(f"Generating reports in languages: {', '.join(languages)}")
        
        reports = report_processor.generate_multilingual_reports(
            posts=all_posts,
            weekly_posts=weekly_posts,
            monthly_posts=monthly_posts,
            languages=languages
        )
        
        # Save reports to files
        os.makedirs("reports", exist_ok=True)
        
        for lang, report in reports.items():
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/test_report_{timestamp}_{lang}.md"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report["content"])
            
            logger.info(f"Saved {lang} report to file: {filename}")
        
        logger.info("Multilingual report generation test completed successfully")
        
        # Ask user if they want to save to MongoDB
        save_to_db = input("Do you want to save these reports to MongoDB? (y/n): ").lower() == 'y'
        
        if save_to_db:
            mongodb_client = MongoDBClient()
            for lang, report in reports.items():
                report_id = mongodb_client.insert_report(report)
                logger.info(f"Saved {lang} report to MongoDB with ID: {report_id}")
            logger.info("All reports saved to MongoDB")
        
        return reports
    
    except Exception as e:
        logger.error(f"Error in multilingual report test: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    test_multilingual_reports() 