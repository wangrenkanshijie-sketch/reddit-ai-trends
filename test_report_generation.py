#!/usr/bin/env python3
"""
Test Script for Reddit Post Trend Report Generation

This script tests various components of the report generation system.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import services
from services.reddit_collection.collector import RedditDataCollector
from services.llm_processing.report_processor import ReportProcessor
from services.llm_processing.groq_client import GroqClient
from database.mongodb import MongoDBClient
# from services.github.github_integration import GitHubIntegration
# from services.docker.docker_integration import DockerIntegration
from config import REPORT_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_report_generation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_reddit_collection(subreddit: str = "artificial") -> List[Dict[str, Any]]:
    """
    Test Reddit data collection.
    
    Args:
        subreddit: Subreddit to collect data from
        
    Returns:
        List of collected posts
    """
    try:
        logger.info(f"Testing Reddit data collection from r/{subreddit}")
        
        # Initialize Reddit collector
        reddit_collector = RedditDataCollector()
        
        # Get posts from subreddit
        posts = reddit_collector.get_subreddit_posts(
            subreddit=subreddit,
            limit=REPORT_CONFIG['posts_per_subreddit']
        )
        
        # Filter posts with more than 10 comments
        filtered_posts = [post for post in posts if post.get('num_comments', 0) > 10]
        
        logger.info(f"Collected {len(posts)} posts from r/{subreddit}")
        logger.info(f"Found {len(filtered_posts)} posts with more than 10 comments")
        
        # Print some sample data
        if filtered_posts:
            sample_post = filtered_posts[0]
            logger.info(f"Sample post title: {sample_post.get('title')}")
            logger.info(f"Sample post score: {sample_post.get('score')}")
            logger.info(f"Sample post comments: {sample_post.get('num_comments')}")
        
        return filtered_posts
    
    except Exception as e:
        logger.error(f"Error testing Reddit data collection: {e}", exc_info=True)
        return []

def test_weekly_monthly_collection(subreddit: str = "artificial") -> Dict[str, List[Dict[str, Any]]]:
    """
    Test weekly and monthly post collection.
    
    Args:
        subreddit: Subreddit to collect data from
        
    Returns:
        Dictionary with weekly and monthly posts
    """
    try:
        logger.info(f"Testing weekly and monthly post collection from r/{subreddit}")
        
        # Initialize Reddit collector
        reddit_collector = RedditDataCollector()
        
        # Get weekly popular posts
        weekly_posts = reddit_collector.get_weekly_popular_posts(
            subreddits=[subreddit],
            limit=20
        )
        logger.info(f"Collected {len(weekly_posts)} weekly popular posts from r/{subreddit}")
        
        # Get monthly popular posts
        monthly_posts = reddit_collector.get_monthly_popular_posts(
            subreddits=[subreddit],
            limit=20
        )
        logger.info(f"Collected {len(monthly_posts)} monthly popular posts from r/{subreddit}")
        
        return {
            'weekly': weekly_posts,
            'monthly': monthly_posts
        }
    
    except Exception as e:
        logger.error(f"Error testing weekly/monthly collection: {e}", exc_info=True)
        return {'weekly': [], 'monthly': []}

def test_llm_processing(posts: List[Dict[str, Any]], 
                       weekly_posts: List[Dict[str, Any]] = None,
                       monthly_posts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Test LLM processing.
    
    Args:
        posts: List of posts to process
        weekly_posts: List of weekly popular posts
        monthly_posts: List of monthly popular posts
        
    Returns:
        Generated report
    """
    try:
        logger.info("Testing LLM processing")
        
        # Initialize report processor
        report_processor = ReportProcessor()
        
        # Generate report
        report = report_processor.generate_report(
            posts=posts,
            weekly_posts=weekly_posts,
            monthly_posts=monthly_posts
        )
        
        logger.info(f"Generated report with ID: {report.get('report_id')}")
        logger.info(f"Report content length: {len(report.get('content', ''))}")
        
        # Save report to file for inspection
        filename = "test_report.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report["content"])
        
        logger.info(f"Saved test report to file: {filename}")
        
        return report
    
    except Exception as e:
        logger.error(f"Error testing LLM processing: {e}", exc_info=True)
        return {}

