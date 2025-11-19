"""Central place for configuring CSV column names used across the app."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetColumns:
    # Common columns
    time: str = "time"
    tweet_id: str = "Tweet id"
    tweet_text: str = "Tweet text"
    tweet_permalink: str = "Tweet permalink"

    # Post-level columns (as provided by the CSV export)
    post_text: str = "Post text"
    post_link: str = "Post Link"
    post_impressions: str = "Impressions"
    post_replies: str = "Replies"
    post_profile_visits: str = "Profile visits"
    post_likes: str = "Likes"
    post_reposts: str = "Reposts"

    # Metric columns used across analytics
    impressions: str = "impressions"
    engagements: str = "engagements"
    likes: str = "likes"
    replies: str = "replies"
    retweets: str = "retweets"
    user_profile_clicks: str = "user profile clicks"
    media_views: str = "media views"


COLUMNS = DatasetColumns()
