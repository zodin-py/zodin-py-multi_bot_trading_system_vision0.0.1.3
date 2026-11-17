---
name: trader-news
description: >-
  Collect and classify cryptocurrency news from configured API, RSS,
  website sources, monitored public X accounts, and coin-specific sources.
  Analyze all open news entries, identify affected cryptocurrencies,
  classify sentiment and importance, and save results in news-results.json.
  Use when asked for crypto news updates, coin news, monitored-person posts,
  or to run the News_card collector and analyzer.
---

# Crypto Information Collector & Analyzer

This skill collects, organizes, and classifies cryptocurrency news.

It consists of two independent processes:

1. **News Collection:** Collect information from configured sources and store it in config.json.
2. **AI News Analysis:** Analyze all news entries with status "offen", classify them, save results in news-results.json, and update their original status to "erledigt".

The collector and analyzer must remain separate.

The AI must not perform price predictions, generate trading signals, recommend buying or selling, or execute trades.

# 1. Files and Configuration

All files are located in:

`backend/News_card/`

Paths in this skill are relative to the application root (the project directory containing `backend/News_card/news.py`), not to this skill's directory or the current working directory. The shared results file is `backend/News_card/news-results.json`.

Files:

- `news.py`: News collector.
- `config.json`: Main configuration and collected news.
- `news-results.json`: AI analysis results.
- `.env.example`: X API credential template.
- `.env`: Local X API credentials, if used.

Never store secrets in config.json or report them in chat.

## 1.1 config.json structure

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

A collected news entry can contain fields such as:

- `date`
- `title`
- `source`
- `url`
- `summary`
- `id`
- `kind`
- `status`

The original `id` in config.json is the source news ID. It must be preserved and used internally for identification, duplicate prevention, and status management.

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

Do not analyze entries marked `"erledigt"` unless they require migration of an existing export result.

Do not assume that only newly collected entries need analysis. Every existing entry with status `"offen"` must be considered.

## 3.1 The Six Analysis and Export Fields

Every successfully analyzed news item must contain exactly six fields in news-results.json:

1. `id`
2. `title`
3. `coin_name`
4. `sentiment`
5. `importance`
6. `url`

No original `news_id` field may appear in the exported result.

### 1. id

The primary ID of the exported result.

Requirements:

- Generate a unique, stable primary ID.
- Use UUID version 5 (UUIDv5).
- Generate it deterministically from the original source news ID.
- Use the standard DNS namespace UUID:

`6ba7b810-9dad-11d1-80b4-00c04fd430c8`

- Use the following UUIDv5 name input:

`trader-news:<original_source_news_id>`

- The resulting UUID is stored in the export field `id`.
- The same original source news ID must always generate the same primary ID.
- Never generate a new primary ID for an already processed news entry.
- Never use random UUID generation for this purpose.

The original source news ID is used internally to generate and verify the primary ID. It must not be exported.

### 2. title

The original title of the news item.

Requirements:

- Preserve the original title.
- Do not invent or unnecessarily rewrite it.
- Do not remove relevant information from the title.

### 3. coin_name

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

### 4. sentiment

Classify the news into exactly one of these two values:

- `"positive"`
- `"negative"`

#### Positive classification

Classify a news item as positive when its actual content indicates potentially positive implications for the affected cryptocurrency or the general crypto market.

Examples:

- Bitcoin ETF approval.
- Positive regulatory developments.
- Major institutional adoption.
- Successful blockchain upgrades.
- Significant ecosystem growth.

#### Negative classification

Classify a news item as negative when its actual content indicates potentially negative implications for the affected cryptocurrency or the general crypto market.

Examples:

- Exchange hacks.
- Major security vulnerabilities.
- Negative regulatory decisions.
- Critical blockchain outages.
- Major institutional withdrawals.

#### Classification rules

- Evaluate the actual news content, not just the headline.
- Do not classify every announcement as positive.
- Consider the context and potential consequences.
- Do not confuse neutral writing with neutral market implications.
- Do not invent facts or consequences.
- If the available information is insufficient to make a reliable positive or negative classification, leave the item open.

### 5. importance

Classify the importance of every analyzed news item using exactly one of these five values:

- `"very_low"`
- `"low"`
- `"medium"`
- `"high"`
- `"very_high"`

