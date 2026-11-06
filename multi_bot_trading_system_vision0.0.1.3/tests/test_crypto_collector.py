from backend.News_card.news import deduplicate


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
