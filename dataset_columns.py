"""Central place for configuring CSV column names used across the app."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetColumns:
    # Common columns
    time: str = "Date"
    tweet_id: str = "Post id"
    tweet_text: str = "Post text"
    tweet_permalink: str = "Post Link"

    # Post-level columns
    post_text: str = "Post text"
    post_link: str = "Post Link"
    post_impressions: str = "Impressions"
    post_replies: str = "Replies"
    post_profile_visits: str = "Profile visits"
    post_likes: str = "Likes"
    post_reposts: str = "Reposts"

    # Metric columns used across analytics
    impressions: str = "Impressions"
    engagements: str = "Engagements"
    likes: str = "Likes"
    replies: str = "Replies"
    retweets: str = "Reposts"
    user_profile_clicks: str = "Profile visits"
    media_views: str = "Detail Expands"
    bookmarks: str = "Bookmarks"
    shares: str = "Shares"
    new_follows: str = "New follows"
    url_clicks: str = "URL Clicks"
    hashtag_clicks: str = "Hashtag Clicks"
    permalink_clicks: str = "Permalink Clicks"


COLUMNS = DatasetColumns()
