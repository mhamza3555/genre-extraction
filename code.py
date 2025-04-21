import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_movie_info(movie_name):
    # Replace spaces with underscores for Wikipedia URL format
    formatted_name = movie_name.strip().replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{formatted_name}"

    # Send a request to the page
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Could not find the Wikipedia page for '{movie_name}'")
        return None

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to extract Genre and Plot
    genre = "Not found"
    plot = "Not found"

    # Look for infobox (usually where genre is listed)
    infobox = soup.find("table", class_="infobox vevent")
    if infobox:
        for row in infobox.find_all("tr"):
            header = row.find("th")
            if header and "Genre" in header.text:
                genre_cell = row.find("td")
                if genre_cell:
                    genres = [li.get_text() for li in genre_cell.find_all(["li", "a"])]
                    genre = ", ".join(set(genres)) if genres else genre_cell.get_text(separator=", ").strip()
                break

    # Find the Plot section
    plot_header = soup.find(id="Plot")
    if plot_header:
        plot_paragraph = plot_header.find_next("p")
        if plot_paragraph:
            plot = plot_paragraph.get_text().strip()

    return {
        "Name": movie_name,
        "Genre": genre,
        "Plot": plot
    }
