
import sqlite3

# Connect to the database.
# If movies.db doesn't exist, SQLite creates it.
conn = sqlite3.connect("movies.db")

# Read the SQL statements from schema.sql
with open("schema.sql", "r", encoding="utf-8") as file:
    schema = file.read()

# Create the tables
conn.executescript(schema)

conn.close()

print("Database and tables created successfully!")
