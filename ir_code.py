import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def get_movie_info(movie_name):
    def fetch_wiki_data(name_variant):
        formatted_name = name_variant.strip().replace(" ", "_")
        url = f"https://en.wikipedia.org/wiki/{formatted_name}"
        response = requests.get(url)
        if response.status_code != 200:
            return None, None
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get genre from infobox
        genre = "Not found"
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

        # Get plot section
        plot = "Not found"
        plot_header = soup.find(id="Plot")
        if plot_header:
            plot_paragraph = plot_header.find_next("p")
            if plot_paragraph:
                plot = plot_paragraph.get_text().strip()

        return genre, plot

    # Try original name
    genre, plot = fetch_wiki_data(movie_name)

    # If not found, try "Movie Name (film)"
    if genre is None and plot is None:
        print(f"🔁 Retrying with film tag: {movie_name} (film)")
        genre, plot = fetch_wiki_data(f"{movie_name} (film)")

    # Still not found?
    if genre is None and plot is None:
        print(f"❌ Page not found even with film tag: {movie_name}")
        genre = "Not found"
        plot = "Not found"

    return {
        "Name": movie_name,
        "Genre": genre,
        "Plot": plot
    }

# ✅ You can change the movie list here
movie_names = [
    "Inception",
    "The Godfather",
    "Interstellar",
    "Forrest Gump",
    "Avengers: Endgame"
]

# 🔍 Scrape all movie info
movie_data = []
for name in movie_names:
    print(f"📘 Searching: {name}")
    info = get_movie_info(name)
    movie_data.append(info)

# 🔽 Set your Excel file path here
file_path = r"C:\Project\movie_summary.xlsx"

# ✅ Check if file exists and update, otherwise create
if os.path.exists(file_path):
    existing_df = pd.read_excel(file_path)
    new_df = pd.DataFrame(movie_data)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    try:
        combined_df.to_excel(file_path, index=False)
        print(f"✅ Excel file updated at {file_path}")
    except PermissionError:
        print("❌ Permission denied: Please close the Excel file before running the script again.")
else:
    new_df = pd.DataFrame(movie_data)
    try:
        new_df.to_excel(file_path, index=False)
        print(f"✅ New Excel file created at {file_path}")
    except PermissionError:
        print("❌ Permission denied: Please close the Excel file before running the script again.")
