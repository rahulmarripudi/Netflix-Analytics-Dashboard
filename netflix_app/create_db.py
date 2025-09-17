import sqlite3
import pandas as pd

# Load Excel
df = pd.read_excel("netflix_titles.xlsx")

# Connect DB
conn = sqlite3.connect("netflix.db")
cursor = conn.cursor()

# Create netflix table
cursor.execute('''
CREATE TABLE IF NOT EXISTS netflix(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    show_id TEXT,
    type TEXT,
    title TEXT,
    director TEXT,
    cast TEXT,
    country TEXT,
    date_added TEXT,
    release_year INTEGER,
    rating TEXT,
    duration TEXT,
    listed_in TEXT,
    description TEXT
)
''')

# Insert data
for _, row in df.iterrows():
    cursor.execute('''
        INSERT INTO netflix (
            show_id, type, title, director, cast, country, 
            date_added, release_year, rating, duration, listed_in, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        row.get("show_id"),
        row.get("type"),
        row.get("title"),
        row.get("director"),
        row.get("cast"),
        row.get("country"),
        row.get("date_added"),
        row.get("release_year"),
        row.get("rating"),
        row.get("duration"),
        row.get("listed_in"),
        row.get("description"),
    ))

# Commit + Close
conn.commit()
conn.close()

print("Netflix database created and populated successfully")
