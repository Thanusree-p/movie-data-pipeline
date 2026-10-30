
import os
import re
import sqlite3
import time
import requests
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("OMDB_API_KEY")

MOVIES_FILE = "data/movies.csv"
RATINGS_FILE = "data/ratings.csv"
DATABASE_FILE = "movies.db"

# Maximum NEW OMDb requests per run.
OMDB_ENRICH_LIMIT = int(os.getenv("OMDB_ENRICH_LIMIT", "100"))


# -------------------- EXTRACT --------------------

def extract_data():
    movies = pd.read_csv(MOVIES_FILE)
    ratings = pd.read_csv(RATINGS_FILE)

    print(f"Movies extracted: {len(movies)}")
    print(f"Ratings extracted: {len(ratings)}")

    return movies, ratings


# -------------------- TRANSFORM --------------------

def clean_movies(movies):
    movies = movies.copy()

    movies = movies.dropna(subset=["movieId", "title"])

    movies["movieId"] = pd.to_numeric(
        movies["movieId"], errors="coerce"
    )

    movies = movies.dropna(subset=["movieId"])

    movies = movies[
        (movies["movieId"] > 0)
        & (movies["movieId"] % 1 == 0)
    ].copy()

    movies["movieId"] = movies["movieId"].astype("int64")
    movies["title"] = movies["title"].astype("string").str.strip()
    movies["genres"] = movies["genres"].astype("string").str.strip()

    movies = movies[movies["title"] != ""]

    movies = movies.drop_duplicates(
        subset=["movieId"], keep="first"
    )

    movies["release_year"] = pd.to_numeric(
        movies["title"].str.extract(r"\((\d{4})\)\s*$")[0],
        errors="coerce"
    ).astype("Int64")

    movies["genres_list"] = movies["genres"].apply(
        lambda value: [
            genre.strip()
            for genre in value.split("|")
            if genre.strip()
            and genre.strip() != "(no genres listed)"
        ]
        if pd.notna(value) else []
    )

    return movies.reset_index(drop=True)


def clean_ratings(ratings):
    ratings = ratings.copy()

    for column in ["userId", "movieId", "rating", "timestamp"]:
        ratings[column] = pd.to_numeric(
            ratings[column], errors="coerce"
        )

    ratings = ratings.dropna(
        subset=["userId", "movieId", "rating", "timestamp"]
    )

    ratings = ratings[
        (ratings["userId"] > 0)
        & (ratings["movieId"] > 0)
        & (ratings["rating"].between(0.5, 5.0))
        & (ratings["userId"] % 1 == 0)
        & (ratings["movieId"] % 1 == 0)
        & (ratings["timestamp"] % 1 == 0)
        & (ratings["timestamp"] >= 0)
    ].copy()

    ratings["userId"] = ratings["userId"].astype("int64")
    ratings["movieId"] = ratings["movieId"].astype("int64")
    ratings["timestamp"] = ratings["timestamp"].astype("int64")

    ratings = ratings.drop_duplicates(
        subset=["userId", "movieId"], keep="first"
    )

    ratings["rating_datetime"] = pd.to_datetime(
        ratings["timestamp"],
        unit="s",
        utc=True,
        errors="coerce"
    )

    ratings = ratings.dropna(subset=["rating_datetime"])

    return ratings.reset_index(drop=True)


def transform_data(movies, ratings):
    movies_clean = clean_movies(movies)
    ratings_clean = clean_ratings(ratings)

    valid_movie_ids = set(movies_clean["movieId"])

    ratings_clean = ratings_clean[
        ratings_clean["movieId"].isin(valid_movie_ids)
    ].copy()

    print("\nTransformation completed.")
    print(f"Clean movies: {len(movies_clean)}")
    print(f"Clean ratings: {len(ratings_clean)}")

    return movies_clean, ratings_clean


# -------------------- OMDb ENRICHMENT --------------------

