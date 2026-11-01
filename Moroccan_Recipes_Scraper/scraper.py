"""Polite recipe scraper: collects titles, ingredients and steps into a CSV.

Set BASE_URL and the CSS selectors for the target site, check its robots.txt
and terms of use, then run:  python scraper.py --pages 5 --delay 2
"""
import argparse
import logging
import time
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.example.com/recipes?page="
SELECTORS = {
    "card_link": ".recipe-card a",
    "title": "h1",
    "ingredients": ".ingredients li",
    "instructions": ".instructions li",
}
HEADERS = {"User-Agent": "MoroccanRecipesScraper/1.0 (educational project)"}

log = logging.getLogger(__name__)
session = requests.Session()
session.headers.update(HEADERS)


def get_soup(url: str) -> BeautifulSoup:
    response = session.get(url, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


def fetch_recipe_links(page: int) -> list[str]:
    url = f"{BASE_URL}{page}"
    soup = get_soup(url)
    return list(dict.fromkeys(urljoin(url, a["href"]) for a in soup.select(SELECTORS["card_link"]) if a.get("href")))


def parse_recipe(url: str) -> dict:
    soup = get_soup(url)
    title = soup.select_one(SELECTORS["title"])
    return {
        "title": title.get_text(strip=True) if title else "",
        "ingredients": " | ".join(li.get_text(strip=True) for li in soup.select(SELECTORS["ingredients"])),
        "instructions": " | ".join(li.get_text(strip=True) for li in soup.select(SELECTORS["instructions"])),
        "url": url,
    }


def scrape_recipes(pages: int = 1, delay: float = 1.0) -> list[dict]:
    recipes = []
    for page in range(1, pages + 1):
        try:
            links = fetch_recipe_links(page)
        except requests.RequestException as exc:
            log.warning("Skipping page %s: %s", page, exc)
            continue
        for link in links:
            try:
                recipes.append(parse_recipe(link))
            except requests.RequestException as exc:
                log.warning("Skipping %s: %s", link, exc)
            time.sleep(delay)  # be respectful to the server
    return recipes


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Scrape recipes into a CSV file.")
    parser.add_argument("--pages", type=int, default=5)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--out", default="recipes.csv")
    args = parser.parse_args()

    data = scrape_recipes(pages=args.pages, delay=args.delay)
    pd.DataFrame(data).to_csv(args.out, index=False)
    log.info("Saved %d recipes to %s", len(data), args.out)
