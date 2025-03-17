"""
Reddit Post Trend Management

Main script to fetch and analyze trending posts from Reddit communities.
"""

import os
import argparse
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Load services and utilities
from services.reddit_collection.community_fetch import RedditCommunityFetcher
from utils.data_analysis import (
    convert_posts_to_dataframe,
    get_top_posts_by_score,
    get_top_posts_by_comments,
    extract_common_keywords,
    plot_posts_by_day,
    plot_score_distribution,
    get_engagement_metrics
)
from utils.export import (
    export_to_csv,
    export_to_json,
    export_to_excel,
    save_figure
)

# Load environment variables
load_dotenv()

def display_post_summary(df, title):
    """Display a summary of posts."""
    print(f"\n{title}")
    print("=" * len(title))
    
    # Display top 5 posts by score
    top_posts = get_top_posts_by_score(df, 5)
    print("\nTop 5 Posts by Score:")
    for i, (_, post) in enumerate(top_posts.iterrows(), 1):
        print(f"{i}. {post['title']} (Score: {post['score']}, Comments: {post['num_comments']})")
    
    # Display common keywords
    keywords = extract_common_keywords(df, 10)
    print("\nCommon Keywords:")
    print(", ".join([f"{word} ({count})" for word, count in keywords]))
    
    # Display engagement metrics
    metrics = get_engagement_metrics(df)
    print("\nEngagement Metrics:")
    print(f"Total Posts: {metrics['total_posts']}")
    print(f"Total Score: {metrics['total_score']}")
    print(f"Total Comments: {metrics['total_comments']}")
    print(f"Average Score: {metrics['avg_score']:.2f}")
    print(f"Average Comments: {metrics['avg_comments']:.2f}")
    if metrics['avg_upvote_ratio']:
        print(f"Average Upvote Ratio: {metrics['avg_upvote_ratio']:.2f}")

def fetch_and_analyze_community(subreddit_name, export=False):
    """Fetch and analyze posts from a subreddit."""
    fetcher = RedditCommunityFetcher()
    
    print(f"\nFetching data for r/{subreddit_name}...")
    
    # Get community info
    community_info = fetcher.get_community_summary(subreddit_name)
    print(f"\nCommunity: r/{community_info['display_name']} - {community_info['title']}")
    print(f"Subscribers: {community_info['subscribers']:,}")
    print(f"Description: {community_info['description']}")
    
    # Fetch posts for all time periods
    all_data = fetcher.fetch_all_timeframes(subreddit_name)
    
    # Convert to DataFrames
    dfs = {
        'day': convert_posts_to_dataframe(all_data['day']),
        'week': convert_posts_to_dataframe(all_data['week']),
        'month': convert_posts_to_dataframe(all_data['month'])
    }
    
    # Display summaries
    for period, df in dfs.items():
        display_post_summary(df, f"Top Posts from the Past {period.capitalize()}")
    
    # Export data if requested
    if export:
        print("\nExporting data...")
        
        # Export raw data to JSON
        json_path = export_to_json(all_data, f"{subreddit_name}_raw_data")
        print(f"Raw data exported to: {json_path}")
        
        # Export DataFrames to Excel
        excel_path = export_to_excel(dfs, f"{subreddit_name}_posts")
        print(f"Posts exported to Excel: {excel_path}")
        
        # Export visualizations
        for period, df in dfs.items():
            # Score distribution
            fig = plot_score_distribution(df)
            fig_path = save_figure(fig, f"{subreddit_name}_{period}_score_distribution")
            print(f"Score distribution for {period} exported to: {fig_path}")
            
            # Posts by day (only for month)
            if period == 'month':
                fig = plot_posts_by_day(df, 30)
                fig_path = save_figure(fig, f"{subreddit_name}_posts_by_day")
                print(f"Posts by day exported to: {fig_path}")
    
    return all_data, dfs

def main():
    """Main function to run the application."""
    parser = argparse.ArgumentParser(description='Fetch and analyze trending posts from Reddit communities.')
    parser.add_argument('subreddit', help='Subreddit name (without r/)')
    parser.add_argument('--export', action='store_true', help='Export data to files')
    args = parser.parse_args()
    
    try:
        fetch_and_analyze_community(args.subreddit, args.export)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 