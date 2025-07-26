
import time
from animetrends import AnimeFetcher

def initialize_dataset(limit=20):  # Starting with a smaller limit for testing
    try:
        print("Initializing AnimeFetcher...")
        fetcher = AnimeFetcher()
        
        print(f"Fetching top {limit} anime...")
        df = fetcher.fetch_top_anime(limit=limit, deep_fetch=True)
        
        if df is not None and not df.empty:
            print(f"Successfully fetched {len(df)} anime entries")
            filename = 'test_anime_dataset.csv'
            fetcher.save_dataset(df, filename)
            print(f"Dataset saved to {filename}")
            return True
        else:
            print("Error: Failed to fetch anime data")
            return False
            
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        return False

# Run the initialization
if __name__ == "__main__":
    success = initialize_dataset()
    if not success:
        print("Failed to initialize dataset. Please check your internet connection and try again.")
