
import sqlite3

conn = sqlite3.connect("movies.db")

print("Movies in database:")
for row in conn.execute(
    "SELECT movie_id, title, director, imdb_id FROM movies"
):
    print(row)

print("\nTotal movies:", conn.execute(
    "SELECT COUNT(*) FROM movies"
).fetchone()[0])

print("Total ratings:", conn.execute(
    "SELECT COUNT(*) FROM ratings"
).fetchone()[0])

print("Total genres:", conn.execute(
    "SELECT COUNT(*) FROM genres"
).fetchone()[0])

conn.close()
