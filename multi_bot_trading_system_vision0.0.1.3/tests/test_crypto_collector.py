from backend.News_card import news
from backend.News_card.news import collect_all, collect_rss_source, deduplicate


def test_api_only_news_route_returns_news_items(monkeypatch):
    from unittest.mock import patch

    with patch("backend.services.price_service.PriceService.start"):
        from backend import api_only

    items = [{"id": "test-news", "title": "Test news"}]
    monkeypatch.setattr(api_only, "collect_news", lambda: {"total_new": 1})
    monkeypatch.setattr(api_only, "get_news_items", lambda: items)

    response = api_only.app.test_client().get("/api/news")

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True,
        "total_new": 1,
        "total_items": 1,
        "items": items,
    }


def test_collect_rss_source_extracts_item_fields(monkeypatch):
    feed = b"""<?xml version="1.0"?>
    <rss><channel><item>
      <title>Bitcoin update</title>
      <link>https://example.com/bitcoin</link>
      <description>Market summary</description>
      <guid>bitcoin-update</guid>
      <pubDate>Fri, 06 Nov 2026 10:00:00 GMT</pubDate>
    </item></channel></rss>"""
    monkeypatch.setattr(news, "fetch_url", lambda _: feed)

    items, error = collect_rss_source(
        {"name": "Example RSS", "url": "https://example.com/feed.xml"}
    )

    assert error is None
    assert items == [
        {
            "date": "2026-11-06T10:00:00Z",
            "title": "Bitcoin update",
            "source": "Example RSS",
            "url": "https://example.com/bitcoin",
            "summary": "Market summary",
            "id": "bitcoin-update",
            "kind": "rss",
        }
    ]


def test_deduplicate_keeps_newest_unique_items():
    items = [
        {"id": "old", "date": "2026-11-01T10:00:00Z", "title": "Old article"},
        {"id": "new", "date": "2026-11-05T10:00:00Z", "title": "New article"},
        {"id": "old", "date": "2026-11-01T10:00:00Z", "title": "Old article duplicate"},
    ]

    result = deduplicate(items)

    assert [item["id"] for item in result] == ["new", "old"]


def test_deduplicate_uses_url_when_id_missing():
    items = [
        {"url": "https://example.com/a", "date": "2026-11-01T10:00:00Z", "title": "A"},
        {"url": "https://example.com/a", "date": "2026-11-02T10:00:00Z", "title": "A duplicate"},
        {"url": "https://example.com/b", "date": "2026-11-03T10:00:00Z", "title": "B"},
    ]

    result = deduplicate(items)

    assert [item["url"] for item in result] == [
        "https://example.com/b",
        "https://example.com/a",
    ]


def test_collect_all_counts_new_items_before_persisting_them(monkeypatch):
    general_item = {"id": "general-1", "title": "General news"}
    person_post = {"id": "post-1", "title": "New post"}
    coin_item = {"id": "coin-1", "title": "Coin news"}
    items_by_source = {
        "General": [general_item],
        "Coin": [coin_item],
    }

    monkeypatch.setattr(
        news,
        "dispatch_source",
        lambda source: (items_by_source[source["name"]], None),
    )
    monkeypatch.setattr(news, "collect_x_person", lambda _: ([person_post], None))

    config = {
        "general": {
            "sources": [{"name": "General", "enabled": True, "items": []}],
        },
        "people_monitoring": [
            {"name": "Person", "enabled": True, "posts": []},
        ],
        "coins": [
            {
                "name": "Coin",
                "news": [],
                "sources": [{"name": "Coin", "enabled": True}],
            },
        ],
    }

    first_result = collect_all(config)
    second_result = collect_all(config)

    assert first_result["summary"] == [
        ("General", 1, "source"),
        ("Person", 1, "post"),
        ("Coin", 1, "article"),
    ]
    assert second_result["summary"] == [
        ("General", 0, "source"),
        ("Person", 0, "post"),
        ("Coin", 0, "article"),
    ]
    assert config["general"]["sources"][0]["items"] == [general_item]
    assert config["people_monitoring"][0]["posts"] == [person_post]
    assert config["coins"][0]["news"] == [coin_item]
