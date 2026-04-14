import os
import random
import pickle
import requests
import streamlit as st
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="Movie Recommender", layout="wide")

# ==============================
# API KEY
# ==============================
# For Streamlit Cloud, add this in Secrets:
# API_KEY = "your_tmdb_api_key"
if "API_KEY" in st.secrets:
    API_KEY = st.secrets["API_KEY"]
else:
    API_KEY = "YOUR_TMDB_API_KEY_HERE"


# ==============================
# FETCH MOVIE DETAILS
# ==============================
def fetch_movie_details(movie_name: str):
    try:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={movie_name}"
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("results"):
            return None, None, "N/A", "No description available", None, "No reviews available"

        movie = data["results"][0]
        movie_id = movie["id"]

        poster = (
            f"https://image.tmdb.org/t/p/w500/{movie['poster_path']}"
            if movie.get("poster_path")
            else None
        )
        backdrop = (
            f"https://image.tmdb.org/t/p/original/{movie['backdrop_path']}"
            if movie.get("backdrop_path")
            else None
        )
        rating = movie.get("vote_average", "N/A")
        overview = movie.get("overview", "No description available")

        trailer = None
        video_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}"
        video_response = requests.get(video_url, timeout=10)
        if video_response.ok:
            video_data = video_response.json()
            for vid in video_data.get("results", []):
                if vid.get("type") == "Trailer" and vid.get("site") == "YouTube":
                    trailer = f"https://www.youtube.com/watch?v={vid['key']}"
                    break

        review_text = "No reviews available"
        review_url = f"https://api.themoviedb.org/3/movie/{movie_id}/reviews?api_key={API_KEY}"
        review_response = requests.get(review_url, timeout=10)
        if review_response.ok:
            review_data = review_response.json()
            if review_data.get("results"):
                review_text = review_data["results"][0]["content"][:180] + "..."

        return poster, backdrop, rating, overview, trailer, review_text

    except Exception:
        return None, None, "N/A", "No description available", None, "No reviews available"


# ==============================
# LOAD DATA
# ==============================
@st.cache_data
def load_movies():
    base_path = os.path.dirname(__file__)
    movies_path = os.path.join(base_path, "movies_intern.pkl")

    with open(movies_path, "rb") as f:
        movies_dict = pickle.load(f)

    movies_df = pd.DataFrame(movies_dict)

    if "title" not in movies_df.columns:
        raise ValueError("movies_intern.pkl must contain a 'title' column.")

    if "description" not in movies_df.columns:
        movies_df["description"] = ""

    movies_df["description"] = movies_df["description"].fillna("").astype(str)
    movies_df["title"] = movies_df["title"].fillna("").astype(str)

    return movies_df


@st.cache_resource
def build_similarity(movies_df: pd.DataFrame):
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(movies_df["description"])
    return cosine_similarity(tfidf_matrix)


movies = load_movies()
similarity = build_similarity(movies)


# ==============================
# RECOMMEND FUNCTION
# ==============================
def recommend(movie: str):
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
    for i, _ in movie_list:
        title = movies.iloc[i]["title"]
        details = fetch_movie_details(title)
        results.append((title, *details))

    return results


# ==============================
# RANDOM HERO MOVIE
# ==============================
random_movie = movies.sample(1)["title"].values[0]
hero_poster, hero_backdrop, hero_rating, hero_overview, hero_trailer, hero_review = fetch_movie_details(random_movie)


# ==============================
# CUSTOM CSS
# ==============================
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #05070d;
    color: white;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 95rem;
}

.hero {
    position: relative;
    height: 430px;
    border-radius: 22px;
    overflow: hidden;
    margin-bottom: 24px;
    box-shadow: 0 10px 35px rgba(0,0,0,0.35);
}

.overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to right, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.70) 38%, rgba(0,0,0,0.15) 100%);
    z-index: 1;
}

.faded {
    position: absolute;
    top: 18px;
    left: 34px;
    font-size: 82px;
    line-height: 0.92;
    font-weight: 900;
    color: rgba(255,255,255,0.16);
    letter-spacing: 3px;
    z-index: 2;
    pointer-events: none;
}

.hero-content {
    position: relative;
    z-index: 3;
    padding: 140px 38px 40px 38px;
    max-width: 600px;
}

.hero-title {
    font-size: 46px;
    font-weight: 800;
    margin-bottom: 12px;
    color: white;
}

