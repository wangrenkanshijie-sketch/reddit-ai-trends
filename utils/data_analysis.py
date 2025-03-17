"""
Data Analysis Utilities

This module provides functions for analyzing Reddit post data.
"""

import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from collections import Counter

def convert_posts_to_dataframe(posts: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of post dictionaries to a pandas DataFrame.
    
    Args:
        posts: List of post data dictionaries
        
    Returns:
        DataFrame containing post data
    """
    df = pd.DataFrame(posts)
    
    # Convert created_utc to datetime
    if 'created_utc' in df.columns:
        df['created_utc'] = pd.to_datetime(df['created_utc'])
    
    return df

def get_top_posts_by_score(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Get the top N posts by score.
    
    Args:
        df: DataFrame containing post data
        n: Number of top posts to return
        
    Returns:
        DataFrame with top N posts
    """
    return df.sort_values('score', ascending=False).head(n)

def get_top_posts_by_comments(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Get the top N posts by number of comments.
    
    Args:
        df: DataFrame containing post data
        n: Number of top posts to return
        
    Returns:
        DataFrame with top N posts
    """
    return df.sort_values('num_comments', ascending=False).head(n)

def get_posts_by_timeframe(df: pd.DataFrame, days: int) -> pd.DataFrame:
    """
    Filter posts by a specific timeframe.
    
    Args:
        df: DataFrame containing post data
        days: Number of days to look back
        
    Returns:
        DataFrame with posts from the specified timeframe
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    return df[df['created_utc'] >= cutoff_date]

def extract_common_keywords(df: pd.DataFrame, n: int = 10) -> List[Tuple[str, int]]:
    """
    Extract the most common keywords from post titles.
    
    Args:
        df: DataFrame containing post data
        n: Number of top keywords to return
        
    Returns:
        List of (keyword, count) tuples
    """
    # Combine all titles
    all_titles = ' '.join(df['title'].tolist()).lower()
    
    # Split into words and filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
    words = [word for word in all_titles.split() if word not in stop_words and len(word) > 2]
    
    # Count occurrences
    word_counts = Counter(words)
    
    # Return top N keywords
    return word_counts.most_common(n)

def plot_posts_by_day(df: pd.DataFrame, days: int = 30) -> plt.Figure:
    """
    Plot the number of posts by day for a specified period.
    
    Args:
        df: DataFrame containing post data
        days: Number of days to look back
        
    Returns:
        Matplotlib figure
    """
    # Filter posts by timeframe
    recent_df = get_posts_by_timeframe(df, days)
    
    # Group by day and count
    posts_by_day = recent_df.groupby(recent_df['created_utc'].dt.date).size()
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    posts_by_day.plot(kind='bar', ax=ax)
    
    ax.set_title(f'Posts per Day (Last {days} Days)')
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Posts')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_score_distribution(df: pd.DataFrame) -> plt.Figure:
    """
    Plot the distribution of post scores.
    
    Args:
        df: DataFrame containing post data
        
    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    df['score'].hist(bins=20, ax=ax)
    
    ax.set_title('Distribution of Post Scores')
    ax.set_xlabel('Score')
    ax.set_ylabel('Number of Posts')
    plt.tight_layout()
    
    return fig

def get_engagement_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate engagement metrics for posts.
    
    Args:
        df: DataFrame containing post data
        
    Returns:
        Dictionary with engagement metrics
    """
    metrics = {
        'total_posts': len(df),
        'total_score': df['score'].sum(),
        'total_comments': df['num_comments'].sum(),
        'avg_score': df['score'].mean(),
        'avg_comments': df['num_comments'].mean(),
        'avg_upvote_ratio': df['upvote_ratio'].mean() if 'upvote_ratio' in df.columns else None,
        'max_score': df['score'].max(),
        'max_comments': df['num_comments'].max()
    }
    
    return metrics 