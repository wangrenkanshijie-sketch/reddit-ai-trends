"""
Reddit Community Fetch Service

This module provides functionality to fetch trending posts from Reddit communities
for different time periods (day, week, month).
"""

import os
import praw
from datetime import datetime
from typing import List, Dict, Any, Literal

# Time period types
TimePeriod = Literal['day', 'week', 'month']

class RedditCommunityFetcher:
    """Service for fetching trending posts from Reddit communities."""
    
    def __init__(self):
        """Initialize the Reddit API client using credentials from environment variables."""
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
    
    def fetch_trending_posts(self, 
                            subreddit_name: str, 
                            time_period: TimePeriod = 'day', 
                            limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch trending posts from a specified subreddit for a given time period.
        
        Args:
            subreddit_name: Name of the subreddit (without 'r/')
            time_period: Time period to fetch posts for ('day', 'week', or 'month')
            limit: Maximum number of posts to fetch
            
        Returns:
            List of post data dictionaries
        """
        # Convert time_period to Reddit's time filter format
        time_filter = {
            'day': 'day',
            'week': 'week',
            'month': 'month'
        }.get(time_period, 'day')
        
        # Get the subreddit
        subreddit = self.reddit.subreddit(subreddit_name)
        
        # Fetch top posts for the specified time period
        top_posts = subreddit.top(time_filter=time_filter, limit=limit)
        
        # Extract relevant data from each post
        posts_data = []
        for post in top_posts:
            post_data = {
                'id': post.id,
                'title': post.title,
                'author': str(post.author),
                'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                'score': post.score,
                'upvote_ratio': post.upvote_ratio,
                'num_comments': post.num_comments,
                'url': post.url,
                'permalink': f"https://www.reddit.com{post.permalink}",
                'is_self': post.is_self,
                'selftext': post.selftext if post.is_self else "",
                'flair': post.link_flair_text
            }
            posts_data.append(post_data)
        
        return posts_data
    
    def get_community_summary(self, 
                             subreddit_name: str) -> Dict[str, Any]:
        """
        Get summary information about a subreddit community.
        
        Args:
            subreddit_name: Name of the subreddit (without 'r/')
            
        Returns:
            Dictionary with community information
        """
        subreddit = self.reddit.subreddit(subreddit_name)
        
        return {
            'display_name': subreddit.display_name,
            'title': subreddit.title,
            'description': subreddit.public_description,
            'subscribers': subreddit.subscribers,
            'created_utc': datetime.fromtimestamp(subreddit.created_utc).isoformat(),
            'url': f"https://www.reddit.com/r/{subreddit_name}/",
            'over18': subreddit.over18,
            'active_user_count': subreddit.active_user_count if hasattr(subreddit, 'active_user_count') else None
        }
    
    def fetch_all_timeframes(self, 
                            subreddit_name: str, 
                            limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch trending posts for all time periods (day, week, month).
        
        Args:
            subreddit_name: Name of the subreddit (without 'r/')
            limit: Maximum number of posts to fetch per time period
            
        Returns:
            Dictionary with posts organized by time period
        """
        return {
            'day': self.fetch_trending_posts(subreddit_name, 'day', limit),
            'week': self.fetch_trending_posts(subreddit_name, 'week', limit),
            'month': self.fetch_trending_posts(subreddit_name, 'month', limit)
        } 