def create_cache_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS omdb_cache (
            movie_id INTEGER PRIMARY KEY,
            director TEXT,
            plot TEXT,
            box_office TEXT,
            imdb_id TEXT,
            response_found INTEGER NOT NULL,
            FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
        )
    """)

    conn.commit()


def normalize_title(title):
    """Normalize titles for comparison."""
    return re.sub(r"[^a-z0-9]", "", title.lower())


def fetch_movie_details(title):

    if not API_KEY:
        raise ValueError(
            "OMDB_API_KEY is missing. Check your .env file."
        )

    # Extract the final release year
    match = re.search(r"\((\d{4})\)\s*$", title)

    year = match.group(1) if match else None

    # Remove the final year from the title
    search_title = re.sub(
        r"\s*\(\d{4}\)\s*$", "", title
    ).strip()

    # Remove alternate-title annotations
    search_title = re.sub(
        r"\s*\(a\.k\.a\..*?\)",
        "",
        search_title,
        flags=re.IGNORECASE
    ).strip()

    params = {
        "apikey": API_KEY,
        "t": search_title,
        "type": "movie"
    }

    if year:
        params["y"] = year

    try:
        response = requests.get(
            "https://www.omdbapi.com/",
            params=params,
            timeout=15
        )

        response.raise_for_status()
        data = response.json()

        # If exact-title search fails, try fallback search
        if data.get("Response") != "True" and "Error" in data:

            error_message = data.get("Error", "").lower()

            # Do not continue if API limit or authentication fails
            if any(word in error_message for word in [
                "limit", "invalid api key", "unauthorized"
            ]):
                return None

            fallback_params = {
                "apikey": API_KEY,
                "s": search_title,
                "type": "movie"
            }

            if year:
                fallback_params["y"] = year

            fallback_response = requests.get(
                "https://www.omdbapi.com/",
                params=fallback_params,
                timeout=15
            )

            fallback_response.raise_for_status()
            fallback_data = fallback_response.json()

            fallback_error = fallback_data.get("Error", "").lower()

            if any(word in fallback_error for word in [
                "limit", "invalid api key", "unauthorized"
            ]):
                return None

            # Verify fallback search results
            if fallback_data.get("Response") == "True":

                matching_result = None

                for result in fallback_data.get("Search", []):

                    result_title = result.get("Title", "").strip()
                    result_year = result.get("Year", "").strip()

                    title_matches = (
                        normalize_title(result_title)
                        == normalize_title(search_title)
                    )

                    year_matches = (
                        not year or result_year == year
                    )

                    if title_matches and year_matches:
                        matching_result = result
                        break

                if matching_result:

                    imdb_id = matching_result.get("imdbID")

                    if imdb_id:

                        details_response = requests.get(
                            "https://www.omdbapi.com/",
                            params={
                                "apikey": API_KEY,
                                "i": imdb_id
                            },
                            timeout=15
                        )

                        details_response.raise_for_status()
                        data = details_response.json()

                    else:
                        data = {
                            "Response": "False",
                            "Error": "Matching movie has no IMDb ID"
                        }

                else:
                    data = {
                        "Response": "False",
                        "Error": "No matching movie title and year found"
                    }

            else:
                data = fallback_data

    except (requests.RequestException, ValueError) as error:
        print(f"Temporary OMDb error for {title}: {error}")
        return None

    if data.get("Response") == "True":
        return {
            "director": data.get("Director"),
            "plot": data.get("Plot"),
            "box_office": data.get("BoxOffice"),
            "imdb_id": data.get("imdbID"),
            "response_found": 1
        }

    error_message = data.get("Error", "Unknown OMDb error")

    print(
        f"OMDb did not return details for {title}: {error_message}"
    )

    # Do not cache API-limit or authentication errors
    if any(word in error_message.lower() for word in [
        "limit", "invalid api key", "unauthorized"
    ]):
        return None

    return {
        "director": None,
        "plot": None,
        "box_office": None,
        "imdb_id": None,
        "response_found": 0
    }


def enrich_uncached_movies(conn, movies, limit):

    cached_ids = {
        row[0]
        for row in conn.execute(
            """
            SELECT movie_id
            FROM omdb_cache
            WHERE response_found = 1
            """
        ).fetchall()
    }

    pending_movies = movies[
        ~movies["movieId"].isin(cached_ids)
    ]

    batch = pending_movies.head(max(0, limit))

    print(f"\nMovies needing OMDb lookup: {len(pending_movies)}")
    print(f"New OMDb requests planned this run: {len(batch)}")

    for position, (_, movie) in enumerate(
        batch.iterrows(), start=1
    ):

        movie_id = int(movie["movieId"])

        details = fetch_movie_details(str(movie["title"]))

        if details is not None:

            conn.execute(
                """
                INSERT OR REPLACE INTO omdb_cache
                (movie_id, director, plot, box_office,
                 imdb_id, response_found)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    movie_id,
                    details["director"],
                    details["plot"],
                    details["box_office"],
                    details["imdb_id"],
                    details["response_found"]
                )
            )

            conn.commit()

        print(
            f"OMDb processed {position}/{len(batch)}: "
            f"{movie['title']}"
        )

        if position < len(batch):
            time.sleep(0.25)

    print("OMDb enrichment batch completed.")