def test_table_generation(posts: List[Dict[str, Any]], 
                         weekly_posts: List[Dict[str, Any]] = None,
                         monthly_posts: List[Dict[str, Any]] = None) -> None:
    """
    Test table generation functionality.
    
    Args:
        posts: List of posts to process
        weekly_posts: List of weekly popular posts
        monthly_posts: List of monthly popular posts
    """
    try:
        logger.info("Testing table generation")
        
        # Initialize Groq client
        groq_client = GroqClient()
        
        # Generate trending posts table
        trending_table = groq_client._create_trending_posts_table(posts)
        logger.info("Generated trending posts table")
        
        # Generate weekly popular posts table if provided
        weekly_table = ""
        if weekly_posts:
            weekly_table = groq_client._create_weekly_popular_table(weekly_posts)
            logger.info("Generated weekly popular posts table")
        
        # Generate monthly popular posts table if provided
        monthly_table = ""
        if monthly_posts:
            monthly_table = groq_client._create_monthly_popular_table(monthly_posts)
            logger.info("Generated monthly popular posts table")
        
        # Save tables to file for inspection
        with open("test_tables.md", "w", encoding="utf-8") as f:
            f.write("# Test Tables\n\n")
            if monthly_table:
                f.write(monthly_table)
                f.write("\n\n")
            if weekly_table:
                f.write(weekly_table)
                f.write("\n\n")
            f.write(trending_table)
        
        logger.info("Saved test tables to file: test_tables.md")
    
    except Exception as e:
        logger.error(f"Error testing table generation: {e}", exc_info=True)

def test_mongodb(posts: List[Dict[str, Any]], report: Dict[str, Any]) -> None:
    """
    Test MongoDB functionality.
    
    Args:
        posts: List of posts to store
        report: Report to store
    """
    try:
        logger.info("Testing MongoDB functionality")
        
        # Initialize MongoDB client
        mongodb_client = MongoDBClient()
        
        # Insert posts
        result = mongodb_client.insert_or_update_posts(posts)
        logger.info(f"Inserted {result['inserted']} new posts and updated {result['updated']} existing posts")
        
        # Insert report
        report_id = mongodb_client.insert_report(report)
        logger.info(f"Inserted report with ID: {report_id}")
        
        # Get latest report
        latest_report = mongodb_client.get_latest_report()
        logger.info(f"Retrieved latest report with ID: {latest_report.get('report_id')}")
        
        # Test post metrics history
        if posts:
            sample_post_id = posts[0].get('post_id')
            metrics_history = mongodb_client.get_post_metrics_history(sample_post_id)
            logger.info(f"Retrieved {len(metrics_history)} historical metrics for post {sample_post_id}")
        
        # Close connection
        mongodb_client.close()
        logger.info("MongoDB connection closed")
    
    except Exception as e:
        logger.error(f"Error testing MongoDB functionality: {e}", exc_info=True)

def test_github_integration() -> None:
    """Test GitHub integration."""
    try:
        logger.info("Testing GitHub integration")
        
        # Initialize GitHub integration
        github_integration = GitHubIntegration()
        
        # Check if repository is initialized
        is_initialized = github_integration.is_repo_initialized()
        logger.info(f"Repository initialized: {is_initialized}")
        
        if not is_initialized:
            # Initialize repository
            github_integration.init_repo()
            logger.info("Repository initialized")
        
        logger.info("GitHub integration test completed")
    
    except Exception as e:
        logger.error(f"Error testing GitHub integration: {e}", exc_info=True)

def test_docker_integration() -> None:
    """Test Docker integration."""
    try:
        logger.info("Testing Docker integration")
        
        # Initialize Docker integration
        docker_integration = DockerIntegration()
        
        # Set up Docker environment
        docker_integration.setup()
        logger.info("Docker environment set up")
        
        logger.info("Docker integration test completed")
    
    except Exception as e:
        logger.error(f"Error testing Docker integration: {e}", exc_info=True)

