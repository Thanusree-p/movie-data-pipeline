# Movie Data Pipeline

## About the Project

The goal of this project is to build a simple data pipeline that collects movie information, cleans it, adds extra details, and stores everything in a database for analysis.

For this project, I used the MovieLens dataset, which contains information about movies and the ratings given by users. I also integrated the OMDb API to retrieve additional details about movies, such as their director, plot, box office collection, and IMDb ID.

I used Python to process the data and SQLite to store it. Once the data was loaded into the database, I wrote SQL queries to answer questions about movie ratings, genres, directors, and release years.

## Technologies Used

- **Python:** Used to extract, clean, transform, and load the data.
- **Pandas:** Used to read CSV files and process movie and rating records.
- **SQLite:** Used to store the data in a relational database.
- **SQL:** Used to organize the data and answer analytical questions.
- **OMDb API:** Used to retrieve additional information about movies.
- **Requests:** Used to communicate with the OMDb API.
- **python-dotenv:** Used to read the API key securely from a `.env` file.

## Dataset

I used the MovieLens small dataset, which contains two main CSV files:

- `movies.csv` contains movie IDs, titles, and genres.
- `ratings.csv` contains user IDs, movie IDs, ratings, and timestamps.

The OMDb API provides additional information that is not included in the original MovieLens files.

## How the Pipeline Works

The pipeline follows four main stages.

### 1. Extracting the Data

First, the pipeline reads `movies.csv` and `ratings.csv` using Pandas. These files provide the original movie information and user ratings.

### 2. Cleaning and Transforming the Data

The raw data may contain missing values, duplicate records, or values that need to be converted into the correct data types. I cleaned the data, converted IDs and ratings into appropriate numeric types, extracted release years from movie titles, and separated individual genres.

I also removed invalid ratings and ratings that refer to movies not present in the cleaned movie dataset.

### 3. Enriching Movie Information

MovieLens does not provide every detail needed for this project, so I integrated the OMDb API.

For example, the API can provide a movie's director, plot, box office collection, and IMDb ID. I implemented caching so that previously processed movies do not need to be requested again unnecessarily.

To manage API usage, the pipeline processes a limited number of new movie lookups during each run. Therefore, additional movie details are populated gradually as more batches are processed.

### 4. Loading the Data into SQLite

After cleaning the data, the pipeline stores it in the SQLite database named `movies.db`.

I organized the database into separate tables for movies, ratings, genres, and the relationship between movies and genres. This avoids storing repeated genre information for every movie.

I also used primary keys, foreign keys, and conflict-handling SQL statements to maintain relationships and prevent duplicate records when the pipeline is run again.

## Database Design

The database contains the following tables:

- **movies:** Stores movie titles, release years, and available OMDb details.
- **ratings:** Stores user ratings and their timestamps.
- **genres:** Stores unique genre names.
- **movie_genres:** Connects movies with their associated genres.
- **omdb_cache:** Stores previously processed OMDb responses to reduce repeated API calls.

The tables are connected using movie IDs and genre IDs, which helps maintain data consistency.

## Project Setup

Follow these steps to run the project on your computer.

### Step 1: Install the Required Libraries

Open the terminal in the project folder and run:

```bash
pip install pandas requests python-dotenv
```

### Step 2: Configure the OMDb API

Create a `.env` file in the project folder and add your API key:

```text
OMDB_API_KEY=your_api_key_here
OMDB_ENRICH_LIMIT=100
```

Replace `your_api_key_here` with your own API key. Keep this file private and do not upload it to GitHub.

The enrichment limit controls how many new OMDb lookups are attempted in one run.

### Step 3: Create the Database

Run the following command when setting up a fresh database:

```bash
python create_database.py
```

This creates the database tables using the definitions in `schema.sql`.

**Note:** Run this during initial setup only. Do not delete or recreate an existing database that already contains your loaded data.

### Step 4: Run the ETL Pipeline

Run:

```bash
python etl.py
```

The script reads the CSV files, cleans the data, attempts OMDb enrichment, and loads the full MovieLens dataset into SQLite.

### Step 5: Verify the Data

To check the records stored in the database, run:

```bash
python verify_database.py
```

### Step 6: Run the SQL Queries

To execute the analytical queries, run:

```bash
python run_queries.py
```

The results will be displayed in the terminal.

## SQL Analysis

I wrote SQL queries to answer the following questions:

1. Which movie has the highest average rating?
2. What are the top 5 movie genres with the highest average rating?
3. Who is the director with the most movies in the dataset?
4. What is the average rating of movies released each year?

The director analysis depends on the director information successfully retrieved from OMDb. Since enrichment is currently incomplete, the director result may not represent the entire dataset.

## Results So Far

After running the pipeline, the SQLite database contains:

- **9,742 movies**
- **100,836 ratings**
- **19 genres**
- **22,050 movie-genre relationships**

The pipeline has also successfully retrieved and cached OMDb responses in batches.

The MovieLens dataset is fully loaded, but OMDb enrichment is still partial. This means director, plot, box office, and IMDb information is not yet available for every movie.

I tested the pipeline by running it more than once. The main MovieLens table counts remained unchanged, confirming that repeated runs did not create duplicate movie or rating records.

## Challenges and Improvements

One challenge was handling relationships between database tables. For example, ratings must refer to movies that already exist in the database. I addressed this by loading the movie records before storing related OMDb cache entries.

Another consideration was the OMDb API request limit. To manage this, I added a cache and limited the number of new requests per run.

As a future improvement, I would complete the remaining OMDb enrichment as API limits permit, add more automated data-quality checks, and explore deploying the pipeline using Azure data services and Snowflake.

## Conclusion

Through this project, I gained practical experience in building a data pipeline from raw CSV files to a relational database. I worked with Python and Pandas for data cleaning, integrated an external API to enrich movie information, designed related database tables, and used SQL to answer analytical questions.

The project helped me understand how extraction, transformation, enrichment, and loading work together in a basic data engineering workflow.
