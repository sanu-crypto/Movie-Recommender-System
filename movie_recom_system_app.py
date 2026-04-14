import os
import random
import pickle
import requests
import streamlit as st
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(layout="wide", page_title="Movie Recommender")

API_KEY = st.secrets["API_KEY"]

def fetch_movie_details(movie_name):
    try:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={movie_name}"
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            movie = data["results"][0]
            movie_id = movie["id"]

            poster = (
                "https://image.tmdb.org/t/p/w500/" + movie["poster_path"]
                if movie.get("poster_path")
                else None
            )
            backdrop = (
                "https://image.tmdb.org/t/p/original/" + movie["backdrop_path"]
                if movie.get("backdrop_path")
                else None
            )
            rating = movie.get("vote_average", "N/A")
            overview = movie.get("overview", "No description available")

            trailer = None
            video_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}"
            video_response = requests.get(video_url, timeout=10)
            video_response.raise_for_status()
            video_data = video_response.json()

            for vid in video_data.get("results", []):
                if vid.get("type") == "Trailer" and vid.get("site") == "YouTube":
                    trailer = f"https://www.youtube.com/watch?v={vid['key']}"
                    break

            review_text = "No reviews available"
            review_url = f"https://api.themoviedb.org/3/movie/{movie_id}/reviews?api_key={API_KEY}"
            review_response = requests.get(review_url, timeout=10)
            review_response.raise_for_status()
            review_data = review_response.json()

            if review_data.get("results"):
                review_text = review_data["results"][0]["content"][:150] + "..."

            return poster, backdrop, rating, overview, trailer, review_text

    except Exception:
        pass

    return None, None, "N/A", "No data available", None, "No reviews available"


@st.cache_data
def load_movies():
    base_path = os.path.dirname(__file__)
    movies_path = os.path.join(base_path, "movies_intern.pkl")

    with open(movies_path, "rb") as f:
        movies_dict = pickle.load(f)

    movies = pd.DataFrame(movies_dict)

    # Make sure needed columns exist
    if "title" not in movies.columns:
        raise ValueError("movies_intern.pkl must contain a 'title' column.")

    # Use description if available, otherwise blank
    if "description" not in movies.columns:
        movies["description"] = ""
    movies["description"] = movies["description"].fillna("").astype(str)

    return movies


@st.cache_resource
def build_similarity(movies_df):
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(movies_df["description"])
    similarity = cosine_similarity(tfidf_matrix)
    return similarity


movies = load_movies()
similarity = build_similarity(movies)

st.write("APP UPDATED SUCCESSFULLY")

def recommend(movie):
    movie_index_list = movies[movies["title"] == movie].index.tolist()
    if not movie_index_list:
        return []

    index = movie_index_list[0]
    distances = similarity[index]

    movie_list = sorted(
        list(enumerate(distances)),
        key=lambda x: x[1],
        reverse=True
    )[1:6]

    results = []
    for i, _score in movie_list:
        title = movies.iloc[i]["title"]
        details = fetch_movie_details(title)
        results.append((title, *details))

    return results


random_movie = movies.sample(1)["title"].values[0]
poster, backdrop, rating, overview, trailer, review = fetch_movie_details(random_movie)

st.markdown("""
<style>
body { background-color: black; }

.hero {
    position: relative;
    height: 420px;
    border-radius: 18px;
    overflow: hidden;
    margin-bottom: 20px;
}

.overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to right, rgba(0,0,0,0.90) 0%, rgba(0,0,0,0.72) 38%, rgba(0,0,0,0.20) 100%);
    z-index: 1;
}

.faded {
    position: absolute;
    top: 20px;
    left: 40px;
    font-size: 78px;
    color: rgba(255,255,255,0.18);
    font-weight: 900;
    line-height: 0.95;
    letter-spacing: 3px;
    z-index: 2;
}

.hero-content {
    position: relative;
    z-index: 3;
    padding: 135px 40px 40px 40px;
    max-width: 560px;
}

.hero-movie-title {
    color: white;
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 12px;
}

.hero-overview {
    color: #dddddd;
    font-size: 17px;
    line-height: 1.6;
}

.card {
    background: #111;
    padding: 10px;
    border-radius: 12px;
    transition: 0.3s;
}

.card:hover {
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

if backdrop:
    st.markdown(f"""
    <div class="hero" style="background-image:url('{backdrop}'); background-size:cover; background-position:center;">
        <div class="overlay"></div>
        <div class="faded">MOVIE<br>RECOMMENDER</div>
        <div class="hero-content">
            <div class="hero-movie-title">{random_movie}</div>
            <p class="hero-overview">{overview[:200]}...</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

if trailer:
    st.video(trailer)

selected_movie = st.selectbox("Search Movie", movies["title"].values)

if st.button("🔥 Recommend"):
    results = recommend(selected_movie)
    cols = st.columns(5)

    for idx, (title, poster, backdrop, rating, overview, trailer, review) in enumerate(results):
        with cols[idx]:
            st.markdown('<div class="card">', unsafe_allow_html=True)

            if poster:
                st.image(poster, use_container_width=True)

            st.write(title)
            st.write(f"⭐ {rating}")

            if trailer:
                st.link_button("▶ Trailer", trailer)

            st.caption("📝 " + review)
            st.markdown("</div>", unsafe_allow_html=True)

if st.button("🎲 Surprise Me"):
    surprise_movie = movies.sample(1)["title"].values[0]
    st.success(f"Try watching: {surprise_movie}")

st.subheader("🔥 Trending")

sample_count = min(5, len(movies))
sample_movies = random.sample(list(movies["title"].values), sample_count)
cols = st.columns(sample_count)

for i, movie in enumerate(sample_movies):
    poster, _, rating, _, _, _ = fetch_movie_details(movie)
    with cols[i]:
        if poster:
            st.image(poster, use_container_width=True)
        st.write(movie)
        st.write(f"⭐ {rating}")