The importance describes how significant the information is for the affected cryptocurrency or the general cryptocurrency market.

#### Very Low

Use `very_low` for information with almost no meaningful market relevance.

Examples:

- Minor announcements without significant consequences.
- Small updates with no relevant impact.
- Unimportant informational posts.
- Repetitive news without new developments.

#### Low

Use `low` for information with limited relevance.

Examples:

- Smaller partnerships.
- Minor ecosystem announcements.
- Limited product updates.
- Developments affecting only a small part of an ecosystem.

#### Medium

Use `medium` for relevant developments that deserve attention but do not represent an exceptionally important event.

Examples:

- Relevant partnerships.
- Normal regulatory developments.
- Important technical updates.
- Noticeable ecosystem growth.
- Relevant exchange announcements.

#### High

Use `high` for significant developments with potentially substantial consequences.

Examples:

- Major institutional investments.
- Important regulatory decisions.
- Significant security incidents.
- Major blockchain upgrades.
- Large exchange-related developments.
- Important ETF developments.

#### Very High

Use `very_high` for exceptionally important events with potentially far-reaching consequences.

Examples:

- Approval or rejection of major Bitcoin or Ethereum ETFs.
- Major regulatory decisions affecting the entire cryptocurrency market.
- Large-scale exchange collapses.
- Critical security breaches with substantial financial consequences.
- Major blockchain failures.
- Extraordinary institutional adoption.
- Events that fundamentally change the market environment.

#### Importance classification rules

1. Evaluate the actual content and its significance.
2. Consider the scale of the affected cryptocurrency or market.
3. Consider the potential consequences.
4. Distinguish between minor announcements and genuinely significant developments.
5. Do not automatically assign high importance just because a news headline sounds dramatic.
6. Do not automatically assign low importance to negative news.
7. Positive and negative news can both have any importance level.
8. Sentiment and importance must be evaluated independently.
9. Do not exaggerate importance based on speculation.
10. If the information is insufficient to establish the significance reliably, leave the item open.

### 6. url

The original URL of the collected news entry from config.json.

Requirements:

- Read the URL directly from the original news entry.
- Copy the complete URL without modification.
- Preserve all URL parameters and query strings.
- Do not shorten URLs.
- Do not replace the original URL with a different website.
- Do not generate or invent URLs.
- Do not use the URL from another news entry.
- If the original entry has no URL, export `null`.
- Always include the `url` field, even when its value is `null`.

For example, if config.json contains:

```json
{
  "date": "2026-11-06T02:26:00Z",
  "title": "Bitcoin tumbles to $76,000 as collapsing AI trade drags stocks sharply lower - CoinDesk",
  "source": "Google News",
  "url": "https://news.google.com/rss/articles/EXAMPLE?oc=5",
  "summary": "Original article summary",
  "id": "CBMi0gFBVV95cUxPN3VFZFhZ",
  "kind": "rss",
  "status": "offen"
}
```

The exported `url` must contain exactly the same URL as the original entry.

Never use the summary's embedded HTML link as a replacement if the original `url` field already exists.

# 4. Output: news-results.json

Save all successfully analyzed news in:

`backend/News_card/news-results.json`

The required JSON structure is:

```json
{
  "results": [
    {
      "id": "generated-uuid-v5",
      "title": "Bitcoin ETF receives approval",
      "coin_name": "Bitcoin",
      "sentiment": "positive",
      "importance": "very_high",
      "url": "https://example.com/bitcoin-etf-approval"
    },
    {
      "id": "generated-uuid-v5",
      "title": "Ethereum network suffers major outage",
      "coin_name": "Ethereum",
      "sentiment": "negative",
      "importance": "high",
      "url": "https://example.com/ethereum-outage"
    },
    {
      "id": "generated-uuid-v5",
      "title": "Global crypto regulation announced",
      "coin_name": "General Market",
      "sentiment": "negative",
      "importance": "medium",
      "url": "https://example.com/crypto-regulation"
    }
  ]
}
```

These are illustrative examples. Actual IDs must be generated using the UUIDv5 rules described above.

## 4.1 Exact Export Schema

Every result must contain exactly these six fields:

