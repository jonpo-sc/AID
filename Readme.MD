# Keyword-based Web Crawler

This repository contains a small Python crawler that searches the web for a keyword using the DuckDuckGo HTML endpoint and collects page previews.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the crawler with your keyword and optional flags:

```bash
python search_crawler.py "你的关键字" --max-results 10 --max-pages 3 --output crawl_results.json
```

Options:
- `--max-results` – number of search results to collect (default: 10)
- `--max-pages` – how many of the top results to fetch for content previews (default: 3)
- `--delay` – delay in seconds between network requests (default: 1.0)
- `--timeout` – network request timeout in seconds (default: 15)
- `--output` – path to the JSON file to save results (default: `crawl_results.json`)

The output file contains an array of search results with titles, URLs, snippets, and previews of the fetched pages.
