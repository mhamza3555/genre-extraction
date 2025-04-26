# 🛠️ Setup and Imports
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re

# 🧹 Helper Function
def safe_get_text(tag):
    return tag.get_text(strip=True) if tag else "Not found"

# 📥 Fetch from Wikipedia
def fetch_wiki_data(movie_name):
    try:
        formatted_name = movie_name.strip().replace(" ", "_")
        url = f"https://en.wikipedia.org/wiki/{formatted_name}"
        print(f"\n🌐 Fetching Wikipedia page for: {movie_name}")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Wikipedia page not found for {movie_name}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        infobox = soup.find("table", class_="infobox vevent")
        if not infobox:
            print(f"❌ Infobox not found for {movie_name}")
            return None

        print("🔎 Searching Infobox for details...")
        details = {
            "genre": "Not found",
            "director": "Not found",
            "cast": "Not found",
            "release_date": "Not found",
            "runtime": "Not found",
            "rating": "Not found",
            "plot": "Not found"
        }

        genre_keys = ["Genre", "Genres"]
        director_keys = ["Directed by", "Director"]
        cast_keys = ["Starring", "Cast"]
        release_date_keys = ["Release date", "Release dates"]
        runtime_keys = ["Running time", "Runtime"]

        for row in infobox.find_all("tr"):
            header = row.find("th")
            data = row.find("td")
            if header and data:
                header_text = header.text.strip()

                if any(key.lower() in header_text.lower() for key in genre_keys):
                    details["genre"] = ', '.join([li.get_text() for li in data.find_all(["li", "a"])]) or safe_get_text(data)
                    print(f"✅ Genre found.")

                elif any(key.lower() in header_text.lower() for key in director_keys):
                    details["director"] = ', '.join([li.get_text() for li in data.find_all(["li", "a"])]) or safe_get_text(data)
                    print(f"✅ Director found.")

                elif any(key.lower() in header_text.lower() for key in cast_keys):
                    details["cast"] = ', '.join([li.get_text() for li in data.find_all(["li", "a"])]) or safe_get_text(data)
                    print(f"✅ Cast found.")

                elif any(key.lower() in header_text.lower() for key in release_date_keys):
                    details["release_date"] = safe_get_text(data)
                    print(f"✅ Release Date found.")

                elif any(key.lower() in header_text.lower() for key in runtime_keys):
                    details["runtime"] = safe_get_text(data)
                    print(f"✅ Runtime found.")

        plot_header = soup.find(id="Plot")
        if plot_header:
            print("🔎 Searching for Plot section...")
            plot_paragraph = plot_header.find_next("p")
            if plot_paragraph:
                details["plot"] = plot_paragraph.get_text(strip=True)
                print(f"✅ Plot found.")
        else:
            print("❌ Plot section not found.")

        return details

    except Exception as e:
        print(f"❌ Error fetching Wikipedia data for {movie_name}: {e}")
        return None

