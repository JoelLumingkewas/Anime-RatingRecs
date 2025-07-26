# AnimeTrends Version 1.0 (2025-07-14)

# Object-Oriented approach for cleaner structure + reuse
# AmimeFetcher used from Jikan API to fetch anime data
# AnimeRecommender used from AnimeFetcher (CSV) to recommend anime using its model (similarity with genre and synopsis)
# will update classes both with inheritance (sub-classes) when adding more features + optimizing data fetching!
from tqdm import tqdm
import requests
import pandas as pd
import time

class AnimeFetcher:
    def __init__(self):
        self.BASE_URL = "https://api.jikan.moe/v4"

    def safe_request(self, url, retries=3, delay=1):    # Retry mechanism for network requests
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}. Retrying in {delay}s...")
                time.sleep(delay)
        print(f'Failed after {retries} attempts: {url}')
        return None

    def fetch_anime_details(self, anime_id):     # Fetch detailed information about a specific anime
        try:
            url = f"{self.BASE_URL}/anime/{anime_id}"
            response = self.safe_request(url)
            if response is None:
                return None

            data = response.json()['data']
            return {
                "mal_id": anime_id,
                "title": data['title'],
                "title_english": data.get('title_english', ''),
                "genres": ', '.join([genre['name'] for genre in data['genres']]),
                "score": data['score'],
                "popularity": data['popularity'],
                "episodes": data['episodes'],
                "status": data['status'],
                "synopsis": data['synopsis'],
                "year": data['year'],
                "studios": ', '.join([studio['name'] for studio in data['studios']]),
                "source": data['source'],
                "duration": data['duration'],
                "image_url": data['images']['jpg']['image_url']
            }
        except Exception as e:
            print(f"Error fetching anime {anime_id}: {e}")
            return None
    
    def fetch_top_anime(self, limit=100, deep_fetch=True):      # Fetch top anime from Jikan API
        anime_list = []
        page = 1
        print(f"📥 Fetching top {limit} anime (deep_fetch={deep_fetch})...")
        while len(anime_list) < limit:
            try:
                response = self.safe_request(f"{self.BASE_URL}/top/anime?page={page}")
                if response is None:
                    break
                top_anime = response.json()['data']

                for anime in tqdm(top_anime, desc=f"Page {page}", leave=True):
                    if deep_fetch:
                        # Fetch extra details per anime
                        details = self.fetch_anime_details(anime['mal_id'])
                    else:
                        # Use shallow data from top_anime
                        details = {
                            "mal_id": anime['mal_id'],
                            "title": anime['title'],
                            "title_english": anime.get('title_english', ''),
                            "genres": ', '.join([genre['name'] for genre in anime['genres']]),
                            "score": anime.get('score', 0),
                            "popularity": anime.get('popularity', 0),
                            "episodes": anime.get('episodes', 0),
                            "status": anime.get('status', ''),
                            "synopsis": anime.get('synopsis', ''),
                            "year": anime.get('year', ''),
                            "studios": ', '.join([studio['name'] for studio in anime.get('studios', [])]),
                            "source": anime.get('source', ''),
                            "duration": anime.get('duration', ''),
                            "image_url": anime['images']['jpg']['image_url']
                        }

                    if details:
                        anime_list.append(details)

                    # Avoid rate limiting
                    time.sleep(0.5)

                    if len(anime_list) >= limit:
                        break
                page += 1
            except Exception as e:
                print(f"⚠️ Error fetching top anime page {page}: {e}")
                break

        # Ensure the loop continues properly
        df = pd.DataFrame(anime_list)
        df.insert(0, 'rank', range(1, len(df) + 1)) # add rank column by 1 so it doesn't start at 0
        return df
    
    def save_dataset(self, df, filename='anime_dataset.csv'):     # Save the DataFrame to a CSV file
        df.to_csv(filename, index=False)
        print(f"Dataset saved as {filename}")






import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import get_close_matches

class AnimeRecommender:
    def __init__(self, dataset_path="test_anime_dataset.csv"):
        # to load
        self.df = pd.read_csv(dataset_path)
        self.tfidf_matrix = None
        self.synopsis_similarity = None
        self.genre_similarity = None
        self.hybrid_similarity = None
    
    def build_model(self, synopsis_weight=0.7, genre_weight=0.3):  # weights for hybrid model (70% synopsis, 30% genre)
        print("Building recommendation model...")
        # synposis similarity (TF-IDF)
        tfidf = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = tfidf.fit_transform(self.df['synopsis'].fillna(''))
        self.synopsis_similarity = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)

        # genre similarity (one-hot encoding)
        self.df['genre_list'] = self.df['genres'].fillna('').apply(lambda x: [g.strip() for g in x.split(',') if g.strip() != ''])
        mlb = MultiLabelBinarizer()
        genre_matrix = mlb.fit_transform(self.df['genre_list'])
        self.genre_similarity = cosine_similarity(genre_matrix, genre_matrix)

        # hybrid similarity (weighted average)
        self.hybrid_similarity = (
            synopsis_weight * self.synopsis_similarity +
            genre_weight * self.genre_similarity
        )
    
        print("Model built successfully.")

    def fuzzy_search(self, query, cutoff=0.6): # finds close matches (spell errors or missing characters)
        # Combine titles and filter out None or NaN values
        titles = self.df['title'].dropna().tolist() + self.df['title_english'].dropna().tolist()
        matches = get_close_matches(query, titles, n=5, cutoff=cutoff)
        return matches[0] if matches else None
        
    def recommend(self, anime_title, top_n=5):
        # run fuzzy search first
        matched_title = self.fuzzy_search(anime_title)
        if not matched_title:
            return f"Anime '{anime_title}' not found in dataset (even with fuzzy search :( )"
        print(f"Found match! '{matched_title}' for input '{anime_title}'")
      
        # finds recommendations in the dataset (index)
        idx_row = self.df[
            (self.df['title'] == matched_title) | 
            (self.df['title_english'] == matched_title)
            ]
        if idx_row.empty:
            return f"Anime '{anime_title}' not found in dataset."
        idx = idx_row.index[0]

        # similarity scores
        scores = list(enumerate(self.hybrid_similarity[idx]))
        # sort by similarity (high to low)
        scores = sorted(scores, key=lambda x: x[1], reverse=True)[1:top_n+1]  # skip the first one (itself)

        # recommend anime titles
        recommendations = [self.df.iloc[i[0]]['title'] for i in scores]
        return recommendations