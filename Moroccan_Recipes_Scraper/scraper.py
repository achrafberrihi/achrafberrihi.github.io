import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Base URL of the recipes website
BASE_URL = 'https://www.example.com/recipes?page='


def fetch_recipe_links(page: int) -> list:
    """Fetches recipe links from a given page number."""
    response = requests.get(BASE_URL + str(page))
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find all recipe links (update the selector based on the target website)
    links = [a['href'] for a in soup.select('.recipe-card a')]
    return links


def parse_recipe(url: str) -> dict:
    """Parses a single recipe page and extracts relevant information."""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.select_one('h1').get_text(strip=True)
    ingredients = [li.get_text(strip=True) for li in soup.select('.ingredients li')]
    instructions = [step.get_text(strip=True) for step in soup.select('.instructions li')]
    return {
        'title': title,
        'ingredients': ingredients,
        'instructions': instructions,
        'url': url
    }


def scrape_recipes(pages: int = 1, delay: float = 1.0) -> list:
    """Scrapes multiple pages of recipes and returns a list of recipe data."""
    all_recipes = []
    for page in range(1, pages + 1):
        recipe_links = fetch_recipe_links(page)
        for link in recipe_links:
            recipe_data = parse_recipe(link)
            all_recipes.append(recipe_data)
            time.sleep(delay)  # respectful scraping delay
    return all_recipes


def save_to_csv(recipes: list, filename: str = 'recipes.csv') -> None:
    """Saves scraped recipes to a CSV file."""
    df = pd.DataFrame(recipes)
    df.to_csv(filename, index=False)


if __name__ == '__main__':
    # Scrape the first 5 pages with a 2-second delay between requests
    recipes = scrape_recipes(pages=5, delay=2.0)
    save_to_csv(recipes)
