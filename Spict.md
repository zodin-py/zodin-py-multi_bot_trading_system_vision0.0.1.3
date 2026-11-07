# TECHNICAL SPECIFICATION
# Binance Crypto Candlestick Data & Chart Module

**Version:** 1.0  
**Project type:** Erweiterung eines bestehenden Python-Kryptoanalyseprogramms  
**Priority:** Data Integrity, Reliability, Visualization  
**Status:** Ready for implementation planning

---

# 1. PROJECT OVERVIEW

## 1.1 Project Goal

The goal is to extend the existing Python cryptocurrency analysis application with a professional market-data collection, storage, and visualization module.

The existing application is already connected to Binance and retrieves market information.

This project must build on that existing infrastructure.

The new functionality must enable the application to:

1. Retrieve historical cryptocurrency candlestick data from Binance.
2. Load the latest 1,000 completed candles.
3. Store all candle data persistently in JSON files.
4. Automatically detect when a new candle has closed.
5. Retrieve and store only completed candles.
6. Prevent duplicate, missing, or corrupted candle records.
7. Display the historical price movement in an interactive candlestick chart inside a dedicated UI container.
8. Update the chart automatically whenever new completed candles become available.

The primary objective is to create a reliable historical market-data foundation for future cryptocurrency analysis.

## 1.2 Important Project Constraints

The following constraints are mandatory:

- Do NOT create a completely new application.
- Do NOT replace the existing Binance API connection.
- Do NOT unnecessarily rewrite existing modules.
- Do NOT remove existing functionality.
- Do NOT introduce trading strategies or trading signals.
- Do NOT implement automatic buying or selling.
- Do NOT store incomplete candles.
- Do NOT unnecessarily download all historical data on every application restart.
- Do NOT introduce a database such as PostgreSQL or MongoDB for this version.

JSON is the primary persistent storage format.

The implementation must integrate into the existing project architecture.

---

# 2. INITIAL PROJECT ANALYSIS

Before writing or modifying any code, perform a complete analysis of the existing repository.

The existing project structure, framework, dependencies, Binance implementation, and application entry points are currently unknown.

Do not make assumptions about them.

## 2.1 Repository Inspection

Inspect:

- Project directory structure.
- Main application entry point.
- Existing Binance API client.
- Existing API authentication.
- Existing environment variables.
- Existing configuration files.
- Existing data collection functions.
- Existing logging implementation.
- Existing UI framework.
- Existing visualization libraries.
- Existing JSON or other storage mechanisms.
- Existing scheduling mechanisms.
- Existing error-handling patterns.

## 2.2 Identify Reusable Components

Identify which existing components can be reused.

Particularly important:

- Binance client.
- HTTP session.
- API configuration.
- Symbol configuration.
- Existing logging system.
- Existing UI components.
- Existing refresh mechanisms.

Do not implement a second Binance client if the existing one already provides the required functionality.

## 2.3 Analysis Report

Before implementation, provide a short report containing:

1. Existing architecture.
2. Relevant files and modules.
3. Existing Binance integration.
4. Existing UI framework.
5. Recommended integration point.
6. Files that need to be created.
7. Files that need to be modified.
8. Potential compatibility risks.

After this analysis, propose an implementation plan.

Do not begin major modifications until the architecture and implementation plan are clear.

---

# 3. FUNCTIONAL REQUIREMENTS

## FR-01: Binance API Integration

The module must retrieve historical candlestick data through the existing Binance connection.

Use Binance's Kline/Candlestick market-data endpoint.

Depending on the existing application, identify the correct market type:

- Binance Spot.
- Binance USDⓈ-M Futures.
- Binance COIN-M Futures.

Do not silently mix data from different markets.

The implementation must use the existing market configuration wherever possible.

If the existing client does not support historical Klines, extend it without breaking its existing functionality.

For public market data, use the appropriate public market-data endpoint. Do not unnecessarily introduce API credentials where they are not required.

## FR-02: Supported Symbols

