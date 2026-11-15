---
name: trader-news
description: >-
  Collect and classify cryptocurrency news from configured API, RSS,
  website sources, monitored public X accounts, and coin-specific sources.
  Analyze all open news entries, identify affected cryptocurrencies,
  classify news as positive or negative, and save results in news-results.json.
  Use when asked for crypto news updates, coin news, monitored-person posts,
  or to run the News_card collector and analyzer.
---

# Crypto Information Collector & Analyzer

This skill collects, organizes, and classifies cryptocurrency news.

It consists of two independent processes:

1. **News Collection:** Collect information from configured sources and store it in config.json.
2. **AI News Analysis:** Analyze all news entries with status "offen", classify them, save the results in news-results.json, and update their original status to "erledigt".

The collector and analyzer must remain separate.

The AI must not perform price predictions, generate trading signals, recommend buying or selling, or execute trades.

# 1. Files and configuration

All files are located in:

`backend/News_card/`

Files:

- `news.py`: News collector.
- `config.json`: Main configuration and collected news.
- `news-results.json`: AI analysis results.
- `.env.example`: X API credential template.
- `.env`: Local X API credentials, if used.

Never store secrets in config.json or report them in chat.

## config.json structure

The configuration contains:

- `general.sources`: Sources independent of a specific coin.
- `people_monitoring`: Monitored public X accounts, topics, and stored posts.
- `coins`: Coin metadata and coin-specific sources.

Every source requires:

- `name`
- `type`
- `url`
- `enabled`

Supported source types:

- `api`
- `rss`
- `website`

Person entries use:

- `name`
- `platform`
- `username`
- `topics`
- `enabled`

Collected information is stored in the corresponding `items`, `posts`, or `news` lists.

Only enable sources whose URLs return information that the collector can parse.

An API endpoint is not necessarily a news feed. For example, Binance's `/api/v3/ticker/24hr` endpoint returns market statistics, not articles.

The website collector captures a page title and URL; it does not extract full articles.

# 2. News Collection

When the user requests a news update, execute the existing collector.

From the project directory in PowerShell:

```powershell
.\venv\Scripts\python.exe backend\News_card\news.py
```

Or, from the News_card folder:

```powershell
python news.py
```

The collector:

1. Reads all enabled entries from config.json.
2. Attempts to collect information from every configured source.
3. Prints source errors and the total collection count.
4. Saves updated information atomically to config.json.

A failed source must not stop the remaining sources.

The script has no command-line options for tickers, time windows, dry runs, or JSON output.

Before reporting new entries, compare the collected `items`, `posts`, and `news` lists before and after collection.

The terminal's total is the collector's count. It does not display individual collected entries.

**Important:** Do not modify or replace the original collection functionality.

# 3. AI News Analysis

After collection, perform the AI analysis as a separate process.

Read the collected news from config.json.

The AI must analyze every news item whose status is exactly:

`"offen"`

This applies to all relevant news entries in:

- `items`
- `posts`
- `news`

Do not analyze entries marked `"erledigt"`.

Do not assume that only newly collected entries need analysis. Every existing entry with status `"offen"` must also be considered.

## 3.1 The four analysis criteria

Every analyzed news item must contain exactly four fields:

**1. title**

The original title of the news item.

Preserve the original title. Do not invent or unnecessarily rewrite it.

**2. coin_name**

The name of the cryptocurrency affected by the news.

Examples:

- Bitcoin
- Ethereum
- Solana
- XRP
- Polkadot

For news that concerns the general cryptocurrency market rather than a specific cryptocurrency, use:

`"General Market"`

If multiple identifiable cryptocurrencies are affected, include their names in one string, separated by commas.

Do not invent affected cryptocurrencies.

**3. news_id**

The original news ID from config.json.

Preserve the exact original ID.

Never generate a replacement ID or use a different identifier.

If an entry has no original news ID, do not invent one. Keep that entry open and report the missing ID.

**4. sentiment**

Classify the news into exactly one of these two values:

- `"positive"`
- `"negative"`

### Positive classification

Classify a news item as positive when its actual content indicates potentially positive implications for the affected cryptocurrency or the general crypto market.

Examples:

- Bitcoin ETF approval.
- Positive regulatory developments.
- Major institutional adoption.
- Successful blockchain upgrades.
- Significant ecosystem growth.

### Negative classification

Classify a news item as negative when its actual content indicates potentially negative implications for the affected cryptocurrency or the general crypto market.

Examples:

- Exchange hacks.
- Major security vulnerabilities.
- Negative regulatory decisions.
- Critical blockchain outages.
- Major institutional withdrawals.

### Classification rules

- Evaluate the actual news content, not just the headline.
- Do not classify every announcement as positive.
- Consider the context and potential consequences.
- Do not confuse neutral writing with neutral market implications.
- Do not invent facts or consequences.
- If the available information is insufficient to make a reliable positive or negative classification, leave the item open.

