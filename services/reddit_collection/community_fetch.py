"""
Reddit Community Fetch Service

This module provides functionality to fetch trending posts from Reddit communities
for different time periods (day, week, month).
"""

import os
import praw
import logging
from datetime import datetime
from typing import List, Dict, Any, Literal, Optional
from dotenv import load_dotenv
from config import REDDIT_COMMUNITIES

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RedditCommunityFetcher:
    """Service for fetching trending posts from Reddit communities."""
    
    def __init__(self):
        """Initialize the Reddit community fetcher using credentials from environment variables."""
        # Get Reddit API credentials from environment variables
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT')
        
        if not all([client_id, client_secret, user_agent]):
            raise ValueError("Reddit API credentials not found in environment variables")
        
        # Initialize PRAW Reddit instance
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        logger.info("Reddit community fetcher initialized")
    
    def get_community_summary(self, subreddit_name: str) -> Dict[str, Any]:
        """
        Get summary information about a subreddit.
        
        Args:
            subreddit_name: Name of the subreddit
            
        Returns:
            Dictionary containing subreddit information
        """
        logger.info(f"Fetching summary for r/{subreddit_name}")
        
        try:
            # Get subreddit instance
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Extract subreddit data
            subreddit_data = {
                "display_name": subreddit.display_name,
                "title": subreddit.title,
                "description": subreddit.public_description,
                "subscribers": subreddit.subscribers,
                "created_utc": datetime.fromtimestamp(subreddit.created_utc),
                "url": f"https://www.reddit.com/r/{subreddit_name}/",
                "over18": subreddit.over18
            }
            
            logger.info(f"Successfully fetched summary for r/{subreddit_name}")
            return subreddit_data
        
        except Exception as e:
            logger.error(f"Error fetching summary for r/{subreddit_name}: {e}")
            return {
                "display_name": subreddit_name,
                "title": "Unknown",
                "description": "Could not fetch subreddit information",
                "subscribers": 0,
                "created_utc": datetime.now(),
                "url": f"https://www.reddit.com/r/{subreddit_name}/",
                "over18": False
            }
    
    def get_trending_posts(self, subreddit_name: str, time_filter: str = "day", limit: int = 25) -> List[Dict[str, Any]]:
        """
        Get trending posts from a subreddit for a specific time period.
        
        Args:
            subreddit_name: Name of the subreddit
            time_filter: Time filter for posts (hour, day, week, month, year, all)
            limit: Maximum number of posts to return
            
        Returns:
            List of post dictionaries
        """
        logger.info(f"Fetching trending posts from r/{subreddit_name} for time filter: {time_filter}")
        
        try:
            # Get subreddit instance
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get top posts
            posts = []
            for post in subreddit.top(time_filter=time_filter, limit=limit):
                post_data = self._convert_post_to_dict(post)
                posts.append(post_data)
            
            logger.info(f"Successfully fetched {len(posts)} trending posts from r/{subreddit_name}")
            return posts
        
        except Exception as e:
            logger.error(f"Error fetching trending posts from r/{subreddit_name}: {e}")
            return []
    
    def _convert_post_to_dict(self, post) -> Dict[str, Any]:
        """
        Convert a PRAW post object to a dictionary.
        
        Args:
            post: PRAW post object
            
        Returns:
            Post dictionary
        """
        # Convert created timestamp to datetime
        created_utc = datetime.fromtimestamp(post.created_utc)
        
        # Extract post data
        post_data = {
            "post_id": post.id,
            "title": post.title,
            "author": str(post.author) if post.author else "[deleted]",
            "created_utc": created_utc,
            "score": post.score,
            "upvote_ratio": post.upvote_ratio,
            "num_comments": post.num_comments,
            "permalink": f"https://www.reddit.com{post.permalink}",
            "url": post.url,
            "is_self": post.is_self,
            "selftext": post.selftext if post.is_self else "",
            "subreddit": post.subreddit.display_name,
            "link_flair_text": post.link_flair_text
        }
        
        return post_data
    
    def fetch_all_timeframes(self, subreddit_name: str, limit: int = 25) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch trending posts for all time periods (day, week, month).
        
        Args:
            subreddit_name: Name of the subreddit
            limit: Maximum number of posts to return per time period
            
        Returns:
            Dictionary containing lists of posts for each time period
        """
        logger.info(f"Fetching posts for all timeframes from r/{subreddit_name}")
        
        # Fetch posts for each time period
        day_posts = self.get_trending_posts(subreddit_name, time_filter="day", limit=limit)
        week_posts = self.get_trending_posts(subreddit_name, time_filter="week", limit=limit)
        month_posts = self.get_trending_posts(subreddit_name, time_filter="month", limit=limit)
        
        # Combine results
        all_data = {
            "day": day_posts,
            "week": week_posts,
            "month": month_posts
        }
        
        logger.info(f"Successfully fetched posts for all timeframes from r/{subreddit_name}")
        return all_data 