# Stock Fundamental Scanner (Phase 1 MVP)

A lean fundamental scanner for daily stock trading preparation. This tool reads a manual watchlist and fetches recent news, upcoming earnings, and recent SEC filings to compute a relevance score for each ticker.

## Features
- **Manual Watchlist:** Simple YAML-based watchlist management.
- **News Integration:** Fetches recent news and sentiment from Marketaux.
- **Earnings Calendar:** Tracks upcoming earnings via Finnhub.
- **SEC Filings:** Monitors 8-K, 10-Q, and 10-K filings via SEC EDGAR.
- **Scoring Engine:** Deterministic scoring based on fundamental catalysts.
- **Local Output:** Console table and CSV export.

## Tech Stack
- Python 3.11+
- Pydantic & Pydantic-Settings
- HTTPX & Tenacity
- Pandas & PyYAML
- Pytest (for testing)

## Setup

1. **Clone the repository** (or copy the files).
2. **Install dependencies**:
   ```bash
   pip install -e .
   ```
3. **Configure Environment**:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   - `MARKETAUX_API_KEY`: Get from [Marketaux](https://www.marketaux.com/).
   - `FINNHUB_API_KEY`: Get from [Finnhub](https://finnhub.io/).
   - `SEC_USER_AGENT`: Your name/email as per SEC requirements.

4. **Prepare Watchlist**:
   Edit `config/watchlist.yaml` (see `config/watchlist.example.yaml` for format).

## Usage

### CLI Mode
Run the scanner from the terminal:
```bash
python -m app.main
```

### Web GUI Mode (Streamlit)
Launch the local web interface:
```bash
streamlit run app/ui/streamlit_app.py
```
The GUI allows you to edit the watchlist, run scans, and view results interactively.

The tool will:
1. Load your watchlist.
2. Fetch data for each symbol.
3. Print a ranked table to the console.
4. Save a detailed CSV to the `output/` directory.

## Scoring Logic
- **Earnings**: +30 for today, +20 for tomorrow.
- **Filings**: +25 for 8-K (last 12h), +15 for 10-Q/10-K (last 24h), +10 for any in lookback.
- **News**: Up to +10 based on volume and sentiment.
- **Clamp**: Final score is clamped between 0 and 100.

## Project Structure
```text
stock-fundamental-scanner/
  app/
    providers/   # API integrations
    services/    # Core logic (watchlist, scanner, scoring, report)
    models.py    # Data structures
    config.py    # Configuration management
  config/        # Watchlist and settings
  output/        # CSV reports
  tests/         # Unit and integration tests
```

## Current Limitations (Phase 1)
- Manual watchlist only.
- Local execution only (no scheduler).
- Limited filing types (8-K, 10-Q, 10-K).
- No database or web UI.