| Field | Description |
|---|---|
| `id` | Generated UUIDv5 primary ID |
| `title` | Original news title |
| `coin_name` | Affected cryptocurrency |
| `sentiment` | positive or negative |
| `importance` | One of the five importance levels |
| `url` | Original news URL or null |

The original source `news_id` must never be included in the exported JSON.

Do not add:

- `news_id`
- `source_news_id`
- `date`
- `source`
- `summary`
- `kind`
- `status`
- Explanations
- Confidence scores
- Additional metadata

The export must remain limited to the six specified fields.

## 4.2 Export Rules

- Each result must contain exactly six fields.
- Preserve the original title.
- Preserve the original URL.
- Generate the primary ID deterministically.
- Never export the original source news ID.
- Use only the allowed sentiment values.
- Use only the allowed importance values.
- Store valid JSON using UTF-8 encoding.
- Preserve all existing valid results.
- Never overwrite existing results with an empty list.
- Do not create duplicate results for the same original source news ID.
- Use atomic file writing to prevent corruption.
- Keep the JSON structure valid.
- Do not modify the original collection functionality.

# 5. Status Management

The original news entries in config.json have a status field.

The analysis process must use this field to control processing.

Possible statuses:

- `"offen"`: Waiting for AI analysis.
- `"erledigt"`: Successfully analyzed and saved.

## 5.1 Processing Sequence

For every news item with status `"offen"`:

1. Read the complete original news entry.
2. Check that the original source news ID exists.
3. Read the original title.
4. Read the original URL, if available.
5. Analyze the actual news content.
6. Identify the affected cryptocurrency or cryptocurrencies.
7. Determine whether the sentiment is positive or negative.
8. Determine the importance level.
9. Generate the deterministic UUIDv5 primary ID using the original source news ID.
10. Create the result containing exactly the six required export fields.
11. Check whether a result with the same primary ID already exists.
12. Save the result in news-results.json.
13. Verify that the result was successfully saved and can be read.
14. Only then change the original news status in config.json to `"erledigt"`.
15. Preserve every other original field and value.

Never mark a news item as `"erledigt"` before its analysis result has been successfully saved.

If analysis fails, the original status must remain `"offen"`.

If the original source news ID is missing, do not generate an arbitrary primary ID. Keep that entry open and report the missing ID.

If the information is insufficient for a reliable classification, keep the status `"offen"`.

## 5.2 Internal ID Handling

There are two different IDs with separate responsibilities:

**Original source news ID:**

- Exists in config.json.
- Used internally for identifying the original news.
- Used to generate the UUIDv5 primary ID.
- Used for duplicate prevention.
- Used for matching the original news entry.
- Never exported.

**Generated primary ID:**

- Exists in news-results.json.
- Is the permanent identifier of the exported result.
- Must remain stable across all future executions.
- Is generated deterministically using UUIDv5.
- Is the only ID visible in the export.

Never confuse these two identifiers.

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
7. Do not analyze entries already marked `"erledigt"` unless performing a necessary migration.
8. Do not create duplicate results for the same original source news ID.
9. Generate the primary ID deterministically so that the same original news always produces the same ID.
10. Before creating a result, calculate its expected primary ID and check whether it already exists.
11. If a valid result with the same primary ID already exists, do not create another result.
12. If an existing result is incomplete or invalid, correct it before changing the original status.
13. If the same original source news ID occurs in multiple source lists, prevent duplicate export results and handle the original records consistently.
14. Verify that the exported URL belongs to the correct original news entry.
15. Never use the original source news ID as the exported primary ID.

## 6.1 Existing Results and Migration

Existing versions of news-results.json may contain the old four-field or five-field format, including:

- `title`
- `coin_name`
- `news_id`
- `sentiment`
- `importance`

These results must be migrated to the new six-field schema.

Migration procedure:

1. Read all existing results.
2. Identify the original source news ID from the old `news_id` field.
3. Find the corresponding original entry in config.json.
4. Generate the UUIDv5 primary ID using the original source news ID.
5. Retrieve the original URL from config.json.
6. Preserve the existing title, coin_name, sentiment, and importance whenever valid.
7. If importance is missing, perform the importance classification using the available original news information.
8. If URL is missing from the old result, retrieve it from the original config.json entry.
9. Replace the old `news_id` field with the generated `id`.
10. Remove all fields that are not part of the new six-field schema.
11. Verify that the migrated result contains exactly the required six fields.
12. Preserve all valid existing analysis results.

