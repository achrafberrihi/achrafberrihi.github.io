# Moroccan Recipes Scraper

This project is a simple web scraper that collects recipe information from a Moroccan cooking website. It extracts details like recipe title, ingredients, preparation steps, and images, and stores them in a structured format for analysis or culinary exploration.

## Features

- Scrapes multiple recipe pages for titles, ingredients, and instructions.
- Uses BeautifulSoup for HTML parsing.
- Saves extracted data to a CSV file.
- Timeouts, a descriptive User-Agent, and per-page error handling so one bad page does not stop the run.
- Handles polite scraping with delays between requests.

## Files

- `scraper.py` – Python script to perform web scraping and save the data.

## Usage

1. Install dependencies: `pip install -r ../requirements.txt`.
2. Set `BASE_URL` and the CSS `SELECTORS` for the target site in `scraper.py`, and check its robots.txt and terms of use.
3. Run: `python scraper.py --pages 5 --delay 2 --out recipes.csv`.
4. Find your scraped data in `recipes.csv`.
