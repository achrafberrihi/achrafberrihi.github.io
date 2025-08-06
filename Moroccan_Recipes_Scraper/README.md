# Moroccan Recipes Scraper

This project is a simple web scraper that collects recipe information from a Moroccan cooking website. It extracts details like recipe title, ingredients, preparation steps, and images, and stores them in a structured format for analysis or culinary exploration.

## Features

- Scrapes multiple recipe pages for titles, ingredients, and instructions.
- Uses BeautifulSoup for HTML parsing.
- Saves extracted data to a CSV file.
- Handles polite scraping with delays between requests.

## Files

- `scraper.py` – Python script to perform web scraping and save the data.

## Usage

1. Install dependencies (`requests`, `beautifulsoup4`, `pandas`).
2. Set the base URL and number of pages to scrape in `scraper.py`.
3. Run the script: `python scraper.py`.
4. Find your scraped data in `recipes.csv`.