def test_comparison_with_previous_report() -> None:
    """Test comparison with previous report."""
    try:
        logger.info("Testing comparison with previous report")
        
        # Initialize services
        mongodb_client = MongoDBClient()
        report_processor = ReportProcessor()
        reddit_collector = RedditDataCollector()
        
        # Get latest report
        previous_report = mongodb_client.get_latest_report()
        
        if not previous_report:
            logger.info("No previous report found, skipping comparison test")
            return
        
        logger.info(f"Found previous report with ID: {previous_report.get('report_id')}")
        
        # Get new posts
        posts = reddit_collector.get_subreddit_posts(
            subreddit="artificial",
            limit=REPORT_CONFIG['posts_per_subreddit']
        )
        
        # Filter posts with more than 10 comments
        filtered_posts = [post for post in posts if post.get('num_comments', 0) > 10]
        
        # Get weekly and monthly posts
        weekly_posts = reddit_collector.get_weekly_popular_posts(
            subreddits=["artificial"],
            limit=20
        )
        
        monthly_posts = reddit_collector.get_monthly_popular_posts(
            subreddits=["artificial"],
            limit=20
        )
        
        # Generate report with comparison
        report = report_processor.generate_report(
            posts=filtered_posts,
            previous_report=previous_report,
            weekly_posts=weekly_posts,
            monthly_posts=monthly_posts
        )
        
        logger.info(f"Generated report with comparison, ID: {report.get('report_id')}")
        
        # Save report to file for inspection
        filename = "test_comparison_report.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report["content"])
        
        logger.info(f"Saved comparison test report to file: {filename}")
        
        # Close connection
        mongodb_client.close()
    
    except Exception as e:
        logger.error(f"Error testing comparison with previous report: {e}", exc_info=True)

def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(description="Test Reddit Post Trend Report Generation")
    
    # Add arguments
    parser.add_argument("--reddit", action="store_true", help="Test Reddit data collection")
    parser.add_argument("--weekly-monthly", action="store_true", help="Test weekly and monthly post collection")
    parser.add_argument("--llm", action="store_true", help="Test LLM processing")
    parser.add_argument("--tables", action="store_true", help="Test table generation")
    parser.add_argument("--mongodb", action="store_true", help="Test MongoDB functionality")
    parser.add_argument("--github", action="store_true", help="Test GitHub integration")
    parser.add_argument("--docker", action="store_true", help="Test Docker integration")
    parser.add_argument("--comparison", action="store_true", help="Test comparison with previous report")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--subreddit", type=str, default="artificial", help="Subreddit to use for testing")
    
    args = parser.parse_args()
    
    try:
        # Run all tests if --all is specified or no specific test is specified
        run_all = args.all or not any([
            args.reddit, args.weekly_monthly, args.llm, args.tables, args.mongodb, 
            args.github, args.docker, args.comparison
        ])
        
        posts = []
        weekly_posts = []
        monthly_posts = []
        report = {}
        
        # Test Reddit data collection
        if run_all or args.reddit:
            posts = test_reddit_collection(args.subreddit)
        
        # Test weekly and monthly post collection
        if run_all or args.weekly_monthly:
            wm_posts = test_weekly_monthly_collection(args.subreddit)
            weekly_posts = wm_posts.get('weekly', [])
            monthly_posts = wm_posts.get('monthly', [])
        
        # Test LLM processing
        if (run_all or args.llm) and posts:
            report = test_llm_processing(posts, weekly_posts, monthly_posts)
        
        # Test table generation
        if (run_all or args.tables) and posts:
            test_table_generation(posts, weekly_posts, monthly_posts)
        
        # Test MongoDB functionality
        if (run_all or args.mongodb) and posts and report:
            test_mongodb(posts, report)
        
        # Test GitHub integration
        if run_all or args.github:
            test_github_integration()
        
        # Test Docker integration
        if run_all or args.docker:
            test_docker_integration()
        
        # Test comparison with previous report
        if run_all or args.comparison:
            test_comparison_with_previous_report()
        
        logger.info("All specified tests completed")
    
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 