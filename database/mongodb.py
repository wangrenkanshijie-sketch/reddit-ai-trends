"""
MongoDB Client Module

This module provides functionality to interact with MongoDB for storing and retrieving Reddit data.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from config import REPORT_CONFIG

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MongoDBClient:
    """Client for interacting with MongoDB."""
    
    def __init__(self):
        """Initialize the MongoDB client using credentials from environment variables."""
        self.connection_string = os.getenv('MONGODB_CONNECTION_STRING')
        if not self.connection_string:
            raise ValueError("MongoDB connection string not found in environment variables")
        
        self.client = MongoClient(self.connection_string)
        self.db = self.client[REPORT_CONFIG['database_name']]
        self.posts_collection = self.db[REPORT_CONFIG['collections']['posts']]
        self.reports_collection = self.db[REPORT_CONFIG['collections']['reports']]
        
        # Create indexes for better performance
        self._create_indexes()
        
        logger.info(f"Connected to MongoDB database: {REPORT_CONFIG['database_name']}")
    
    def _create_indexes(self):
        """Create indexes for better query performance."""
        # Create index on post_id for faster lookups
        self.posts_collection.create_index("post_id", unique=True)
        
        # Create index on subreddit for faster filtering
        self.posts_collection.create_index("subreddit")
        
        # Create index on created_utc for faster time-based queries
        self.posts_collection.create_index("created_utc")
        
        # Create index on report_id for faster lookups
        self.reports_collection.create_index("report_id", unique=True)
        
        # Create index on timestamp for faster time-based queries
        self.reports_collection.create_index("timestamp")
    
    def insert_or_update_posts(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Insert or update multiple posts in the database.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary with counts of inserted and updated posts
        """
        if not posts:
            return {"inserted": 0, "updated": 0}
        
        # Prepare bulk operations
        operations = []
        for post in posts:
            # Use post_id as the unique identifier
            filter_query = {"post_id": post["post_id"]}
            
            # Add last_updated timestamp
            post["last_updated"] = datetime.utcnow()
            
            # Store previous metrics for comparison if the post already exists
            existing_post = self.posts_collection.find_one(filter_query)
            if existing_post:
                # Store historical metrics
                if "historical_metrics" not in post:
                    post["historical_metrics"] = []
                
                # Add current metrics to historical data
                if "historical_metrics" in existing_post:
                    post["historical_metrics"] = existing_post["historical_metrics"]
                
                # Add new historical entry
                historical_entry = {
                    "timestamp": datetime.utcnow(),
                    "score": existing_post.get("score", 0),
                    "num_comments": existing_post.get("num_comments", 0)
                }
                post["historical_metrics"].append(historical_entry)
                
                # Limit historical entries to last 10
                if len(post["historical_metrics"]) > 10:
                    post["historical_metrics"] = post["historical_metrics"][-10:]
            
            # Create update operation
            operation = UpdateOne(
                filter_query,
                {"$set": post},
                upsert=True
            )
            operations.append(operation)
        
        try:
            # Execute bulk operations
            result = self.posts_collection.bulk_write(operations)
            
            # Return counts
            return {
                "inserted": result.upserted_count,
                "updated": result.modified_count
            }
        except PyMongoError as e:
            logger.error(f"Error inserting or updating posts: {e}")
            raise
    
    def get_posts_by_subreddit(self, subreddit: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get posts from a specific subreddit.
        
        Args:
            subreddit: Name of the subreddit
            limit: Maximum number of posts to return
            
        Returns:
            List of post dictionaries
        """
        try:
            cursor = self.posts_collection.find(
                {"subreddit": subreddit}
            ).sort("created_utc", -1).limit(limit)
            
            return list(cursor)
        except PyMongoError as e:
            logger.error(f"Error getting posts from subreddit {subreddit}: {e}")
            raise
    
    def get_posts_by_time_range(self, 
                               start_time: datetime, 
                               end_time: datetime, 
                               subreddit: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get posts within a specific time range.
        
        Args:
            start_time: Start time
            end_time: End time
            subreddit: Optional subreddit filter
            
        Returns:
            List of post dictionaries
        """
        query = {
            "created_utc": {
                "$gte": start_time,
                "$lte": end_time
            }
        }
        
        if subreddit:
            query["subreddit"] = subreddit
        
        try:
            cursor = self.posts_collection.find(query).sort("created_utc", -1)
            return list(cursor)
        except PyMongoError as e:
            logger.error(f"Error getting posts by time range: {e}")
            raise
    
    def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a post by its ID.
        
        Args:
            post_id: Post ID
            
        Returns:
            Post dictionary or None if not found
        """
        try:
            return self.posts_collection.find_one({"post_id": post_id})
        except PyMongoError as e:
            logger.error(f"Error getting post by ID {post_id}: {e}")
            raise
    
    def get_post_metrics_history(self, post_id: str) -> List[Dict[str, Any]]:
        """
        Get the metrics history for a specific post.
        
        Args:
            post_id: Post ID
            
        Returns:
            List of historical metrics or empty list if not found
        """
        try:
            post = self.posts_collection.find_one(
                {"post_id": post_id},
                {"historical_metrics": 1}
            )
            
            if post and "historical_metrics" in post:
                return post["historical_metrics"]
            
            return []
        except PyMongoError as e:
            logger.error(f"Error getting metrics history for post {post_id}: {e}")
            return []
    
    def insert_report(self, report: Dict[str, Any]) -> str:
        """
        Insert a new report.
        
        Args:
            report: Report dictionary
            
        Returns:
            ID of the inserted report
        """
        try:
            # Add timestamp if not present
            if "timestamp" not in report:
                report["timestamp"] = datetime.utcnow()
            
            # Insert report
            result = self.reports_collection.insert_one(report)
            
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error inserting report: {e}")
            raise
    
    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest report.
        
        Returns:
            Latest report dictionary or None if no reports exist
        """
        try:
            return self.reports_collection.find_one(
                sort=[("timestamp", -1)]
            )
        except PyMongoError as e:
            logger.error(f"Error getting latest report: {e}")
            raise
    
    def get_reports_by_time_range(self, 
                                 start_time: datetime, 
                                 end_time: datetime) -> List[Dict[str, Any]]:
        """
        Get reports within a specific time range.
        
        Args:
            start_time: Start time
            end_time: End time
            
        Returns:
            List of report dictionaries
        """
        try:
            cursor = self.reports_collection.find({
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            }).sort("timestamp", -1)
            
            return list(cursor)
        except PyMongoError as e:
            logger.error(f"Error getting reports by time range: {e}")
            raise
    
    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def get_posts_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取指定日期范围内的帖子。
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回的最大帖子数量
            
        Returns:
            帖子列表
        """
        try:
            # 将日期转换为Unix时间戳
            start_timestamp = start_date.timestamp()
            end_timestamp = end_date.timestamp()
            
            # 查询指定日期范围内的帖子
            query = {
                "created_utc": {
                    "$gte": start_timestamp,
                    "$lte": end_timestamp
                }
            }
            
            # 执行查询
            posts = list(self.posts_collection.find(query).limit(limit))
            
            logger.info(f"从MongoDB获取了 {len(posts)} 个日期范围内的帖子")
            return posts
        
        except PyMongoError as e:
            logger.error(f"获取日期范围内的帖子时出错: {e}")
            return []
    
    def get_latest_posts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取最新的帖子。
        
        Args:
            limit: 返回的最大帖子数量
            
        Returns:
            帖子列表
        """
        try:
            # 按创建时间降序排序，获取最新的帖子
            posts = list(self.posts_collection.find().sort("created_utc", -1).limit(limit))
            
            logger.info(f"从MongoDB获取了 {len(posts)} 个最新帖子")
            return posts
        
        except PyMongoError as e:
            logger.error(f"获取最新帖子时出错: {e}")
            return []
    
    def get_latest_report_before_date(self, date: datetime) -> Optional[Dict[str, Any]]:
        """
        获取指定日期之前的最新报告。
        
        Args:
            date: 日期
            
        Returns:
            报告字典，如果没有找到则返回None
        """
        try:
            # 查询指定日期之前的最新报告
            query = {
                "created_at": {
                    "$lt": date.isoformat()
                }
            }
            
            # 按创建时间降序排序，获取最新的报告
            report = self.reports_collection.find_one(query, sort=[("created_at", -1)])
            
            if report:
                logger.info(f"找到了日期 {date.isoformat()} 之前的最新报告，ID: {report.get('report_id')}")
            else:
                logger.info(f"没有找到日期 {date.isoformat()} 之前的报告")
            
            return report
        
        except PyMongoError as e:
            logger.error(f"获取日期之前的最新报告时出错: {e}")
            return None 