The module must work with configurable cryptocurrency trading pairs.

Examples:

- BTCUSDT
- ETHUSDT
- SOLUSDT
- BNBUSDT
- KITEUSDT

These are examples, not a fixed list.

The application should use the symbols already configured in the existing project.

If the application already supports multiple symbols, the candle module should integrate with that configuration.

## FR-03: Timeframe Configuration

The initial default timeframe is:

**5 minutes (5m)**

The architecture should support future configuration of additional Binance intervals, such as:

- 1m
- 3m
- 5m
- 15m
- 30m
- 1h
- 4h
- 1d

However, version 1.0 only needs to implement the configured initial timeframe.

Timeframe handling must use Binance's official interval definitions rather than manually assuming all intervals have identical calendar behavior.

## FR-04: Historical Candle Retrieval

On the first initialization of a symbol/timeframe combination:

Retrieve the latest 1,000 historical candles.

Requirements:

- Request a maximum of 1,000 candles per symbol/timeframe.
- Retrieve data in chronological order.
- Validate every candle.
- Exclude incomplete candles.
- Remove duplicates.
- Store the resulting dataset in JSON.

The initial dataset should contain up to 1,000 completed candles.

If fewer than 1,000 candles are available, store all available completed candles.

## FR-05: Incremental Data Retrieval

After initialization, the application must use the existing JSON dataset as its starting point.

It must NOT download the entire historical dataset again on every restart.

Instead:

1. Load the existing JSON file.
2. Identify the timestamp of the latest stored candle.
3. Determine whether additional completed candles are available.
4. Request only the missing or newer candles.
5. Validate the received data.
6. Merge new records with existing records.
7. Remove duplicates.
8. Maintain the maximum of 1,000 records.
9. Save the updated dataset.

The system must also detect missing intervals and retrieve missing candles when possible.

Never assume that the newest timestamp alone proves that the historical dataset is complete.

## FR-06: Completed Candle Validation

This is one of the most important requirements.

The application must only store fully completed candles.

Binance Kline responses contain:

- Open time.
- Open price.
- High price.
- Low price.
- Close price.
- Base asset volume.
- Close time.
- Quote asset volume.
- Number of trades.
- Taker buy volume.
- Additional exchange fields.

The implementation must correctly identify the candle's closing time.

Use Binance server time or another reliable exchange-time reference for determining whether a candle has closed.

A candle is eligible for storage only when:

`candle.close_time < binance_server_time`

The exact comparison must respect Binance's timestamp semantics.

An incomplete candle must never be written to the persistent historical dataset.

Do not use the local computer clock as the sole authority for candle completion.

## FR-07: Candle Update Scheduling

The update mechanism must be synchronized with the selected timeframe.

For the initial 5-minute timeframe:

- 10:00
- 10:05
- 10:10
- 10:15
- 10:20

The application must wait until the current 5-minute interval has ended.

Then:

1. Wait approximately 2 seconds as a configurable safety buffer.
2. Retrieve Binance server time.
3. Request the latest Klines.
4. Identify completed candles.
5. Ignore incomplete candles.
6. Save newly completed candles.
7. Notify the chart component that new data is available.

The update must not be based on an arbitrary one-minute polling interval.

The scheduling logic must calculate the next valid candle boundary.

It must also handle:

- Application startup in the middle of a candle.
- Delayed API responses.
- Network interruptions.
- Temporary Binance API failures.
- Missed update intervals.
- Computer sleep and wake-up.
- Application restarts.

After an interruption, the application must catch up on missing completed candles instead of simply continuing with the newest candle.

## FR-08: Duplicate Prevention

Each candle must have a unique identity based on:

- Exchange.
- Market type.
- Symbol.
- Timeframe.
- Candle open timestamp.

A candle must never appear twice in the same dataset.

When an existing candle is received again, the system must recognize it and handle it deterministically.

## FR-09: Historical Data Retention

The JSON dataset must contain a maximum of 1,000 completed candles per symbol/timeframe combination.

