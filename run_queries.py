
import sqlite3

DATABASE_FILE = "movies.db"
QUERIES_FILE = "queries.sql"

with open(QUERIES_FILE, "r", encoding="utf-8") as file:
    sql_content = file.read()

# Split the file into individual SQL statements.
queries = [
    query.strip()
    for query in sql_content.split(";")
    if query.strip()
]

conn = sqlite3.connect(DATABASE_FILE)

try:
    for index, query in enumerate(queries, start=1):
        print(f"\n{'=' * 50}")
        print(f"QUERY {index}")
        print("=" * 50)

        cursor = conn.execute(query)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        print(" | ".join(columns))

        for row in rows:
            print(" | ".join(
                str(value) if value is not None else "NULL"
                for value in row
            ))

        print(f"\nRows returned: {len(rows)}")

finally:
    conn.close()
