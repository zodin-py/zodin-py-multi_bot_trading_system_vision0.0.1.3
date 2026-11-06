---
name: trader-news
description: >-
  Collect and review crypto information from the sources configured in
  backend/News_card/config.json: general API/RSS/website sources, monitored
  public X accounts, and coin-specific sources. Use when asked for crypto news,
  coin updates, monitored-person posts, or to run the News_card collector.
---

# Crypto Information Collector

This skill uses the existing collector in this folder. It only gathers and
organizes source information; it does not perform AI analysis, sentiment
analysis, market forecasts, trading signals, or trades.

## Files and configuration

- Collector: [news.py](./news.py)
- Main configuration and collected items: [config.json](./config.json)
- X credential template: [.env.example](./.env.example)
- Local X credentials, if used: `.env` in this same folder. Never put secrets
  in `config.json` or report them in chat.

Edit `config.json` to add or remove:

- `general.sources`: sources independent of a coin.
- `people_monitoring`: public X accounts, topics, and stored posts.
- `coins`: coin metadata and that coin's own sources.

Every source needs a `name`, `type`, `url`, and `enabled` value. Supported types
are `api`, `rss`, and `website`. Person entries use `name`, `platform`,
`username`, `topics`, and `enabled`. New collection results are stored in the
corresponding `items`, `posts`, or `news` list in this same JSON file.

Only enable a source if its URL returns information the collector can parse.
An API endpoint is not necessarily a news feed: for example,
Binance's `/api/v3/ticker/24hr` endpoint returns market statistics, not
articles. The website collector captures a page title and URL; it does not
extract full articles.

## Run the collector

From the project directory in PowerShell:

```powershell
.\venv\Scripts\python.exe backend\News_card\news.py
```

Or, from this folder:

```powershell
python news.py
```

The script has no command-line options for tickers, time windows, dry runs, or
JSON output. It reads all enabled entries from `config.json`, attempts each
source, prints source errors and a total count, then atomically saves the
updated configuration. A failed source should not stop the remaining sources.

Before reporting which entries are new, compare the configured `items`,
`posts`, and `news` lists before and after the run. The terminal's total is the
collector's count; it does not print the individual collected entries.

## X API

X monitoring uses the official X API. Set `X_BEARER_TOKEN` in
`backend/News_card/.env` (see [.env.example](./.env.example)) and enable the
person in `config.json`. Without a supported token, the collector reports that
X is unavailable. Do not scrape X or use unofficial endpoints.

Posts are stored with their date, account, original text, X URL, post ID, and
topics found by case-insensitive substring matching. Topics label posts; they
do not filter them out or represent sentiment/AI analysis.

## Reporting collected information

1. Run the collector using the command above when the user asks for an update.
2. Read the resulting entries in `config.json`. Use the source's original URL
   and text/summary; do not invent missing fields or treat a market-data
   response as a news article.
3. Give a concise summary organized by source, person, or coin. Include dates
   and links when present, and say when a source failed or returned no usable
   entries.
4. Report facts as published. Do not predict prices or recommend buying,
   selling, or trading.
