
import pandas as pd

movies = pd.read_csv("data/movies.csv")
ratings = pd.read_csv("data/ratings.csv")

print("Movies dataset:")
print(movies.head())
print("Total movies:", len(movies))

print("\nRatings dataset:")
print(ratings.head())
print("Total ratings:", len(ratings))
