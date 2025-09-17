import streamlit as st
import pandas as pd
import os
import plotly.express as px
import sqlite3
import hashlib
import numpy as np
import random
import math

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title="Netflix Dashboard",
    layout="wide",
    page_icon="🎬"
)

# ---------------------------
# Database Setup (SQLite for Users)
# ---------------------------
def create_usertable():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    conn.close()
    return True

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed))
    data = c.fetchone()
    conn.close()
    return data

create_usertable()

# ---------------------------
# Ensure default admin
# ---------------------------
def ensure_default_admin():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    if count == 0:
        default_user = "admin"
        default_pass = hashlib.sha256("admin123".encode()).hexdigest()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (default_user, default_pass))
            conn.commit()
            print("✅ Default admin created: admin / admin123")
        except sqlite3.IntegrityError:
            pass
    conn.close()

ensure_default_admin()

# ---------------------------
# CSS Styling
# ---------------------------
st.markdown("""
    <style>
        body {background-color: #121212; color: #f5f5f5;}
        .stApp {background-color: #121212;}
        h1, h2, h3 {color: #E50914 !important; font-weight: 700;}
        .nav-container {
            display: flex; justify-content: space-between;
            align-items: center; background-color: #1c1c1c;
            padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;
        }
        .nav-item {
            color: #f5f5f5; text-decoration: none; margin: 0 15px;
            font-weight: 500; cursor: pointer;
        }
        .nav-item:hover {color: #E50914;}
        .centered-form {
            max-width: 400px; margin: auto; padding: 30px;
            background: #1f1f1f; border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.6);
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# Load Data
# ---------------------------
@st.cache_data
def load_data():
    if os.path.exists("netflix_titles.csv"):
        df = pd.read_csv("netflix_titles.csv")
    elif os.path.exists("netflix_titles.xlsx"):
        df = pd.read_excel("netflix_titles.xlsx", engine="openpyxl")
    else:
        raise FileNotFoundError("No Netflix dataset found!")
    df.columns = df.columns.str.strip().str.lower()
    return df

df = load_data()

# ---------------------------
# Session State
# ---------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "Login"

# ---------------------------
# Navigation Bar
# ---------------------------
def navbar():
    st.markdown("""
        <div class="nav-container">
            <div>
                <span class="nav-item">🎬 Netflix Dashboard</span>
            </div>
            <div>
                <a class="nav-item" href="?page=Home">🏠 Home</a>
                <a class="nav-item" href="?page=Data">📂 Data</a>
                <a class="nav-item" href="?page=Visualizations">📊 Visualizations</a>
                <a class="nav-item" href="?page=Recommendations">🤖 Recommendations</a>
                <a class="nav-item" href="?page=Trends">📈 Trends</a>
                <a class="nav-item" href="?page=About">ℹ️ About</a>
                <a class="nav-item" href="?page=Logout">🚪 Logout</a>
            </div>
        </div>
    """, unsafe_allow_html=True)

    query_params = st.query_params
    if "page" in query_params:
        st.session_state.page = query_params["page"]

# ---------------------------
# Login Page
# ---------------------------
def login_page():
    st.title("🔑 Login")
    with st.form("login_form"):
        st.markdown('<div class="centered-form">', unsafe_allow_html=True)
        username = st.text_input("👤 Username")
        password = st.text_input("🔒 Password", type="password")
        login_btn = st.form_submit_button("Login")

        if login_btn:
            user = login_user(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.page = "Home"
                st.success("✅ Login successful! Redirecting...")
            else:
                st.error("❌ Invalid username or password")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("👉 Don’t have an account? [Sign Up](?page=Signup)")

# ---------------------------
# Signup Page
# ---------------------------
def signup_page():
    st.title("📝 Sign Up")
    with st.form("signup_form"):
        st.markdown('<div class="centered-form">', unsafe_allow_html=True)
        new_user = st.text_input("👤 Choose a Username")
        new_pass = st.text_input("🔒 Choose a Password", type="password")
        signup_btn = st.form_submit_button("Sign Up")

        if signup_btn:
            if new_user and new_pass:
                success = add_user(new_user, new_pass)
                if success:
                    st.success("🎉 Account created successfully! Please [Login](?page=Login).")
                else:
                    st.error("⚠️ Username already exists. Try another one.")
            else:
                st.warning("⚠️ Please fill in all fields.")
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Home Page
# ---------------------------
def home_page():
    st.markdown(
        "<h1 style='text-align: center; color: white;'>Netflix Analytics Dashboard</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: gray;'>Comprehensive insights into your content library</p>",
        unsafe_allow_html=True,
    )

    # --- KPIs ---
    movies = (df["type"] == "Movie").sum() if "type" in df else 0
    shows = (df["type"] == "TV Show").sum() if "type" in df else 0
    avg_duration = (
        df["duration"].str.extract("(\d+)").astype(float).mean()[0]
        if "duration" in df
        else 0
    )
    top_country = df["country"].mode()[0] if "country" in df else "Unknown"
    top_country_count = (
        df["country"].value_counts().iloc[0] if "country" in df else 0
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Movies", movies, "🎥 Active content")
    with c2:
        st.metric("TV Shows", shows, "📺 Series collection")
    with c3:
        st.metric("Avg Duration", f"{int(avg_duration)} min", "⏱ Movie average")
    with c4:
        st.metric("Top Country", top_country, f"{top_country_count} titles")

    st.markdown("---")

    # --- Charts ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Genre Distribution")
        if "listed_in" in df:
            genre_counts = (
                df["listed_in"].dropna().str.split(", ").explode().value_counts().head(6)
            )
            fig1 = px.pie(
                genre_counts,
                values=genre_counts.values,
                names=genre_counts.index,
                hole=0.3,
                color_discrete_sequence=px.colors.qualitative.Set1,
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("No genre data available.")

    with col2:
        st.subheader("Production by Country")
        if "country" in df:
            country_counts = df["country"].value_counts().head(6)
            fig2 = px.bar(
                country_counts,
                x=country_counts.index,
                y=country_counts.values,
                text=country_counts.values,
                color=country_counts.values,
                color_continuous_scale="Reds",
            )
            fig2.update_traces(textposition="outside")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No country data available.")

    st.markdown("---")

    # --- Top 10 Highest Rated Content ---
    if "rating" in df.columns:
        top10 = df.dropna(subset=["rating"]).head(10)
    else:
        df["fake_rating"] = np.random.uniform(7.5, 9.0, size=len(df))
        top10 = df.sort_values("fake_rating", ascending=False).head(10)

    st.subheader("⭐ Top 10 Highest Rated Content")
    cols = st.columns(5)

    for idx, row in enumerate(top10.itertuples(), start=1):
        col = cols[(idx - 1) % 5]
        with col:
            # Try to convert rating to float, else fallback to fake_rating
            rating_value = getattr(row, "rating", getattr(row, "fake_rating", 8.0))
            try:
                rating_value = float(rating_value)
            except (ValueError, TypeError):
                rating_value = getattr(row, "fake_rating", 8.0)

            st.markdown(
                f"""
                <div style="background:#1f1f1f; padding:15px; border-radius:10px; 
                            margin-bottom:10px; text-align:center;">
                    <h4 style="color:white; margin:8px 0;">#{idx} {row.title}</h4>
                    <p style="color:gray;">{row.type} • {getattr(row,'release_year','')}</p>
                    <p style="font-size:18px;">⭐ {round(rating_value,1)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


    st.markdown("---")

    # --- Random Pick of the Day ---
    st.subheader("🎲 Random Pick of the Day")
    random_row = df.sample(1).iloc[0]

    # Safely handle values
    year = random_row["release_year"] if "release_year" in df else ""
    country = random_row["country"] if "country" in df else "N/A"
    description = (
        random_row["description"]
        if "description" in df
        else "No description available."
    )
    director = random_row["director"] if "director" in df else "Unknown"
    cast = random_row["cast"] if "cast" in df else "Not available"

    # Mock rating
    rating = round(np.random.uniform(7.0, 9.5), 1)

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, #E50914, #221f1f); 
                    padding:20px; border-radius:12px; color:white;">
            <h3 style="color:black;">{random_row['title']}</h3>
            <p><b>{random_row['type']}</b> • {year} • ⭐ {rating}</p>
            <p>{description}</p>
            <p><b>Director:</b> {director}</p>
            <p><b>Cast:</b> {cast}</p>
            <p><b>Country:</b> {country}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )




# ---------------------------
# Data Page
# ---------------------------
def data_page():
    st.title("📂 Netflix Dataset Explorer")

    search = st.text_input("🔍 Search by Title")
    type_filter = st.multiselect("🎬 Filter by Type", df["type"].dropna().unique())
    country_filter = st.multiselect("🌍 Filter by Country", df["country"].dropna().unique()[:20])
    year_filter = st.slider("📅 Filter by Release Year", int(df["release_year"].min()), int(df["release_year"].max()), (2000, 2020))

    filtered_df = df.copy()
    if search:
        filtered_df = filtered_df[filtered_df["title"].str.contains(search, case=False, na=False)]
    if type_filter:
        filtered_df = filtered_df[filtered_df["type"].isin(type_filter)]
    if country_filter:
        filtered_df = filtered_df[filtered_df["country"].isin(country_filter)]
    if year_filter:
        filtered_df = filtered_df[(filtered_df["release_year"] >= year_filter[0]) & (filtered_df["release_year"] <= year_filter[1])]

    st.dataframe(filtered_df.head(20), use_container_width=True)

# ---------------------------
# Visualization Page
# ---------------------------
import streamlit as st
import plotly.express as px
import pandas as pd

def visualization_page():
    global df
    st.title("📊 Data Visualizations")
    st.markdown("Interactive charts and insights from Netflix content data")

    # --- Filters ---
    st.markdown("### 🔎 Dynamic Filters")
    col1, col2 = st.columns(2)
    with col1:
        selected_country = st.selectbox("Country", ["All Countries"] + sorted(df["country"].dropna().unique().tolist()))
    with col2:
        selected_genre = st.selectbox("Genre", ["All Genres"] + sorted(set(", ".join(df["listed_in"].dropna()).split(", "))))

    # Apply filters
    df_filtered = df.copy()
    if selected_country != "All Countries":
        df_filtered = df_filtered[df_filtered["country"] == selected_country]
    if selected_genre != "All Genres":
        df_filtered = df_filtered[df_filtered["listed_in"].str.contains(selected_genre, na=False)]

    # --- Row 1: Genre & Country Distribution ---
    st.markdown("### 📊 Distribution Insights")
    col1, col2 = st.columns(2)

    with col1:
        genre_counts = df_filtered["listed_in"].str.split(", ").explode().value_counts().head(10)
        fig1 = px.bar(
            genre_counts,
            x=genre_counts.index,
            y=genre_counts.values,
            title="🎭 Top Genres Distribution",
            labels={"x": "Genre", "y": "Count"},
            color=genre_counts.values,
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        country_counts = df_filtered["country"].value_counts().head(10)
        fig2 = px.bar(
            country_counts,
            x=country_counts.index,
            y=country_counts.values,
            title="🌍 Content by Country",
            labels={"x": "Country", "y": "Count"},
            color=country_counts.values,
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # --- Row 2: Releases Over Time ---
    st.markdown("### ⏳ Content Releases Over Time")
    releases_by_year = df_filtered["release_year"].value_counts().sort_index()
    fig3 = px.area(
        x=releases_by_year.index,
        y=releases_by_year.values,
        title="📅 Content Releases Over Time",
        labels={"x": "Year", "y": "Releases"},
    )
    st.plotly_chart(fig3, use_container_width=True)

    # --- Row 3: Genre Trends Over Years ---
    st.markdown("### 📈 Genre Trends Over Years")
    genre_trends = (
        df_filtered
        .assign(genre=df_filtered["listed_in"].str.split(", "))
        .explode("genre")
        .groupby(["release_year", "genre"])
        .size()
        .reset_index(name="count")
    )
    top_genres = genre_trends.groupby("genre")["count"].sum().nlargest(5).index
    genre_trends = genre_trends[genre_trends["genre"].isin(top_genres)]

    fig4 = px.line(
        genre_trends,
        x="release_year",
        y="count",
        color="genre",
        markers=True,
        title="📈 Genre Trends Over Years"
    )
    st.plotly_chart(fig4, use_container_width=True)


# ---------------------------
# Recommendations Page
# ---------------------------
# ---------------------------
# Recommendations Page
# ---------------------------
def recommendations_page():
    st.markdown("## 🤖 AI Recommendations")
    st.markdown("Discover your next favorite show with content-based filtering")

    # ---------------------------
    # Content Filter
    # ---------------------------
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        filter_type = st.button("All", use_container_width=True)
    with col2:
        movie_filter = st.button("Movie", use_container_width=True)
    with col3:
        tv_filter = st.button("TV Show", use_container_width=True)

    if movie_filter:
        df_filtered = df[df["type"] == "Movie"]
    elif tv_filter:
        df_filtered = df[df["type"] == "TV Show"]
    else:
        df_filtered = df.copy()

    st.write("---")

    # ---------------------------
    # Personalize by Genre
    # ---------------------------
    st.markdown("### ✨ Personalize by Genre")

    genres = (
        df["listed_in"]
        .dropna()
        .str.split(", ")
        .explode()
        .unique()
        .tolist()
    )

    cols = st.columns(4)
    selected_genre = None
    for i, genre in enumerate(genres[:16]):  # show top 16 genres
        with cols[i % 4]:
            if st.button(genre, use_container_width=True):
                selected_genre = genre

    if selected_genre:
        df_filtered = df_filtered[df_filtered["listed_in"].str.contains(selected_genre, na=False)]

    st.write("---")

    # ---------------------------
    # Popular & Highly Rated
    # ---------------------------
    st.markdown("### 📈 Popular & Highly Rated")
    st.markdown("Click on any show to get similar recommendations:")

    if not df_filtered.empty:
        subset = df_filtered.sample(min(12, len(df_filtered)))  # show up to 12
        cols = st.columns(4)

        for i, (_, row) in enumerate(subset.iterrows()):
            with cols[i % 4]:
                st.markdown(
                    f"""
                    <div style="background-color:#1e1e2e; padding:15px; border-radius:10px; margin-bottom:20px;">
                        <span style="color:#ff4b4b; font-weight:bold;">{row['type']}</span>
                        <h4 style="margin:5px 0;">{row['title']}</h4>
                        <p style="margin:0; font-size:14px; color: #bbb;">{row['release_year']}</p>
                        <p style="margin:5px 0; font-size:14px;">⭐ {row.get('rating', 'N/A')}</p>
                        <p style="font-size:13px; color:#aaa;">{row.get('description', '')[:120]}...</p>
                        <p style="font-size:12px; color:#888;">{row.get('country', 'Unknown')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("No recommendations available for the selected filter.")

# ---------------------------
# Trends Page
# ---------------------------
import streamlit as st
import plotly.express as px
import pandas as pd

# ---------------------------
# Trends Page
# ---------------------------
def trends_page():
    st.markdown("## 📊 Trends & Insights")
    st.markdown("Advanced analytics and storytelling from Netflix data")

    # ---------------------------
    # Interactive Filters
    # ---------------------------
    st.markdown("### 🔎 Interactive Filters")
    col1, col2, col3 = st.columns(3)

    genres = df["listed_in"].dropna().str.split(", ").explode().unique()
    countries = df["country"].dropna().str.split(", ").explode().unique()
    ratings = df["rating"].dropna().unique()

    with col1:
        selected_genre = st.selectbox("Genre", ["All Genres"] + sorted(genres.tolist()))
    with col2:
        selected_country = st.selectbox("Country", ["All Countries"] + sorted(countries.tolist()))
    with col3:
        selected_rating = st.selectbox("Rating", ["All Ratings"] + sorted(ratings.tolist()))

    df_filtered = df.copy()
    if selected_genre != "All Genres":
        df_filtered = df_filtered[df_filtered["listed_in"].str.contains(selected_genre, na=False)]
    if selected_country != "All Countries":
        df_filtered = df_filtered[df_filtered["country"].str.contains(selected_country, na=False)]
    if selected_rating != "All Ratings":
        df_filtered = df_filtered[df_filtered["rating"] == selected_rating]

    st.write("---")

    # ---------------------------
    # Movies vs TV Shows Over Time
    # ---------------------------
    st.markdown("### 📈 Movies vs TV Shows Over Time")
    yearly_counts = df_filtered.groupby(["release_year", "type"]).size().reset_index(name="count")
    fig = px.area(
        yearly_counts,
        x="release_year",
        y="count",
        color="type",
        title="Movies vs TV Shows Over Time",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------
    # Top Producing Countries
    # ---------------------------
    st.markdown("### 🌍 Top Producing Countries Over Time")
    country_counts = (
        df_filtered.dropna(subset=["country"])
        .assign(country=df_filtered["country"].str.split(", "))
        .explode("country")
        .groupby(["release_year", "country"]).size().reset_index(name="count")
    )
    top_countries = country_counts.groupby("country")["count"].sum().nlargest(3).index
    fig2 = px.line(
        country_counts[country_counts["country"].isin(top_countries)],
        x="release_year",
        y="count",
        color="country",
        title="Top Producing Countries Over Time",
        template="plotly_dark"
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------
    # Average IMDb Rating by Genre
    # ---------------------------
    if "imdb_rating" in df_filtered.columns:
        st.markdown("### ⭐ Average IMDb Rating by Genre")
        genre_ratings = (
            df_filtered.dropna(subset=["listed_in", "imdb_rating"])
            .assign(genre=df_filtered["listed_in"].str.split(", "))
            .explode("genre")
            .groupby("genre")["imdb_rating"]
            .mean()
            .sort_values(ascending=False)
            .head(5)
        )
        fig3 = px.bar(
            genre_ratings,
            x=genre_ratings.index,
            y=genre_ratings.values,
            labels={"x": "Genre", "y": "Avg IMDb Rating"},
            template="plotly_dark"
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ---------------------------
    # Content Rating Distribution
    # ---------------------------
        # ---------------------------
    # Content Rating Distribution
    # ---------------------------
    st.markdown("### 🎬 Content Rating Distribution")
    rating_counts = df_filtered["rating"].value_counts().reset_index()
    rating_counts.columns = ["rating_label", "count"]  # rename columns

    fig4 = px.pie(
        rating_counts,
        names="rating_label",
        values="count",
        title="Content Rating Distribution",
        template="plotly_dark"
    )
    st.plotly_chart(fig4, use_container_width=True)

    # ---------------------------
    # Binge-Worthy Shows (Ranked Cards)
    # ---------------------------
    st.markdown("### 📺 Binge-Worthy Shows")
    binge_df = (
        df_filtered[df_filtered["type"] == "TV Show"]
        .dropna(subset=["title", "rating"])
        .head(10)
    )

    cols = st.columns(5)
    for i, (_, row) in enumerate(binge_df.iterrows()):
        with cols[i % 5]:
            st.markdown(
                f"""
                <div style="background-color:#1e1e2e; padding:15px; border-radius:10px; margin-bottom:20px;">
                    <span style="color:#ff4b4b; font-weight:bold;">#{i+1}</span>
                    <h4 style="margin:5px 0;">{row['title']}</h4>
                    <p style="margin:0; font-size:14px; color:#bbb;">⭐ {row['rating']}</p>
                    <p style="font-size:13px; color:#aaa;">{row.get('listed_in','')}</p>
                    <p style="font-size:12px; color:#888;">{row.get('country','')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )



    # ---------------------------
    # Binge-Worthy Shows
    # ---------------------------
   

    st.write("---")

    # ---------------------------
    # Correlation: Duration vs IMDb Rating
    # ---------------------------
    if "imdb_rating" in df_filtered.columns and "duration" in df_filtered.columns:
        st.markdown("### 🎥 Movie Duration vs IMDb Rating Correlation")
        duration_df = df_filtered[df_filtered["type"] == "Movie"].dropna(subset=["duration", "imdb_rating"])
        duration_df["minutes"] = duration_df["duration"].str.extract(r'(\d+)').astype(float)

        fig5 = px.scatter(
            duration_df,
            x="minutes",
            y="imdb_rating",
            title="Movie Duration vs IMDb Rating",
            template="plotly_dark"
        )
        st.plotly_chart(fig5, use_container_width=True)


# ---------------------------
# About Page
# ---------------------------import streamlit as st

def about_page():
    st.title("📖 About Netflix Analytics")
    st.markdown(
        """
        A comprehensive data analytics platform built with modern web technologies to provide deep insights into content libraries through interactive visualizations and machine learning-powered recommendations.
        """
    )

    # --- Project Overview ---
    st.subheader("📌 Project Overview")
    st.markdown(
        """
        **Purpose**  
        This application demonstrates advanced web development skills by creating a full-featured analytics dashboard.  
        It combines data science concepts with modern frontend technologies to deliver a professional, production-ready solution.

        **Key Highlights**
        - 🔑 Authentication system with persistent sessions  
        - ⚡ Real-time data filtering and search capabilities  
        - 🤖 Machine learning–based content recommendations  
        - 📂 Custom CSV upload and analysis functionality  
        - 📱 Responsive design optimized for all devices  
        - 🛠️ Production-ready code architecture  

        **Dataset Information**
        - Source: Curated Netflix content dataset with movies and TV shows  
        - Features: Attributes like title, genre, country, ratings, duration, cast, director, and IMDb ratings  
        - Coverage: Global content from 2008–2021 across multiple genres and countries  
        - Usage: Demonstration purposes only (users can upload their own datasets for analysis)  
        """
    )

    # --- Key Features ---
    st.subheader("✨ Key Features")
    st.markdown(
        """
        - 📂 **Data Management**: Advanced filtering, searching, and CSV export  
        - 📊 **Visualizations**: Charts, line graphs, scatter plots, and more  
        - 🤖 **ML Recommendations**: Cosine similarity–based personalized show recommendations  
        - ⚡ **Custom Analysis**: Upload your own CSV datasets for analytics  
        """
    )

    # --- Technologies Used ---
    st.subheader("🛠️ Technologies Used")
    st.markdown(
        """
        - ⚛️ **React 18** – Modern frontend with hooks and context API  
        - 🔄 **React Router** – Client-side routing and navigation  
        - 🎨 **Tailwind CSS** – Responsive UI design  
        - 📈 **Recharts** – Interactive data visualization library  
        - 🧩 **Lucide React** – Icon library  
        - 📦 **Papa Parse** – CSV parsing and processing  
        - ⚡ **Vite** – Fast frontend build tool  
        - 🐍 **Streamlit, Plotly, Pandas** – Backend analytics & visualization stack  
        """
    )

    # --- How to Use ---
    st.subheader("🚀 How to Use")
    st.markdown(
        """
        1. 🔑 **Login** – Use demo credentials or register a new account  
        2. 📊 **Explore** – Navigate through visualizations and trends  
        3. 📂 **Analyze** – Upload your CSV file to apply analytics tools  
        """
    )

    # --- Developer ---
    st.subheader("👨‍💻 Developer")
    st.markdown(
        """
        **AI Assistant**  
        Full-Stack Developer & Data Scientist  

        Specialized in creating production-ready applications with advanced analytics capabilities.  

        🔗 [GitHub](https://github.com) | [LinkedIn](https://linkedin.com) | [Email](mailto:test@example.com)
        """
    )

    # --- Credits ---
    st.subheader("🙏 Credits & Acknowledgments")
    st.markdown(
        """
        - 🎨 Icons: **Lucide React**  
        - 🖼️ Images: **Pexels** (stock images for demo purposes)  
        - 📊 Charts: **Recharts** (React chart library with D3)  
        - 🎨 Styling: **Tailwind CSS**  
        - 📦 Data Processing: **Papa Parse** (JavaScript CSV parser)  
        """
    )


# ---------------------------
# Main
# ---------------------------
if not st.session_state.authenticated:
    if st.session_state.page == "Signup":
        signup_page()
    else:
        login_page()
else:
    navbar()
    if st.session_state.page == "Home":
        home_page()
    elif st.session_state.page == "Data":
        data_page()
    elif st.session_state.page == "Visualizations":
        visualization_page()
    elif st.session_state.page == "Recommendations":
        recommendations_page()
    elif st.session_state.page == "Trends":
        trends_page()
    elif st.session_state.page == "About":
        about_page()
    elif st.session_state.page == "Logout":
        st.session_state.authenticated = False
        st.session_state.page = "Login"
        st.success("👋 You have been logged out.")