When a new candle is added and the limit is exceeded:

- Remove the oldest candle.
- Preserve the newest 1,000 completed candles.
- Keep the dataset chronologically sorted.

The retention limit should be configurable.

---

# 4. DATA STORAGE ARCHITECTURE

## 4.1 Storage Format

Use JSON as the persistent storage format.

Recommended directory structure:

```text
project/
│
├── data/
│   └── candles/
│       ├── BTCUSDT_5m.json
│       ├── ETHUSDT_5m.json
│       └── SOLUSDT_5m.json
│
└── existing_project_files/
```

Adapt the directory structure to the existing repository.

Do not create unnecessary duplicate configuration files.

## 4.2 JSON Schema

Use the following logical structure:

```json
{
  "metadata": {
    "exchange": "binance",
    "market_type": "spot",
    "symbol": "BTCUSDT",
    "timeframe": "5m",
    "candle_count": 1000,
    "last_update": "2026-11-07T18:35:02Z",
    "last_candle_open_time": 1794076200000,
    "version": 1
  },
  "candles": [
    {
      "open_time": 1794076200000,
      "close_time": 1794076499999,
      "timestamp": "2026-11-07T18:30:00Z",
      "open": 100000.50,
      "high": 100120.00,
      "low": 99950.00,
      "close": 100080.25,
      "volume": 125.75,
      "quote_volume": 12580000.50,
      "trades": 1520,
      "taker_buy_base_volume": 65.20,
      "taker_buy_quote_volume": 6520000.00
    }
  ]
}
```

All values above are illustrative.

Use actual values returned by Binance.

## 4.3 Data Types

Requirements:

- Timestamps must be stored in UTC.
- Binance timestamps should retain millisecond precision.
- Prices and volumes must be stored without unnecessary precision loss.
- Do not use rounded display values for persistent storage.
- Preserve the original numeric precision where practical.
- Store the number of trades as an integer.

For financial calculations, avoid introducing binary floating-point precision errors unnecessarily.

Use an appropriate decimal representation internally where needed.

## 4.4 Atomic JSON Writes

The storage system must protect existing data against interrupted writes.

Recommended procedure:

1. Build the complete updated JSON object.
2. Write it to a temporary file.
3. Flush and close the temporary file.
4. Replace the original file atomically.
5. Preserve the previous valid file if the operation fails.

Never truncate the original JSON file before the new dataset has been successfully written.

## 4.5 Storage Recovery

If a JSON file is:

- Missing.
- Empty.
- Invalid.
- Corrupted.
- Incompatible with the current schema.

The system must handle the problem safely.

It must not silently delete existing files or overwrite potentially recoverable data.

Provide meaningful logging and a controlled recovery procedure.

---

# 5. CANDLE MANAGER

Implement a dedicated candle-management component.

Its responsibility is to manage the complete lifecycle of candle data.

Expected operations:

| Operation | Description |
|---|---|
| Initialize | Load or initialize the dataset |
| Fetch history | Retrieve initial historical data |
| Fetch updates | Retrieve missing/new candles |
| Validate | Verify candle integrity |
| Deduplicate | Remove duplicate records |
| Merge | Combine existing and new data |
| Sort | Sort chronologically |
| Trim | Keep the newest 1,000 records |
| Save | Persist the dataset |
| Load | Read the dataset |

The Candle Manager must not contain UI-specific code.

The chart component must receive validated data through a clear interface.

---

# 6. CHART VISUALIZATION

## FR-10: Candlestick Chart

The application must display the collected historical data in a dedicated chart container or box.

The chart should resemble a professional cryptocurrency trading interface.

Recommended visualization library:

**Plotly Candlestick**

However, first inspect the existing UI framework and visualization dependencies.

Use a compatible solution instead of unnecessarily replacing the current interface.

If the existing application has no visualization framework, Plotly is the preferred option.

## 6.1 Chart Appearance

The chart should include:

- Dark trading-style background.
- Green bullish candles.
- Red bearish candles.
- Visible candle wicks.
- Price axis on the right.
- Time axis at the bottom.
- Subtle grid lines.
- Clear candle spacing.
- Responsive layout.

## 6.2 Chart Functionality

The chart must support:

1. Zoom in.
2. Zoom out.
3. Horizontal scrolling.
4. Mouse hover information.
5. Price inspection.
6. Timestamp inspection.
7. Automatic refresh.
8. Historical candle visualization.

Hover information should display:

- Timestamp.
- Open.
- High.
- Low.
- Close.
- Volume.

## 6.3 Chart Container

The chart must be displayed inside a dedicated UI box.

It must integrate with the existing application rather than creating an unrelated second application.

The chart container should include:

**Header:**

- Trading pair.
- Market type.
- Selected timeframe.

**Main area:**

- Interactive candlestick chart.

**Footer or information section:**

- Number of stored candles.
- Last completed candle.
- Last successful API update.
- Data connection status.

The layout should remain responsive.

## 6.4 Automatic Chart Refresh

Whenever a new completed candle has been successfully stored:

1. Notify the chart component.
2. Load the updated dataset.
3. Update the chart.
4. Preserve the user's current chart interaction where technically possible.

Do not refresh the entire application unnecessarily.

Do not reload the chart continuously while no new completed candle exists.

---

# 7. SOFTWARE ARCHITECTURE

The implementation must follow the architecture and conventions of the existing project.

The following is a logical target architecture, not an instruction to create these exact files regardless of the existing structure.

```text
Existing Application
│
├── Existing Binance Client
│
├── Market Data Layer
│   ├── Historical Kline Retrieval
│   ├── Latest Kline Retrieval
│   └── Server Time
│
├── Candle Manager
│   ├── Validation
│   ├── Deduplication
│   ├── Merge
│   └── Retention
│
├── Storage Layer
│   ├── JSON Loader
│   ├── JSON Writer
│   └── Recovery
│
├── Scheduler
│   ├── Next Candle Boundary
│   ├── Completion Check
│   └── Retry Handling
│
└── Visualization Layer
    ├── Chart Data Adapter
    ├── Candlestick Chart
    └── Chart Refresh
```

## 7.1 Separation of Responsibilities

The following responsibilities must remain separated:

- API communication.
- Data validation.
- Data storage.
- Scheduling.
- Visualization.

The Binance client should not directly manipulate UI elements.

The chart renderer should not make its own Binance API requests.

The JSON storage module should not contain scheduling logic.

## 7.2 Suggested Function Interfaces

Adapt names to the existing coding conventions.

```python
def fetch_historical_candles(
    symbol: str,
    interval: str,
    limit: int = 1000
):
    pass


def fetch_latest_candles(
    symbol: str,
    interval: str,
    start_time: int | None = None
):
    pass


def validate_candles(candles):
    pass


def merge_candles(existing, new):
    pass


def load_candles(symbol, interval):
    pass


def save_candles(symbol, interval, candles):
    pass


def get_next_candle_boundary(interval):
    pass


def update_candle_data(symbol, interval):
    pass


def render_candlestick_chart(candles):
    pass
```

These are interface examples, not finished implementations.

---

# 8. ERROR HANDLING AND RELIABILITY

The module must handle failures without corrupting historical data.

## 8.1 API Errors

Handle:

- Connection timeouts.
- HTTP errors.
- Binance rate limits.
- Invalid API responses.
- Service interruptions.
- Temporary unavailable endpoints.

Use controlled retries with exponential backoff and respect Binance rate-limit instructions.

Do not retry indefinitely without limits.

## 8.2 Data Validation

Reject candles with:

- Missing timestamps.
- Invalid numeric values.
- Negative prices.
- Negative volumes.
- High prices below low prices.
- Open or close outside the high/low range.
- Invalid timestamps.
- Incomplete status.

Do not silently convert invalid data into valid-looking candles.

