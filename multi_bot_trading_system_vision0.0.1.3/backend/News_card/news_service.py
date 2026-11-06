#!/usr/bin/env python3
"""News Service for the Multi-Bot Trading System.

Wraps the News Card crypto information collector to provide news data
via API endpoints for the Angular frontend.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def news_config_path() -> Path:
    """Get the configuration file next to this service."""
    return Path(__file__).resolve().parent / "config.json"


def load_news_config() -> Dict[str, Any]:
    """Load the news configuration from config.json."""
    try:
        with news_config_path().open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load news config: {e}")
        return {}


def save_news_config(config: Dict[str, Any]) -> None:
    """Save the news configuration to config.json."""
    try:
        with news_config_path().open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved news config to {news_config_path()}")
    except Exception as e:
        logger.error(f"Could not save news config: {e}")


def collect_news() -> Dict[str, Any]:
    """Collect news from all enabled sources.

    Returns a summary of newly collected items.
    """
    config = load_news_config()
    if not config:
        return {"summary": [], "total_new": 0}

    # Run the collector
    from backend.News_card.news import ensure_config, collect_all

    # Make sure config is properly ensured
    config = ensure_config(config)
    result = collect_all(config)
    save_news_config(config)

    summary = result.get("summary", [])
    total_new = sum(count for _, count, _ in summary)

    logger.info(f"Collected {total_new} new news items")
    return {"summary": summary, "total_new": total_new}


def get_news_items() -> List[Dict[str, Any]]:
    """Get all news items from configured sources.

    Returns a list of news items ready for display in the Angular frontend.
    """
    config = load_news_config()
    if not config:
        return []

    from backend.News_card.news import ensure_config, deduplicate

    config = ensure_config(config)

    all_items: List[Dict[str, Any]] = []

    # Newly collected items are already saved in these configuration lists.
    for source in config.get("general", {}).get("sources", []):
        items = source.get("items", [])
        if isinstance(items, list):
            all_items.extend(item for item in items if isinstance(item, dict))

    # Include persisted posts from monitored accounts.
    for person in config.get("people_monitoring", []):
        items = person.get("posts", [])
        if isinstance(items, list):
            all_items.extend(item for item in items if isinstance(item, dict))

    # Include persisted coin-specific news.
    for coin in config.get("coins", []):
        items = coin.get("news", [])
        if isinstance(items, list):
            all_items.extend(item for item in items if isinstance(item, dict))

    return deduplicate(all_items)


def _dispatch_source(source: Dict[str, Any]) -> tuple:
    """Dispatch a source to the appropriate collector."""
    source_type = (source.get("type") or "api").lower()
    name = source.get("name", "SOURCE")

    if source_type == "rss":
        from backend.News_card.news import collect_rss_source
        return collect_rss_source(source)
    elif source_type == "website":
        from backend.News_card.news import collect_website_source
        return collect_website_source(source)
    elif source_type == "x":
        from backend.News_card.news import collect_x_person
        return collect_x_person(source)
    elif source_type == "api":
        from backend.News_card.news import collect_api_source
        return collect_api_source(source)
    else:
        return [], f"Unknown source type: {source_type}"


def _collect_x_person(person: Dict[str, Any]) -> tuple:
    """Collect posts from an X (Twitter) person."""
    from backend.News_card.news import x_bearer_token

    token = x_bearer_token()
    if not token:
        return [], "X API not available. Add X_BEARER_TOKEN in .env file."

    username = (person.get("username") or "").strip()
    if not username:
        return [], "X profile missing username"

    try:
        import urllib.parse
        import urllib.request

        user_url = f"https://api.x.com/2/users/by/username/{urllib.parse.quote(username)}"
        user_req = urllib.request.Request(
            user_url,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(user_req, timeout=20) as response:
            user_payload = json.loads(response.read().decode("utf-8"))
        user_id = (user_payload.get("data") or {}).get("id")
        if not user_id:
            return [], f"X username '{username}' could not be resolved"

        tweets_url = (
            f"https://api.x.com/2/users/{user_id}/tweets"
            "?max_results=10&tweet.fields=created_at,text,public_metrics"
        )
        tweets_req = urllib.request.Request(
            tweets_url,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(tweets_req, timeout=20) as response:
            tweets_payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return [], f"X API request failed: {exc}"

    posts = tweets_payload.get("data") or []
    if not posts:
        return [], "No public X posts found for this account"

    person_topics = [str(topic).lower() for topic in person.get("topics", [])]
    items: List[Dict[str, Any]] = []
    for tweet in posts:
        text = (tweet.get("text") or "").strip()
        if not text:
            continue
        detected = (
            [topic for topic in person.get("topics", []) if str(topic).lower() in text.lower()]
            if isinstance(person.get("topics"), list)
            else []
        )
        item = {
            "title": text[:90] or f"X post by {person.get('name', username)}",
            "date": tweet.get("created_at"),
            "source": person.get("platform", "X"),
            "url": f"https://x.com/{username}/status/{tweet.get('id')}",
            "summary": text,
            "id": f"x:{tweet.get('id')}",
            "kind": "x",
            "post_id": tweet.get("id"),
            "topics": detected,
        }
        item["person"] = person.get("name", username)
        item["topics"] = detected
        items.append(item)
    return items, None


def _canonical_key(item: Dict[str, Any]) -> Optional[str]:
    """Create a canonical key for deduplication."""
    item_id = (item.get("id") or item.get("post_id") or item.get("source_id") or "").strip()
    if item_id:
        return f"id:{item_id}"
    url = (item.get("url") or item.get("link") or "").strip()
    if url:
        return f"url:{url}"
    title = str(item.get("title") or "").strip()
    date = str(item.get("date") or item.get("published_at") or "").strip()
    if title and date:
        title_key = re.sub(r"\W+", " ", title.lower()).strip()
        return f"title-date:{title_key}|{date}"
    return None