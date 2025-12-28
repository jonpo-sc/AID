from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
SEARCH_ENDPOINT = "https://duckduckgo.com/html/"


@dataclass
class PageContent:
    url: str
    status: int
    text_preview: str


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    page: PageContent | None = None


class KeywordCrawler:
    def __init__(
        self,
        keyword: str,
        max_results: int = 10,
        max_pages: int = 3,
        delay: float = 1.0,
        timeout: int = 15,
    ) -> None:
        self.keyword = keyword
        self.max_results = max_results
        self.max_pages = max_pages
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def search(self) -> List[SearchResult]:
        results: List[SearchResult] = []
        offset = 0

        while len(results) < self.max_results:
            response = self.session.post(
                SEARCH_ENDPOINT,
                data={"q": self.keyword, "s": offset},
                timeout=self.timeout,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            new_results = self._parse_results(soup)
            if not new_results:
                break

            for result in new_results:
                results.append(result)
                if len(results) >= self.max_results:
                    break

            offset += len(new_results)
            time.sleep(self.delay)

        return results

    def fetch_pages(self, results: List[SearchResult]) -> List[SearchResult]:
        to_fetch = results[: self.max_pages]
        for index, result in enumerate(to_fetch, start=1):
            try:
                response = self.session.get(result.url, timeout=self.timeout)
                status = response.status_code
                preview = self._extract_text_preview(response.text)
            except requests.RequestException as error:
                status = 0
                preview = f"Request failed: {error}"

            result.page = PageContent(
                url=result.url,
                status=status,
                text_preview=preview,
            )
            if index < len(to_fetch):
                time.sleep(self.delay)

        return results

    def _parse_results(self, soup: BeautifulSoup) -> List[SearchResult]:
        parsed: List[SearchResult] = []
        for body in soup.select("div.result__body"):
            link_tag = body.select_one("a.result__a")
            snippet_tag = body.select_one("a.result__snippet") or body.select_one("div.result__snippet")
            if not link_tag:
                continue

            url = link_tag.get("href")
            if not url:
                continue

            parsed.append(
                SearchResult(
                    title=link_tag.get_text(strip=True),
                    url=url,
                    snippet=snippet_tag.get_text(strip=True) if snippet_tag else "",
                    source=urlparse(url).netloc,
                )
            )

        return parsed

    def _extract_text_preview(self, html: str, limit: int = 400) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(part.strip() for part in soup.stripped_strings)
        return text[:limit]


def run(keyword: str, max_results: int, max_pages: int, output: Path, delay: float, timeout: int) -> Path:
    crawler = KeywordCrawler(
        keyword=keyword,
        max_results=max_results,
        max_pages=max_pages,
        delay=delay,
        timeout=timeout,
    )
    results = crawler.search()
    crawler.fetch_pages(results)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump([asdict(result) for result in results], file, ensure_ascii=False, indent=2)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the web by keyword and fetch page previews.")
    parser.add_argument("keyword", help="Keyword to search for")
    parser.add_argument("--max-results", type=int, default=10, help="Number of search results to collect")
    parser.add_argument("--max-pages", type=int, default=3, help="Number of result pages to fetch for previews")
    parser.add_argument("--output", type=Path, default=Path("crawl_results.json"), help="Output JSON file path")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between network requests in seconds")
    parser.add_argument("--timeout", type=int, default=15, help="Request timeout in seconds")

    args = parser.parse_args()
    output_path = run(
        keyword=args.keyword,
        max_results=args.max_results,
        max_pages=args.max_pages,
        output=args.output,
        delay=args.delay,
        timeout=args.timeout,
    )
    print(f"Saved {args.max_results} results for '{args.keyword}' to {output_path}")


if __name__ == "__main__":
    main()