## 8.3 Logging

Use the existing logging framework.

Important events should be logged:

- Initial historical download.
- Number of downloaded candles.
- Number of new completed candles.
- Duplicate records.
- Missing intervals.
- Successful JSON updates.
- API errors.
- Recovery operations.
- Chart update events.

Avoid logging API secrets or sensitive credentials.

---

# 9. PERFORMANCE REQUIREMENTS

The application should remain responsive while candles are collected and stored.

Requirements:

- Avoid unnecessary API requests.
- Avoid downloading the same historical data repeatedly.
- Keep chart data separate from unrelated application state.
- Avoid unnecessary JSON reads and writes.
- Avoid blocking the UI during network requests.
- Prevent overlapping scheduler executions.
- Prevent simultaneous writes to the same JSON file.
- Keep the implementation efficient for multiple configured trading pairs.

If multiple symbols are supported, schedule and process them without creating uncontrolled concurrent API requests.

---

# 10. TESTING REQUIREMENTS

The implementation must include automated tests.

Use the testing framework already present in the repository. If none exists, pytest is recommended.

## TEST-01: Initial Download

Given an empty dataset:

- Request 1,000 historical candles.
- Exclude incomplete candles.
- Save completed candles.
- Verify chronological order.

Expected result: A valid JSON dataset containing up to 1,000 completed candles.

## TEST-02: Restart

Given an existing valid JSON file:

- Start the application again.
- Load existing data.
- Do not repeat the initial full historical download unnecessarily.

Expected result: Existing historical data remains intact.

## TEST-03: New Candle

Given 1,000 stored candles:

- A new 5-minute candle closes.
- The application retrieves it.
- The application validates and stores it.

Expected result: The dataset contains the newest 1,000 candles.

## TEST-04: Incomplete Candle

Given a candle that is still open:

Expected result: It must not be stored.

## TEST-05: Duplicate Candle

Given a candle that already exists:

Expected result: No duplicate record is created.

## TEST-06: API Failure

Given an API timeout:

Expected result:

- Existing JSON remains intact.
- The error is logged.
- A controlled retry is scheduled.

## TEST-07: Missing Candles

Given a dataset with a missing time interval:

Expected result: The application attempts to retrieve the missing completed candles.

## TEST-08: Corrupted JSON

Given an invalid JSON file:

Expected result:

- No silent data loss.
- Recovery is logged.
- The original file is preserved when possible.

## TEST-09: Chart Rendering

Given valid historical candle data:

Expected result:

- The chart displays the correct price movement.
- Candles are chronologically ordered.
- OHLC values correspond to the stored data.

## TEST-10: Chart Update

Given a newly stored completed candle:

Expected result: The chart updates without requiring an application restart.

---

# 11. ACCEPTANCE CRITERIA

Version 1.0 is complete only when all the following requirements are satisfied.

### Data collection

- [ ] Existing Binance integration is reused.
- [ ] Correct market type is selected.
- [ ] Historical Klines are retrieved.
- [ ] Initial download contains up to 1,000 completed candles.
- [ ] New candles are retrieved incrementally.
- [ ] Only completed candles are stored.
- [ ] Server time is used for completion checks.

### Storage

- [ ] JSON storage works.
- [ ] UTC timestamps are correct.
- [ ] Duplicate candles are prevented.
- [ ] Missing intervals are detected.
- [ ] Maximum of 1,000 candles is maintained per dataset.
- [ ] Atomic writes are implemented.
- [ ] Existing data survives application restarts.

### Visualization

- [ ] Candlestick chart is visible inside a dedicated UI box.
- [ ] Green and red candles are displayed correctly.
- [ ] OHLC information is available on hover.
- [ ] Zoom and scrolling work.
- [ ] Chart updates after a completed candle is stored.
- [ ] Chart uses the existing application's UI architecture.

### Reliability

- [ ] API failures do not corrupt historical data.
- [ ] Retry handling works.
- [ ] Scheduler does not execute overlapping updates.
- [ ] Logging is implemented.
- [ ] Automated tests pass.

