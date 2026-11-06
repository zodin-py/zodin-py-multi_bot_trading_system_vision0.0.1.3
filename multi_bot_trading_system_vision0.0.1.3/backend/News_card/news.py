#!/usr/bin/env python3
"""Crypto Information Collector.

Adaptation of the existing news monitor to collect crypto information from
configured general sources, monitored people and individual coin sources.

This script intentionally does not implement trading signals, sentiment analysis
or automatic trading.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from dotenv import load_dotenv


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value).strip()
        if not raw:
            return None
        try:
            import email.utils

            dt = email.utils.parsedate_to_datetime(raw)
        except (TypeError, ValueError, IndexError):
            dt = None
        if dt is None:
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso_utc(value: Any) -> str | None:
    dt = parse_datetime(value)
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def default_config() -> Dict[str, Any]:
    return {
        "general": {
            "sources": [
                {
                    "name": "Binance",
                    "type": "api",
                    "url": "https://api.binance.com/api/v3/ticker/24hr",
                    "enabled": False,
                    "items": [],
                },
                {
                    "name": "Google News",
                    "type": "rss",
                    "url": "https://news.google.com/rss/search?q=crypto&hl=en-US&gl=US&ceid=US:en",
                    "enabled": False,
                    "items": [],
                },
                {
                    "name": "Bitcoin News",
                    "type": "rss",
                    "url": "https://www.bitcoinnews.com/feed/",
                    "enabled": False,
                    "items": [],
                },
            ]
        },
        "people_monitoring": [
            {
                "name": "Donald Trump",
                "platform": "X",
                "username": "realDonaldTrump",
                "topics": ["Bitcoin", "Crypto", "Regulation"],
                "enabled": False,
                "posts": [],
            },
            {
                "name": "Elon Musk",
                "platform": "X",
                "username": "elonmusk",
                "topics": ["Bitcoin", "Crypto", "Technology"],
                "enabled": False,
                "posts": [],
            },
        ],
        "coins": [
            {
                "name": "KITE",
                "symbol": "KITE",
                "sources": [
                    {
                        "name": "KITE Official Website",
                        "type": "website",
                        "url": "https://kite.com/",
                        "enabled": False,
                        "items": [],
                    },
                    {
                        "name": "KITE News RSS",
                        "type": "rss",
                        "url": "https://kite.com/news/rss/",
                        "enabled": False,
                        "items": [],
                    },
                ],
                "news": [],
            }
        ],
        "seen_items": [],
    }


def load_json(path: str | Path) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_json_atomic(path: str | Path, payload: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(tmp_path, file_path)


def ensure_config(config: Dict[str, Any]) -> Dict[str, Any]:
    config.setdefault("general", {"sources": []})
    config.setdefault("people_monitoring", [])
    config.setdefault("coins", [])
    config.setdefault("seen_items", [])
    if not isinstance(config["general"], dict):
        config["general"] = {"sources": []}
    config["general"].setdefault("sources", [])
    return config


def config_path() -> Path:
    project_root = repo_root()
    return project_root / "config.json"


def load_config() -> Dict[str, Any]:
    path = config_path()
    config = load_json(path)
    if not config:
        # config = default_config()
        save_json_atomic(path, config)
    return ensure_config(config)


def load_environment() -> None:
    project_root = repo_root()
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)
    else:
        load_dotenv(override=False)


def canonical_key(item: Dict[str, Any]) -> str | None:
    if not isinstance(item, dict):
        return None
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


def stable_hash(value: Any) -> str:
    return hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:16]


def deduplicate(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    result: List[Dict[str, Any]] = []
    for item in items:
        key = canonical_key(item) or stable_hash(item.get("id") or item.get("url") or item.get("title") or json.dumps(item, sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    result.sort(key=lambda entry: parse_datetime(entry.get("date")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return result


def gather_seen_keys(config: Dict[str, Any]) -> set[str]:
    seen: set[str] = set(config.get("seen_items", []))
    for source in config.get("general", {}).get("sources", []):
        for item in source.get("items", []):
            key = canonical_key(item) or stable_hash(item.get("id") or item.get("url") or item.get("title") or json.dumps(item, sort_keys=True))
            seen.add(key)
    for person in config.get("people_monitoring", []):
        for post in person.get("posts", []):
            key = canonical_key(post) or stable_hash(post.get("id") or post.get("url") or post.get("title") or json.dumps(post, sort_keys=True))
            seen.add(key)
    for coin in config.get("coins", []):
        for item in coin.get("news", []):
            key = canonical_key(item) or stable_hash(item.get("id") or item.get("url") or item.get("title") or json.dumps(item, sort_keys=True))
            seen.add(key)
    return seen


def remember_items(config: Dict[str, Any], items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = gather_seen_keys(config)
    new_items: List[Dict[str, Any]] = []
    for item in items:
        key = canonical_key(item) or stable_hash(item.get("id") or item.get("url") or item.get("title") or json.dumps(item, sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        new_items.append(item)
    config["seen_items"] = sorted(seen)
    return new_items


def fetch_url(url: str, timeout: int = 20) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def normalize_item(source_name: str, payload: Dict[str, Any], default_kind: str = "item") -> Dict[str, Any]:
    item = {
        "date": payload.get("date") or payload.get("published_at") or payload.get("updated_at") or "",
        "title": str(payload.get("title") or payload.get("headline") or payload.get("name") or "Untitled").strip(),
        "source": payload.get("source") or source_name,
        "url": payload.get("url") or payload.get("link") or payload.get("website") or "",
        "summary": payload.get("summary") or payload.get("description") or "",
        "id": str(payload.get("id") or payload.get("post_id") or payload.get("source_id") or payload.get("url") or payload.get("link") or payload.get("title") or "").strip(),
        "kind": payload.get("kind") or default_kind,
    }
    item["date"] = iso_utc(item["date"]) or None
    if not item["id"]:
        item["id"] = f"{default_kind}:{hashlib.sha1((item.get('title','') + '|' + str(item.get('date') or '')).encode('utf-8')).hexdigest()[:16]}"
    return item


# ------------------------------------------------------------------
# General source collectors
# ------------------------------------------------------------------


def collect_api_source(source: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str | None]:
    url = (source.get("url") or "").strip()
    if not url:
        return [], "API source missing URL"
    try:
        data = fetch_url(url)
        payload = json.loads(data.decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as exc:
        return [], f"API source unavailable: {exc}"

    entries: Iterable[Any]
    if isinstance(payload, list):
        entries = payload
    elif isinstance(payload, dict):
        entries = []
        for key in ("items", "data", "results", "articles", "news", "posts"):
            value = payload.get(key)
            if isinstance(value, list):
                entries = value
                break
        else:
            entries = []
    else:
        entries = []

    items: List[Dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        item = normalize_item(source.get("name", "API"), {
            "title": entry.get("title") or entry.get("headline") or entry.get("name") or "API update",
            "date": entry.get("published_at") or entry.get("date") or entry.get("updated_at"),
            "source": source.get("name", "API"),
            "url": entry.get("url") or entry.get("link") or entry.get("website") or "",
            "summary": entry.get("summary") or entry.get("description") or "",
            "id": entry.get("id") or entry.get("slug") or entry.get("link") or entry.get("url") or str(entry.get("title") or "API update"),
            "kind": "api",
        }, default_kind="api")
        items.append(item)
    return items, None


def collect_rss_source(source: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str | None]:
    url = (source.get("url") or "").strip()
    if not url:
        return [], "RSS source missing URL"
    try:
        data = fetch_url(url)
        root = ET.fromstring(data)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, ET.ParseError, TimeoutError) as exc:
        return [], f"RSS feed unavailable: {exc}"

    items: List[Dict[str, Any]] = []
    for node in root.iter("item"):
        title = node.findtext("title", default="")
        link = node.findtext("link", default="")
        summary = node.findtext("description", default="")
        guid = node.findtext("guid", default="")
        pub = node.findtext("pubDate", default="") or node.findtext("published", default="")
        if not title and not link:
            continue
        item = normalize_item(source.get("name", "RSS"), {
            "title": title or "RSS item",
            "date": pub,
            "source": source.get("name", "RSS"),
            "url": link,
            "summary": summary,
            "id": guid or link or title,
            "kind": "rss",
        }, default_kind="rss")
        items.append(item)
    return items, None


def _extract_meta_title(html: str) -> str:
    patterns = [
        r"<meta[^>]+property=[\"']og:title[\"'][^>]+content=[\"']([^\"']+)[\"']",
        r"<meta[^>]+name=[\"']twitter:title[\"'][^>]+content=[\"']([^\"']+)[\"']",
        r"<title>(.*?)</title>",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.I | re.S)
        if match:
            title = re.sub(r"\s+", " ", match.group(1)).strip()
            if title:
                return title
    return "Website update"


def collect_website_source(source: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str | None]:
    url = (source.get("url") or "").strip()
    if not url:
        return [], "Website source missing URL"
    try:
        html = fetch_url(url).decode("utf-8", errors="ignore")
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as exc:
        return [], f"Website unavailable: {exc}"
    title = _extract_meta_title(html)
    item = normalize_item(source.get("name", "Website"), {
        "title": title,
        "date": None,
        "source": source.get("name", "Website"),
        "url": url,
        "summary": "HTML page captured from configured website source",
        "id": f"website:{url}",
        "kind": "website",
    }, default_kind="website")
    return [item], None


# ------------------------------------------------------------------
# X people monitoring
# ------------------------------------------------------------------


def x_bearer_token() -> str:
    return (
        os.getenv("X_BEARER_TOKEN")
        or os.getenv("TWITTER_BEARER_TOKEN")
        or os.getenv("X_API_KEY")
        or ""
    ).strip()


def collect_x_person(person: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str | None]:
    username = (person.get("username") or "").strip()
    if not username:
        return [], "X profile missing username"
    token = x_bearer_token()
    if not token:
        return [], "X API not available. Add X_BEARER_TOKEN or X_API_KEY in your .env file."

    try:
        user_url = f"https://api.x.com/2/users/by/username/{urllib.parse.quote(username)}"
        user_req = urllib.request.Request(user_url, headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(user_req, timeout=20) as response:
            user_payload = json.loads(response.read().decode("utf-8"))
        user_id = (user_payload.get("data") or {}).get("id")
        if not user_id:
            return [], f"X username '{username}' could not be resolved"

        tweets_url = (
            f"https://api.x.com/2/users/{user_id}/tweets?max_results=10"
            "&tweet.fields=created_at,text,public_metrics"
        )
        tweets_req = urllib.request.Request(tweets_url, headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(tweets_req, timeout=20) as response:
            tweets_payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as exc:
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
        detected = [topic for topic in person.get("topics", []) if str(topic).lower() in text.lower()] if isinstance(person.get("topics"), list) else []
        item = normalize_item(person.get("name", username), {
            "title": text[:90] or f"X post by {person.get('name', username)}",
            "date": tweet.get("created_at"),
            "source": person.get("platform", "X"),
            "url": f"https://x.com/{username}/status/{tweet.get('id')}",
            "summary": text,
            "id": f"x:{tweet.get('id')}",
            "kind": "x",
            "post_id": tweet.get("id"),
            "topics": detected,
        }, default_kind="x")
        item["person"] = person.get("name", username)
        item["topics"] = detected
        items.append(item)
    return items, None


def dispatch_source(source: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str | None]:
    source_type = (source.get("type") or "api").lower()
    if source_type == "rss":
        return collect_rss_source(source)
    if source_type == "website":
        return collect_website_source(source)
    if source_type == "x":
        return collect_x_person(source)
    if source_type == "api":
        return collect_api_source(source)
    return collect_api_source(source)


def collect_all(config: Dict[str, Any]) -> Dict[str, Any]:
    summary: List[Tuple[str, int, str]] = []

    for source in config.get("general", {}).get("sources", []):
        if not source.get("enabled"):
            continue
        items, error = dispatch_source(source)
        if error:
            print(f"[{source.get('name', 'SOURCE')}] {error}")
            continue
        if not items:
            continue
        existing_items = list(source.get("items", []))
        merged = deduplicate(existing_items + items)
        source["items"] = merged
        new_items = remember_items(config, items)
        summary.append((source.get("name", "SOURCE"), len(new_items), "source"))

    for person in config.get("people_monitoring", []):
        if not person.get("enabled"):
            continue
        items, error = collect_x_person(person)
        if error:
            print(f"[{person.get('name', 'PERSON')}] {error}")
            continue
        if not items:
            continue
        merged = deduplicate(list(person.get("posts", [])) + items)
        person["posts"] = merged
        new_items = remember_items(config, items)
        summary.append((person.get("name", "PERSON"), len(new_items), "post"))

    for coin in config.get("coins", []):
        coin_items: List[Dict[str, Any]] = []
        for source in coin.get("sources", []):
            if not source.get("enabled"):
                continue
            items, error = dispatch_source(source)
            if error:
                print(f"[{source.get('name', 'COIN')}] {error}")
                continue
            coin_items.extend(items)
        if not coin_items:
            continue
        merged = deduplicate(list(coin.get("news", [])) + coin_items)
        coin["news"] = merged
        new_items = remember_items(config, coin_items)
        summary.append((coin.get("name", "COIN"), len(new_items), "article"))

    total_new = sum(count for _, count, _ in summary)
    print("\nCollection completed.")
    print(f"Total new items: {total_new}")
    return {"summary": summary}


def main() -> int:
    load_environment()
    config = load_config()
    print("Starting Crypto Information Collector...\n")
    collect_all(config)
    save_json_atomic(config_path(), config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