Every successfully analyzed news item must have exactly the four specified fields.

# 4. Output: news-results.json

Save all successfully analyzed news in:

`backend/News_card/news-results.json`

Required JSON structure:

```json
{
  "results": [
    {
      "title": "Bitcoin ETF receives approval",
      "coin_name": "Bitcoin",
      "news_id": "news_001",
      "sentiment": "positive"
    },
    {
      "title": "Ethereum network suffers major outage",
      "coin_name": "Ethereum",
      "news_id": "news_002",
      "sentiment": "negative"
    },
    {
      "title": "Global crypto regulation announced",
      "coin_name": "General Market",
      "news_id": "news_003",
      "sentiment": "negative"
    }
  ]
}
```

These are illustrative examples.

## Output rules

- Each result must contain exactly four fields.
- Do not add timestamps, explanations, confidence scores, impact levels, or additional fields.
- Preserve the original news ID.
- Preserve the original title.
- Store valid JSON using UTF-8 encoding.
- Preserve all existing valid results.
- Never overwrite existing results with an empty list.
- Do not create duplicate results for the same news ID.
- Use atomic file writing to prevent corruption.

# 5. Status Management

The original news entries in config.json have a status field.

The analysis process must use this field to control processing.

Possible statuses:

- `"offen"`: Waiting for AI analysis.
- `"erledigt"`: Successfully analyzed and saved.

## Processing sequence

For every news item with status `"offen"`:

1. Read the complete original news entry.
2. Check that the original news ID exists.
3. Analyze the news.
4. Identify the affected cryptocurrency or cryptocurrencies.
5. Determine whether the sentiment is positive or negative.
6. Create the result containing exactly four fields.
7. Save the result in news-results.json.
8. Verify that the result was successfully saved and can be read.
9. Only then change the original news status in config.json to `"erledigt"`.
10. Preserve every other original field and value.

Never mark a news item as `"erledigt"` before its analysis result has been successfully saved.

If analysis fails, the original status must remain `"offen"`.

If the news ID is missing or the information is insufficient for a reliable classification, keep the status `"offen"`.

## Error handling

If an individual news item fails:

- Do not stop processing the remaining news.
- Keep the failed item open.
- Continue with the next open item.
- Report the failure in the final execution summary.

If a source fails during collection, continue collecting from the remaining sources.

# 6. Completeness and Duplicate Prevention

Completeness is mandatory.

The analyzer must process all eligible open news entries, not just the first few.

Rules:

1. Read all relevant news lists in config.json.
2. Count all entries with status `"offen"`.
3. Process every eligible open entry.
4. Continue until no further processable open entries remain.
5. Do not silently skip entries.
6. Do not stop after an arbitrary number of news items.
7. Do not analyze entries already marked `"erledigt"`.
8. Do not create duplicate results for an existing news ID.
9. If an item is still open but a valid result with the same news ID already exists, verify that result and mark the item as completed without duplicating it.
10. If an existing result is invalid or incomplete, correct it before changing the status.

If the same news ID occurs in multiple source lists, prevent duplicate analysis results and handle the original records consistently.

# 7. X API

X monitoring uses the official X API.

Set `X_BEARER_TOKEN` in:

`backend/News_card/.env`

Use `.env.example` as the template.

Enable the monitored person in config.json.

Without a supported token, the collector reports that X is unavailable.

Do not scrape X or use unofficial endpoints.

Posts are stored with:

- Date
- Account
- Original text
- X URL
- Post ID
- Topics found through case-insensitive substring matching

Topics label posts. They do not filter posts and do not represent sentiment or AI analysis.

All eligible X posts with status `"offen"` must go through the same AI analysis process as other news.

# 8. Reporting and Execution Summary

When the user asks for a news update:

1. Run news.py.
2. Compare the collected data before and after collection.
3. Read all relevant news entries from config.json.
4. Identify every entry with status `"offen"`.
5. Analyze all eligible open entries.
6. Save successful results in news-results.json.
7. Verify the saved results.
8. Update the original statuses in config.json.
9. Verify that every successfully analyzed entry is marked `"erledigt"`.
10. Report the execution results.

The final report must include:

- Total news entries collected.
- Total open news entries found.
- Successfully analyzed entries.
- Positive news count.
- Negative news count.
- Entries that remain open.
- Collection or analysis errors.

When presenting analyzed news, show only these four criteria:

| Title | Coin Name | News ID | Sentiment |
|---|---|---|---|

Do not add additional analysis fields to individual news results.

# 9. Separation of Responsibilities

This separation is mandatory:

- `news.py`: Collects source information and updates config.json.
- AI Analyzer: Processes all open news entries and classifies them.
- `news-results.json`: Stores the four required analysis fields.
- `config.json`: Maintains the original collected information and processing status.

The collector must remain independent of the AI analysis.

The AI analyzer must not modify original news content, source URLs, IDs, or other metadata.

Only the status field may be changed during successful processing.

The original collection functionality must remain unchanged.