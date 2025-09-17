from flask import Flask, jsonify, request
import pandas as pd
from sqlalchemy import create_engine
import os

app = Flask(__name__)

# ---------- File Handling ----------
EXCEL_FILE = "netflix_titles.xlsx"  # optional
CSV_FILE = "netflix_titles.csv"     # main dataset



def read_excel_data():
    """Read Netflix dataset from CSV (preferred) or Excel if available."""
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
    elif os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
    else:
        raise FileNotFoundError("Neither netflix_titles.csv nor netflix_titles.xlsx found!")

    # normalize column names
    df.columns = df.columns.str.strip().str.lower()
    return df



def read_sql_data():
    """Read from SQLite DB (auto-create if not exists)."""
    engine = create_engine("sqlite:///netflix.db")

    if not engine.dialect.has_table(engine.connect(), "netflix"):
        print("Creating 'netflix' table from CSV...")
        df = read_excel_data()
        df.to_sql("netflix", con=engine, index=False, if_exists="replace")

    df = pd.read_sql("SELECT * FROM netflix", con=engine)
    return df


# ---------- API Endpoints ----------
@app.route("/")
def home():
    return {
        "endpoints": [
            "/api/xlsx",
            "/api/sql",
            "/api/netflix?source=xlsx&type=Movie&country=India",
            "/api/netflix?source=sql&rating=PG-13&release_year=2020&limit=5&offset=0",
        ],
        "message": "Welcome to the Netflix Titles API!",
    }


@app.route("/api/xlsx", methods=["GET"])
def get_excel_data():
    try:
        df = read_excel_data()
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sql", methods=["GET"])
def get_sql_data():
    try:
        df = read_sql_data()
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/netflix", methods=["GET"])
def get_netflix_data():
    source = request.args.get("source", "xlsx")

    if source == "xlsx":
        df = read_excel_data()
    else:
        df = read_sql_data()

    # Optional filters
    title = request.args.get("title")
    type_ = request.args.get("type")  # Movie / TV Show
    country = request.args.get("country")
    rating = request.args.get("rating")
    release_year = request.args.get("release_year", type=int)
    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", type=int, default=0)

    # Apply filters (case-insensitive where needed)
    if title:
        df = df[df["title"].str.contains(title, case=False, na=False)]
    if type_:
        df = df[df["type"].str.lower() == type_.lower()]
    if country:
        df = df[df["country"].str.contains(country, case=False, na=False)]
    if rating:
        df = df[df["rating"] == rating]
    if release_year:
        df = df[df["release_year"] == release_year]

    # Pagination
    if limit is not None:
        df = df.iloc[offset : offset + limit]

    return jsonify(df.to_dict(orient="records"))


# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True, port=5001)
