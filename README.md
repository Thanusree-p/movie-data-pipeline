# Movie Data Pipeline

## About the Project

The goal of this project is to build a simple data pipeline that collects movie information, cleans it, enriches it with additional details, and stores everything in a relational database for analysis.

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

MovieLens does not provide all the details required for this project, so I integrated the OMDb API to retrieve additional movie information, including director, plot, box office collection, and IMDb ID.

I implemented an OMDb cache table to store previously retrieved responses and reduce unnecessary API requests. Successfully enriched movies are skipped during subsequent runs, while unsuccessful lookups can be retried.

The pipeline also supports batch processing through an enrichment limit configured in the `.env` file. Due to OMDb API request limits, enrichment is currently available for only a subset of movies. Missing metadata does not prevent the remaining MovieLens data from being loaded into the database.

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

### Step 1: Clone the Repository

```bash
git clone https://github.com/Thanusree-p/movie-data-pipeline.git
cd movie-data-pipeline
```

### Step 2: Install the Required Libraries

Open the terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

### Step 3: Configure the OMDb API

Create a `.env` file in the project folder and add your API key:

```text
OMDB_API_KEY=your_api_key_here
OMDB_ENRICH_LIMIT=100
```

Replace `your_api_key_here` with your own API key. Keep this file private and do not upload it to GitHub.

The enrichment limit controls how many new movie lookups are attempted in one run.

### Step 4: Create the Database

Run the following command when setting up a fresh database:

```bash
python create_database.py
```

This creates the database tables using the definitions in `schema.sql`.

**Note:** Run this during initial setup only. Do not delete or recreate an existing database that already contains your loaded data.

### Step 5: Run the ETL Pipeline

Run:

```bash
python etl.py
```

The script reads the CSV files, cleans the data, attempts OMDb enrichment, and loads the MovieLens dataset into SQLite.

### Step 6: Verify the Data

To check the records stored in the database, run:

```bash
python verify_database.py
```

### Step 7: Run the SQL Queries

To execute the analytical queries, run:

```bash
python run_queries.py
```

The results will be displayed in the terminal.

## SQL Analysis

I wrote SQL queries to answer the following questions:

1. Which movie or movies have the highest average rating?
2. What are the top 5 movie genres with the highest average rating?
3. Which director has the most movies?
4. What is the average rating of movies released each year?

The queries use SQL aggregation, joins, grouping, and sorting to analyze the data.

**Note:** The director analysis depends on the director information successfully retrieved from OMDb. Since enrichment is currently incomplete, the director result represents only the available enriched records and may not represent the entire MovieLens dataset.

## Results So Far

After running the pipeline, the SQLite database contains:

- **9,742 movies**
- **100,836 ratings**
- **19 genres**
- **22,050 movie-genre relationships**

The OMDb cache contains 905 processed records:

- **646 successful metadata retrievals**
- **259 unsuccessful lookups**

The MovieLens dataset is fully loaded, while OMDb enrichment is partial because of API request limits. Movies without retrieved metadata remain available in the database with their original MovieLens information.

The analytical SQL queries execute successfully:

- **Highest average rating:** 296 movies are tied with an average rating of 5.0.
- **Top 5 genres:** Documentary, Film-Noir, War, Animation, and Drama.
- **Director with most movies:** Alfred Hitchcock, with 9 movies among the currently enriched records.
- **Average rating by release year:** Results are available for 106 release years.

I also tested repeated pipeline execution and verified that the main MovieLens movie and rating counts remained unchanged, demonstrating that repeated runs do not create duplicate movie or rating records.

## Challenges and Improvements

One challenge was handling relationships between database tables. For example, ratings must refer to movies that already exist in the database. I addressed this by loading the movie records before storing related OMDb cache entries.

Another challenge was handling movie title mismatches while retrieving information from the OMDb API. I used title and release-year information to improve movie matching and reduce incorrect metadata associations.

The OMDb API request limit was another consideration. To manage this, I implemented caching and limited the number of new requests per run. The pipeline also handles missing metadata without interrupting the loading of the main dataset.

As a future improvement, I would complete the remaining OMDb enrichment as API limits permit, add more automated data-quality checks, and explore deploying the pipeline using Azure data services and Snowflake.

## Conclusion

Through this project, I gained practical experience in building a data pipeline from raw CSV files to a relational database. I worked with Python and Pandas for data cleaning, integrated an external API to enrich movie information, designed related database tables, and used SQL to answer analytical questions.

The project helped me understand how extraction, transformation, enrichment, and loading work together in a basic data engineering workflow.