# -------------------- LOAD --------------------

def load_all_data(conn, movies, ratings):

    conn.execute("PRAGMA foreign_keys = ON")

    movie_rows = []
    genre_links = []

    for movie in movies.itertuples(index=False):

        movie_id = int(movie.movieId)

        cached = conn.execute(
            """
            SELECT director, plot, box_office, imdb_id
            FROM omdb_cache
            WHERE movie_id = ?
            """,
            (movie_id,)
        ).fetchone()

        director, plot, box_office, imdb_id = (
            cached if cached else (None, None, None, None)
        )

        release_year = (
            int(movie.release_year)
            if pd.notna(movie.release_year)
            else None
        )

        movie_rows.append((
            movie_id,
            str(movie.title),
            release_year,
            director,
            plot,
            box_office,
            imdb_id
        ))

        for genre in movie.genres_list:

            conn.execute(
                """
                INSERT OR IGNORE INTO genres (genre_name)
                VALUES (?)
                """,
                (genre,)
            )

            genre_id = conn.execute(
                "SELECT genre_id FROM genres WHERE genre_name = ?",
                (genre,)
            ).fetchone()[0]

            genre_links.append((movie_id, genre_id))

    conn.executemany(
        """
        INSERT INTO movies
        (movie_id, title, release_year, director, plot,
         box_office, imdb_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(movie_id) DO UPDATE SET
            title = excluded.title,
            release_year = excluded.release_year,
            director = COALESCE(excluded.director, movies.director),
            plot = COALESCE(excluded.plot, movies.plot),
            box_office = COALESCE(
                excluded.box_office, movies.box_office
            ),
            imdb_id = COALESCE(excluded.imdb_id, movies.imdb_id)
        """,
        movie_rows
    )

    conn.executemany(
        """
        INSERT OR IGNORE INTO movie_genres (movie_id, genre_id)
        VALUES (?, ?)
        """,
        genre_links
    )

    conn.executemany(
        """
        INSERT INTO ratings
        (user_id, movie_id, rating, rating_timestamp)
        VALUES (?, ?, ?, ?)

        ON CONFLICT(user_id, movie_id) DO UPDATE SET
            rating = excluded.rating,
            rating_timestamp = excluded.rating_timestamp
        """,
        (
            (
                int(row.userId),
                int(row.movieId),
                float(row.rating),
                int(row.timestamp)
            )
            for row in ratings.itertuples(index=False)
        )
    )

    conn.commit()

    print("\nFull dataset loaded successfully!")

    print(
        "Movies in database:",
        conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    )

    print(
        "Ratings in database:",
        conn.execute("SELECT COUNT(*) FROM ratings").fetchone()[0]
    )

    print(
        "Genres in database:",
        conn.execute("SELECT COUNT(*) FROM genres").fetchone()[0]
    )

    print(
        "Movie-genre links:",
        conn.execute(
            "SELECT COUNT(*) FROM movie_genres"
        ).fetchone()[0]
    )

    print(
        "Cached OMDb responses:",
        conn.execute("SELECT COUNT(*) FROM omdb_cache").fetchone()[0]
    )


# -------------------- MAIN PIPELINE --------------------

def run_etl():

    movies, ratings = extract_data()

    movies_clean, ratings_clean = transform_data(
        movies, ratings
    )

    conn = sqlite3.connect(DATABASE_FILE)

    try:
        conn.execute("PRAGMA foreign_keys = ON")

        # Step 1: Create the cache table
        create_cache_table(conn)

        # Step 2: Load movies and ratings first
        load_all_data(conn, movies_clean, ratings_clean)

        # Step 3: Enrich movies using OMDb
        enrich_uncached_movies(
            conn,
            movies_clean,
            OMDB_ENRICH_LIMIT
        )

        # Step 4: Apply retrieved OMDb details
        load_all_data(conn, movies_clean, ratings_clean)

        print("\nETL pipeline completed successfully.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    run_etl()