If an existing result has no `importance`, do not automatically assign `medium` without evaluating the available information.

If the original news entry cannot be found, do not invent its URL or source ID. Report the migration problem and preserve the information until it can be resolved.

If an old result cannot be reliably matched to its original entry, do not guess its identity.

**Important:** Migration must not create duplicate results or lose existing valid analysis data.

## 6.2 Atomic Export

When saving news-results.json:

1. Build the complete updated results structure in memory.
2. Validate all result objects.
3. Verify that every result contains exactly six fields.
4. Verify that every primary ID is valid and unique.
5. Verify the sentiment and importance values.
6. Verify that URLs are either strings or null.
7. Write the updated JSON to a temporary file.
8. Replace the original file atomically after the temporary file has been successfully written.
9. Read the resulting file again.
10. Verify that the saved JSON is valid.

Never destroy existing valid results if an error occurs during writing.

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

For X posts, use the original post URL as the exported `url`, provided it exists in the original entry.

# 8. Reporting and Execution Summary

When the user asks for a news update:

1. Run news.py.
2. Compare the collected data before and after collection.
3. Read all relevant news entries from config.json.
4. Identify every entry with status `"offen"`.
5. Count all open entries.
6. Analyze all eligible open entries.
7. Generate a deterministic primary ID for every successfully analyzed entry.
8. Classify sentiment.
9. Classify importance.
10. Retrieve the original URL.
11. Save successful results in news-results.json.
12. Verify the saved results.
13. Update the original statuses in config.json.
14. Verify that every successfully analyzed entry is marked `"erledigt"`.
15. Report the execution results.

## 8.1 Final Execution Report

The final report must include:

- Total news entries collected.
- Total open news entries found.
- Successfully analyzed entries.
- Positive news count.
- Negative news count.
- Very low importance count.
- Low importance count.
- Medium importance count.
- High importance count.
- Very high importance count.
- Entries that remain open.
- Collection or analysis errors.
- Migration errors, if applicable.

When presenting analyzed news, use exactly these columns:

| Primary ID | Title | Coin Name | Sentiment | Importance | URL |
|---|---|---|---|---|---|

The original source news ID must never be displayed as an export field.

The URL should be presented as a clickable link when the output format supports it.

The report must accurately distinguish between newly collected entries, previously existing entries, successfully analyzed entries, and migrated results.

Do not report an entry as successfully analyzed unless its result has been saved and verified.

# 9. Separation of Responsibilities

This separation is mandatory:

- `news.py`: Collects source information and updates config.json.
- AI Analyzer: Processes all open news entries and classifies them.
- `news-results.json`: Stores the six required export fields.
- `config.json`: Maintains the original collected information and processing status.

The collector must remain independent of the AI analysis.

The AI analyzer must not modify original news content, source URLs, IDs, or other metadata.

Only the status field may be changed during successful processing.

The generated primary ID belongs exclusively to the export and must not replace the original source ID in config.json.

The original collection functionality must remain unchanged.

# 10. Mandatory Final Validation

Before completing any analysis run, verify all of the following:

- [ ] All eligible open entries have been considered.
- [ ] Every successfully analyzed entry has a valid UUIDv5 primary ID.
- [ ] Primary IDs are unique.
- [ ] Primary IDs are deterministic and stable.
- [ ] No original `news_id` is exported.
- [ ] Every result contains exactly six fields.
- [ ] Every title matches the original title.
- [ ] Every coin_name is correctly identified.
- [ ] Every sentiment is either `positive` or `negative`.
- [ ] Every importance value is one of `very_low`, `low`, `medium`, `high`, or `very_high`.
- [ ] Every URL matches the original URL from config.json, or is null if unavailable.
- [ ] No duplicate results exist.
- [ ] Existing valid results have been preserved.
- [ ] All required migrations have been completed or reported.
- [ ] The JSON file is valid and readable.
- [ ] All successfully exported entries are marked `"erledigt"`.
- [ ] Failed or insufficiently supported analyses remain `"offen"`.
- [ ] The original collector functionality remains unchanged.

**These requirements are mandatory and must be followed during every execution of this skill.**