.hero-desc {
    font-size: 18px;
    line-height: 1.6;
    color: #e8e8e8;
}

.section-heading {
    font-size: 28px;
    font-weight: 800;
    margin-top: 10px;
    margin-bottom: 14px;
    color: white;
}

.card-box {
    background: linear-gradient(180deg, #111827 0%, #0b1220 100%);
    border-radius: 16px;
    padding: 12px;
    min-height: 100%;
    box-shadow: 0 6px 18px rgba(0,0,0,0.25);
}

.poster-img img {
    border-radius: 12px !important;
}

.stButton > button {
    width: 100%;
    border-radius: 12px;
    font-weight: 700;
    padding: 0.6rem 1rem;
}

div[data-testid="stHorizontalBlock"] {
    gap: 1rem;
}
</style>
""", unsafe_allow_html=True)


# ==============================
# HERO SECTION
# ==============================
if hero_backdrop:
    st.markdown(f"""
    <div class="hero" style="background-image:url('{hero_backdrop}'); background-size:cover; background-position:center;">
        <div class="overlay"></div>
        <div class="faded">MOVIE<br>RECOMMENDER</div>
        <div class="hero-content">
            <div class="hero-title">{random_movie}</div>
            <div class="hero-desc">{hero_overview[:220]}...</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.title("🎬 Movie Recommender")


# ==============================
# TOP TRAILER / REVIEW
# ==============================
col_a, col_b = st.columns([1.15, 1])

with col_a:
    st.markdown('<div class="section-heading">🎞 Featured Trailer</div>', unsafe_allow_html=True)
    if hero_trailer:
        st.video(hero_trailer)
    else:
        st.info("Trailer not available for this movie.")

with col_b:
    st.markdown('<div class="section-heading">📝 Featured Review</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="card-box">
            <h3 style="margin-top:0;">{random_movie}</h3>
            <p><b>⭐ Rating:</b> {hero_rating}</p>
            <p>{hero_review}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ==============================
# SEARCH + BUTTONS
# ==============================
st.markdown('<div class="section-heading">🔍 Find Your Movie</div>', unsafe_allow_html=True)

selected_movie = st.selectbox(
    "Choose a movie",
    movies["title"].values,
    label_visibility="collapsed"
)

btn1, btn2 = st.columns(2)

with btn1:
    recommend_clicked = st.button("🔥 Recommend")

with btn2:
    surprise_clicked = st.button("🎲 Surprise Me")


# ==============================
# SURPRISE ME
# ==============================
if surprise_clicked:
    surprise_movie = movies.sample(1)["title"].values[0]
    st.success(f"Try watching: {surprise_movie}")


# ==============================
# RECOMMENDATIONS
# ==============================
if recommend_clicked:
    results = recommend(selected_movie)

    st.markdown('<div class="section-heading">🍿 Recommended Movies</div>', unsafe_allow_html=True)

    if not results:
        st.warning("No recommendations found.")
    else:
        cols = st.columns(5)
        for idx, (title, poster, backdrop, rating, overview, trailer, review) in enumerate(results):
            with cols[idx]:
                st.markdown('<div class="card-box">', unsafe_allow_html=True)

                if poster:
                    st.markdown('<div class="poster-img">', unsafe_allow_html=True)
                    st.image(poster, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No poster")

                st.markdown(f"**{title}**")
                st.write(f"⭐ {rating}")

                if trailer:
                    st.link_button("▶ Trailer", trailer, use_container_width=True)

                st.caption(overview[:100] + "..." if overview else "No description")
                st.caption("📝 " + review)

                st.markdown('</div>', unsafe_allow_html=True)


# ==============================
# TRENDING
# ==============================
st.markdown('<div class="section-heading">🔥 Trending</div>', unsafe_allow_html=True)

sample_count = min(5, len(movies))
sample_movies = random.sample(list(movies["title"].values), sample_count)
trend_cols = st.columns(sample_count)

for i, movie in enumerate(sample_movies):
    poster, _, rating, overview, trailer, review = fetch_movie_details(movie)
    with trend_cols[i]:
        st.markdown('<div class="card-box">', unsafe_allow_html=True)
        if poster:
            st.image(poster, use_container_width=True)
        st.markdown(f"**{movie}**")
        st.write(f"⭐ {rating}")
        st.markdown('</div>', unsafe_allow_html=True)