# 📥 Fetch from IMDb
def get_movie_details_from_imdb(movie_name):
    try:
        print(f"\n🔍 Searching IMDb for: {movie_name}")
        search_url = f"https://www.imdb.com/find?q={movie_name.replace(' ', '+')}&s=tt"
        response = requests.get(search_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        result = soup.find("td", class_="result_text")
        if not result:
            print(f"❌ IMDb search failed for {movie_name}")
            return None

        relative_link = result.find("a")["href"]
        movie_url = f"https://www.imdb.com{relative_link}"
        print(f"🌐 Fetching IMDb movie page...")
        movie_response = requests.get(movie_url)
        movie_soup = BeautifulSoup(movie_response.text, 'html.parser')

        details = {
            "genre": "Not found",
            "director": "Not found",
            "cast": "Not found",
            "release_date": "Not found",
            "runtime": "Not found",
            "rating": "Not found"
        }

        genre_section = movie_soup.find("div", {"data-testid": "genres"})
        if genre_section:
            genre_links = genre_section.find_all("a")
            details["genre"] = ', '.join(link.get_text(strip=True) for link in genre_links)
            print(f"✅ IMDb Genre found.")

        director_section = movie_soup.find("li", {"data-testid": "title-pc-principal-credit"})
        if director_section:
            directors = director_section.find_all("a")
            details["director"] = ', '.join(d.get_text(strip=True) for d in directors)
            print(f"✅ IMDb Director found.")

        cast_section = movie_soup.find_all("a", {"data-testid": re.compile("title-cast-item__actor")})
        if cast_section:
            details["cast"] = ', '.join(actor.get_text(strip=True) for actor in cast_section)
            print(f"✅ IMDb Cast found.")

        release_date_section = movie_soup.find("li", {"data-testid": "title-details-releasedate"})
        if release_date_section:
            date_tag = release_date_section.find("a")
            if date_tag:
                details["release_date"] = date_tag.get_text(strip=True)
                print(f"✅ IMDb Release Date found.")

        runtime_section = movie_soup.find("li", {"data-testid": "title-techspec_runtime"})
        if runtime_section:
            details["runtime"] = safe_get_text(runtime_section)
            print(f"✅ IMDb Runtime found.")

        rating_section = movie_soup.find("span", {"data-testid": "hero-rating-bar__aggregate-rating__score"})
        if rating_section:
            details["rating"] = rating_section.get_text(strip=True)
            print(f"✅ IMDb Rating found.")

        return details

    except Exception as e:
        print(f"❌ Error fetching IMDb details for {movie_name}: {e}")
        return None

# 🔎 Infer Genre from Plot (if needed)
def infer_genre_from_plot(plot):
    print(f"🎯 Inferring genre from plot...")
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
    result = ", ".join(found) if found else "Not found"
    print(f"✅ Genre inference complete.")
    return result

# 🎬 Collect Information
def get_movie_info(movie_name):
    print(f"\n📄 Gathering information for: {movie_name}")
    wiki_data = fetch_wiki_data(movie_name)
    if not wiki_data:
        print(f"🔄 Retrying Wikipedia with (film) suffix...")
        wiki_data = fetch_wiki_data(f"{movie_name} (film)")

    imdb_data = get_movie_details_from_imdb(movie_name)

    details = {
        "Name": movie_name,
        "Genre": "Not found",
        "Plot": "Not found",
        "Director": "Not found",
        "Cast": "Not found",
        "Release Date": "Not found",
        "Runtime": "Not found",
        "Rating": "Not found"
    }

    if wiki_data:
        details.update({
            "Genre": wiki_data.get("genre", "Not found"),
            "Plot": wiki_data.get("plot", "Not found"),
            "Director": wiki_data.get("director", "Not found"),
            "Cast": wiki_data.get("cast", "Not found"),
            "Release Date": wiki_data.get("release_date", "Not found"),
            "Runtime": wiki_data.get("runtime", "Not found")
        })

    if imdb_data:
        for key in ["Genre", "Director", "Cast", "Release Date", "Runtime", "Rating"]:
            if details[key] == "Not found" and imdb_data.get(key.lower(), "Not found") != "Not found":
                details[key] = imdb_data[key.lower()]

    if details["Genre"] == "Not found" and details["Plot"] != "Not found":
        details["Genre"] = infer_genre_from_plot(details["Plot"])

    if details["Genre"] == "Not found":
        details["Genre"] = "Genre not available"

    print(f"✅ Information collection complete for {movie_name}\n")
    return details

# 🧾 Movie List
movie_names = [
    "Inception",
    "The Godfather",
    "Interstellar",
    "Forrest Gump",
    "Avengers: Endgame"
]

# 📈 Save Data to Excel
movie_data = []
for name in movie_names:
    info = get_movie_info(name)
    movie_data.append(info)

file_path = r"C:\\Project\\movie_summary.xlsx"

if os.path.exists(file_path):
    print("📂 Existing Excel file found, updating...")
    existing_df = pd.read_excel(file_path)

    if 'Name' not in existing_df.columns:
        existing_df['Name'] = None

    updated_df = existing_df.copy()

    for entry in movie_data:
        if entry['Name'] in existing_df['Name'].tolist():
            updated_df.loc[updated_df['Name'] == entry['Name'], ['Genre', 'Plot', 'Director', 'Cast', 'Release Date', 'Runtime', 'Rating']] = entry['Genre'], entry['Plot'], entry['Director'], entry['Cast'], entry['Release Date'], entry['Runtime'], entry['Rating']
        else:
            updated_df = pd.concat([updated_df, pd.DataFrame([entry])], ignore_index=True)

    try:
        updated_df.to_excel(file_path, index=False)
        print(f"✅ Excel file updated at {file_path}")
    except PermissionError:
        print("❌ Permission denied: Please close the Excel file before running the script again.")
else:
    print("📂 No existing Excel file found, creating new...")
    new_df = pd.DataFrame(movie_data)
    try:
        new_df.to_excel(file_path, index=False)
        print(f"✅ New Excel file created at {file_path}")
    except PermissionError:
        print("❌ Permission denied: Please close the Excel file before running the script again.")
