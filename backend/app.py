# source venv/bin/activate
# to go into virtual environment
from flask import Flask, jsonify
from flask_cors import CORS
from animetrends import AnimeFetcher, AnimeRecommender
import logging
import numpy as np
import json


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.bool_)):
            return bool(obj)
        if pd.isna(obj):  # Handle NaN values
            return None
        return super(NpEncoder, self).default(obj)



# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configure CORS to allow requests from your React frontend
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize our anime systems
try:
    logger.info("Initializing AnimeFetcher and AnimeRecommender...")
    fetcher = AnimeFetcher()
    recommender = AnimeRecommender('test_anime_dataset.csv')
    recommender.build_model()
    logger.info("Initialization successful")
except Exception as e:
    logger.error(f"Initialization failed: {str(e)}")
    raise

@app.route('/api/top-anime')
def get_top_anime():
    try:
        logger.info("Fetching top anime...")
        df = fetcher.fetch_top_anime(limit=20, deep_fetch=True)
        if df is None or df.empty:
            logger.error("Fetched DataFrame is empty or None")
            return jsonify({"error": "No anime data retrieved"}), 500
            
        # Convert DataFrame to records and handle NaN values
        df = df.replace({np.nan: None})  # Replace NaN with None
        records = df.to_dict('records')
        logger.info(f"Successfully fetched {len(records)} anime entries")
        return json.dumps(records, cls=NpEncoder)  # Use custom encoder
    except Exception as e:
        logger.error(f"Error fetching top anime: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommendations/<title>')
def get_recommendations(title):
    try:
        logger.info(f"Getting recommendations for: {title}")
        recommendations = recommender.recommend(title, top_n=5)
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)