---

# 12. IMPLEMENTATION PHASES

Do not implement everything in one uncontrolled change.

Work in the following phases.

## Phase 1 – Existing Project Analysis

- Inspect the repository.
- Identify the existing Binance integration.
- Identify the UI framework.
- Document the architecture.
- Prepare an implementation plan.

Deliverable: Architecture analysis and implementation plan.

## Phase 2 – Binance Kline Integration

- Extend the existing Binance client.
- Implement historical Kline retrieval.
- Implement latest Kline retrieval.
- Implement server-time retrieval.
- Verify the correct market type.

Deliverable: Working market-data retrieval.

## Phase 3 – JSON Storage

- Implement JSON schema.
- Implement loading.
- Implement atomic saving.
- Implement duplicate prevention.
- Implement historical retention.
- Implement recovery.

Deliverable: Persistent candle storage.

## Phase 4 – Candle Scheduling

- Calculate the next candle boundary.
- Wait for candle completion.
- Add configurable safety buffer.
- Retrieve new completed candles.
- Handle missed intervals.
- Implement retry handling.

Deliverable: Reliable incremental candle updates.

## Phase 5 – Chart Integration

- Integrate the chart into the existing UI.
- Implement candlestick rendering.
- Add hover information.
- Add zoom and scrolling.
- Implement automatic chart refresh.

Deliverable: Interactive chart inside the existing application.

## Phase 6 – Testing and Integration

- Run automated tests.
- Test real Binance market data.
- Test API interruptions.
- Test application restarts.
- Test chart refresh.
- Check compatibility with existing functionality.

Deliverable: Fully integrated and tested MVP.

---

# 13. FUTURE EXTENSIONS – NOT PART OF VERSION 1.0

The architecture should make future extensions possible without implementing them now.

Potential future functionality:

- Multiple timeframes.
- More advanced historical data management.
- Technical indicators such as RSI, MACD, EMA and Bollinger Bands.
- Support and resistance visualization.
- Volume analysis.
- Market structure analysis.
- Volatility analysis.
- Pattern recognition.
- AI-assisted market analysis.

These features must remain outside the current implementation scope.

Do not prematurely implement them.

---

# 14. INSTRUCTIONS TO THE IMPLEMENTING LLM

You are acting as a senior Python software architect and experienced cryptocurrency market-data engineer.

Your task is to extend an existing Binance-connected cryptocurrency analysis application according to this specification.

Follow these mandatory rules:

1. Inspect the complete existing repository before changing code.
2. Understand the existing architecture and coding conventions.
3. Reuse the existing Binance connection.
4. Preserve all existing functionality.
5. Do not introduce unnecessary dependencies.
6. Do not create a second application.
7. Do not make assumptions about the existing UI framework.
8. Do not implement trading strategies or automatic trading.
9. Keep market data, storage, scheduling and visualization logically separated.
10. Implement in small, verifiable phases.
11. Run tests after every relevant implementation phase.
12. Document all modified and newly created files.
13. Explain important architectural decisions.
14. Never silently discard existing data.
15. Do not claim that functionality works unless it has actually been tested.

If a requirement conflicts with the existing architecture, explain the conflict and propose the smallest safe modification.

If important information is missing, ask specific questions instead of inventing implementation details.

## Final Deliverables

At completion, provide:

1. Summary of the implementation.
2. Updated project architecture.
3. List of created files.
4. List of modified files.
5. Explanation of Binance Kline integration.
6. Explanation of JSON data storage.
7. Explanation of candle completion and scheduling.
8. Explanation of chart integration.
9. Test results.
10. Known limitations and remaining issues.

The final implementation must be integrated into the existing project, not delivered as an isolated demonstration.

---

# END OF SPECIFICATION

**Project milestone:** Binance Historical Candle Collection + JSON Persistence + Interactive Candlestick Chart.

**Version:** 1.0