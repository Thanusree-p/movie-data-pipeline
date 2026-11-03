

-- Query 1: Top 10 highest-rated movies
-- Consider only movies with at least 20 ratings

SELECT
    m.movie_id,
    m.title,
    ROUND(AVG(r.rating), 2) AS average_rating,
    COUNT(r.rating) AS total_ratings
FROM movies m
JOIN ratings r
    ON m.movie_id = r.movie_id
GROUP BY m.movie_id, m.title
HAVING COUNT(r.rating) >= 20
ORDER BY average_rating DESC, total_ratings DESC
LIMIT 10;



-- 2. Find the top 5 genres by average movie rating.
-- Calculate each movie's average first, then average those
-- movie-level averages within each genre.
WITH movie_averages AS (
    SELECT
        movie_id,
        AVG(rating) AS average_rating
    FROM ratings
    GROUP BY movie_id
)
SELECT
    g.genre_name,
    ROUND(AVG(ma.average_rating), 2) AS average_rating,
    COUNT(*) AS number_of_movies
FROM genres AS g
JOIN movie_genres AS mg
    ON g.genre_id = mg.genre_id
JOIN movie_averages AS ma
    ON mg.movie_id = ma.movie_id
GROUP BY g.genre_id, g.genre_name
ORDER BY average_rating DESC, number_of_movies DESC
LIMIT 5;



-- 3. Find the director with the most movies among
-- movies with available OMDb director information.
SELECT
    director,
    COUNT(*) AS total_movies
FROM movies
WHERE director IS NOT NULL
  AND TRIM(director) <> ''
  AND UPPER(TRIM(director)) <> 'N/A'
GROUP BY director
ORDER BY total_movies DESC, director ASC
LIMIT 1;



-- 4. Calculate average rating by release year.
SELECT
    m.release_year,
    ROUND(AVG(r.rating), 2) AS average_rating,
    COUNT(r.rating) AS total_ratings
FROM movies AS m
JOIN ratings AS r
    ON m.movie_id = r.movie_id
WHERE m.release_year IS NOT NULL
GROUP BY m.release_year
ORDER BY m.release_year;
