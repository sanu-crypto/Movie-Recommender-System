# ==============================
# ✅ IMPORTS
# ==============================
import streamlit as st
import pandas as pd
import pickle
import requests
import random   # ✅ FIXED

st.set_page_config(layout="wide")

# ==============================
# 🔑 API KEY
# ==============================
API_KEY = "b7d3955b180a1d71a2dd6949cd41140a"

# ==============================
# 🎬 FETCH MOVIE DETAILS
# ==============================
def fetch_movie_details(movie_name):
    try:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={movie_name}"
        data = requests.get(search_url).json()

        if data['results']:
            movie = data['results'][0]
            movie_id = movie['id']

            poster = "https://image.tmdb.org/t/p/w500/" + movie['poster_path'] if movie.get('poster_path') else None
            backdrop = "https://image.tmdb.org/t/p/original/" + movie['backdrop_path'] if movie.get('backdrop_path') else None
            rating = movie.get('vote_average', "N/A")
            overview = movie.get('overview', "No description")

            # trailer
            trailer = None
            video_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}"
            video_data = requests.get(video_url).json()

            for vid in video_data.get("results", []):
                if vid["type"] == "Trailer":
                    trailer = f"https://www.youtube.com/watch?v={vid['key']}"
                    break

            # reviews
            review_text = "No reviews available"
            review_url = f"https://api.themoviedb.org/3/movie/{movie_id}/reviews?api_key={API_KEY}"
            review_data = requests.get(review_url).json()

            if review_data.get("results"):
                review_text = review_data["results"][0]["content"][:150] + "..."

            return poster, backdrop, rating, overview, trailer, review_text

    except:
        pass

    return None, None, "N/A", "No data", None, "No reviews"


# ==============================
# 📂 LOAD DATA
# ==============================
import os

@st.cache_data
def load_data():
    base_path = os.path.dirname(__file__)

    movies_path = os.path.join(base_path, "movies_intern.pkl")
    similarity_path = os.path.join(base_path, "similarity_intern.pkl")

    movies_dict = pickle.load(open(movies_path, 'rb'))
    similarity = pickle.load(open(similarity_path, 'rb'))

    return pd.DataFrame(movies_dict), similarity

# ==============================
# 🤖 RECOMMEND
# ==============================
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = similarity[index]

    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    results = []
    for i in movie_list:
        title = movies.iloc[i[0]]['title']
        details = fetch_movie_details(title)
        results.append((title, *details))

    return results


# ==============================
# 🎨 UI CSS
# ==============================
st.markdown("""
<style>
body { background-color: black; }

/* Hero */
.hero {
    position: relative;
    height: 420px;
}

/* overlay */
.overlay {
    position:absolute;
    width:100%;
    height:100%;
    background:linear-gradient(to right, black 40%, transparent);
}

/* faded title */
.faded {
    position:absolute;
    top:20px;
    left:40px;
    font-size:80px;
    color:rgba(255,255,255,0.15);
    font-weight:900;
}

/* card */
.card {
    background:#111;
    padding:10px;
    border-radius:10px;
    transition:0.3s;
}
.card:hover {
    transform:scale(1.08);
}
</style>
""", unsafe_allow_html=True)


# ==============================
# 🎥 HERO
# ==============================
random_movie = random.choice(movies['title'].values)
poster, backdrop, rating, overview, trailer, review = fetch_movie_details(random_movie)

if backdrop:
    st.markdown(f"""
    <div class="hero" style="background-image:url('{backdrop}'); background-size:cover; background-position:center;">
        <div class="overlay"></div>
        <div class="faded">🎬MOVIE<br>mATE</div>
        <div class="hero-content">
            <div class="hero-movie-title">{random_movie}</div>
            <p class="hero-overview">{overview[:200]}...</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 🎬 Auto trailer
if trailer:
    st.video(trailer)


# ==============================
# 🔍 SEARCH
# ==============================
selected_movie = st.selectbox("Search Movie", movies['title'].values)

# ==============================
# 🚀 BUTTON
# ==============================
if st.button("🔥 Recommend"):

    results = recommend(selected_movie)

    cols = st.columns(5)

    for i, (title, poster, backdrop, rating, overview, trailer, review) in enumerate(results):
        with cols[i]:
            st.markdown('<div class="card">', unsafe_allow_html=True)

            if poster:
                st.image(poster)

            st.write(title)
            st.write(f"⭐ {rating}")

            if trailer:
                st.video(trailer)

            st.caption("📝 " + review)

            st.markdown('</div>', unsafe_allow_html=True)


# ==============================
# 🔥 TRENDING
# ==============================
st.subheader("🔥 Trending")

sample_movies = random.sample(list(movies['title'].values), 5)
cols = st.columns(5)

for i, movie in enumerate(sample_movies):
    poster, _, rating, _, _, _ = fetch_movie_details(movie)
    with cols[i]:
        if poster:
            st.image(poster)
        st.write(movie)
        st.write(f"⭐ {rating}")
