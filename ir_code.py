import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# Function to fetch movie details from IMDb
def get_movie_details_from_imdb(movie_name):
    try:
        search_url = f"https://www.imdb.com/find?q={movie_name.replace(' ', '+')}&s=tt"
        response = requests.get(search_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        result = soup.find("td", class_="result_text")
        if not result:
            print(f"❌ No IMDb result found for {movie_name}")
            return {"genre": "Not found", "director": "Not found", "cast": "Not found", "release_date": "Not found", "runtime": "Not found", "rating": "Not found"}

        # Extract the relative link and make the movie page URL
        relative_link = result.find("a")["href"]
        movie_url = f"https://www.imdb.com{relative_link}"
        movie_response = requests.get(movie_url)
        movie_soup = BeautifulSoup(movie_response.text, 'html.parser')

        # Extract genre
        genre_section = movie_soup.find("div", {"data-testid": "genres"})
        genres = []
        if genre_section:
            genre_links = genre_section.find_all("a")
            genres = [link.get_text(strip=True) for link in genre_links]

        # Extract director
        director_section = movie_soup.find("div", {"data-testid": "title-pc-principal-credit"})
        director = "Not found"
        if director_section:
            director_tag = director_section.find("a")
            if director_tag:
                director = director_tag.get_text(strip=True)

        # Extract cast
        cast_section = movie_soup.find("div", {"data-testid": "title-cast"})
        cast = []
        if cast_section:
            cast_tags = cast_section.find_all("a", {"data-testid": "title-cast-item"})
            cast = [tag.get_text(strip=True) for tag in cast_tags]

        # Extract release date
        release_date_section = movie_soup.find("a", {"title": "See more release dates"})
        release_date = "Not found"
        if release_date_section:
            release_date = release_date_section.get_text(strip=True)

        # Extract runtime
        runtime_section = movie_soup.find("li", {"data-testid": "title-techspec_runtime"})
        runtime = "Not found"
        if runtime_section:
            runtime = runtime_section.get_text(strip=True)

        # Extract IMDb rating
        rating_section = movie_soup.find("span", {"data-testid": "title-rating"})
        rating = "Not found"
        if rating_section:
            rating = rating_section.get_text(strip=True)

        return {
            "genre": ", ".join(genres) if genres else "Not found",
            "director": director,
            "cast": ", ".join(cast) if cast else "Not found",
            "release_date": release_date,
            "runtime": runtime,
            "rating": rating
        }
    except Exception as e:
        print(f"❌ Error fetching IMDb details for {movie_name}: {e}")
        return {"genre": "Not found", "director": "Not found", "cast": "Not found", "release_date": "Not found", "runtime": "Not found", "rating": "Not found"}

# Function to fetch movie details from Wikipedia
def fetch_wiki_data(movie_name):
    try:
        formatted_name = movie_name.strip().replace(" ", "_")
        url = f"https://en.wikipedia.org/wiki/{formatted_name}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Wikipedia page not found for {movie_name}")
            return None, None
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract genre
        genre = "Not found"
        infobox = soup.find("table", class_="infobox vevent")
        if infobox:
            for row in infobox.find_all("tr"):
                header = row.find("th")
                if header and ("Genre" in header.text or "Genres" in header.text):
                    genre_cell = row.find("td")
                    if genre_cell:
                        genres = [li.get_text() for li in genre_cell.find_all(["li", "a"])]
                        genre = ", ".join(set(genres)) if genres else genre_cell.get_text(separator=", ").strip()

        # Extract plot
        plot = "Not found"
        plot_header = soup.find(id="Plot")
        if plot_header:
            plot_paragraph = plot_header.find_next("p")
            if plot_paragraph:
                plot = plot_paragraph.get_text().strip()

        return genre, plot
    except Exception as e:
        print(f"❌ Error fetching Wikipedia data for {movie_name}: {e}")
        return "Not found", "Not found"

# Function to infer genre from plot description if not found
def infer_genre_from_plot(plot):
    keywords = {
        "Action": ["battle", "fight", "war", "explosion", "chase"],
        "Drama": ["family", "relationship", "emotional", "struggle"],
        "Comedy": ["funny", "hilarious", "laugh", "joke"],
        "Sci-Fi": ["space", "alien", "future", "robot"],
        "Romance": ["love", "romantic", "affair", "relationship"],
        "Thriller": ["murder", "mystery", "crime", "investigation"]
    }
    found = []
    plot_lower = plot.lower()
    for genre, words in keywords.items():
        if any(word in plot_lower for word in words):
            found.append(genre)
    return ", ".join(set(found)) if found else "Not found"

# Function to get movie info
def get_movie_info(movie_name):
    genre, plot = fetch_wiki_data(movie_name)

    if genre == "Not found" and plot == "Not found":
        print(f"🔁 Retrying with film tag: {movie_name} (film)")
        genre, plot = fetch_wiki_data(f"{movie_name} (film)")

    # Fetch details from IMDb if not found in Wikipedia
    if genre == "Not found":
        print(f"🔁 Genre not found on Wikipedia, trying IMDb for {movie_name}")
        imdb_details = get_movie_details_from_imdb(movie_name)
        genre = imdb_details["genre"]
        director = imdb_details["director"]
        cast = imdb_details["cast"]
        release_date = imdb_details["release_date"]
        runtime = imdb_details["runtime"]
        rating = imdb_details["rating"]

    # If genre is still not found, infer it from the plot
    if genre == "Not found" and plot != "Not found":
        genre = infer_genre_from_plot(plot)

    # Ensure genre is not left as "Not found"
    if genre == "Not found":
        genre = "Genre not available"

    return {
        "Name": movie_name,
        "Genre": genre,
        "Plot": plot,
        "Director": director,
        "Cast": cast,
        "Release Date": release_date,
        "Runtime": runtime,
        "Rating": rating
    }

# List of movie names
movie_names = [
    "Inception",
    "The Godfather",
    "Interstellar",
    "Forrest Gump",
    "Avengers: Endgame"
]

# Scrape movie info
movie_data = []
for name in movie_names:
    print(f"📘 Searching: {name}")
    info = get_movie_info(name)
    movie_data.append(info)

# Save to Excel
file_path = r"C:\\Project\\movie_summary.xlsx"

if os.path.exists(file_path):
    existing_df = pd.read_excel(file_path)

    if 'Name' not in existing_df.columns:
        existing_df['Name'] = None

    existing_names = existing_df['Name'].tolist()

    # Ensure 'Genre' column is of type object (for strings)
    if 'Genre' in existing_df.columns:
        existing_df['Genre'] = existing_df['Genre'].astype('object')
    else:
        existing_df['Genre'] = None

    updated_df = existing_df.copy()

    for entry in movie_data:
        if entry['Name'] in existing_names:
            updated_df.loc[updated_df['Name'] == entry['Name'], ['Genre', 'Plot', 'Director', 'Cast', 'Release Date', 'Runtime', 'Rating']] = entry['Genre'], entry['Plot'], entry['Director'], entry['Cast'], entry['Release Date'], entry['Runtime'], entry['Rating']
        else:
            updated_df = pd.concat([updated_df, pd.DataFrame([entry])], ignore_index=True)

    try:
        updated_df.to_excel(file_path, index=False)
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
