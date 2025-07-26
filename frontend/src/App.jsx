import { useState, useEffect } from 'react'
import './App.css'

function AnimeCard({ anime, onSelect }) {
  return (
    <div className="anime-card" onClick={() => onSelect(anime)}>
      <img src={anime.image_url} alt={anime.title} />
      <h3>{anime.title}</h3>
      <p>Score: {anime.score}</p>
      <p>Genres: {anime.genres}</p>
    </div>
  )
}

function App() {
  const [topAnime, setTopAnime] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    console.log('Fetching anime data...');  // Debug log
    fetch('http://localhost:8000/api/top-anime')
      .then(res => {
        console.log('Response received:', res.status);  // Debug log
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        console.log('Data received:', data);  // Debug log
        setTopAnime(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Fetch error:', err);  // Detailed error log
        setError(`Failed to fetch anime: ${err.message}`);
        setLoading(false);
      });
  }, []);

  const handleAnimeSelect = (anime) => {
    fetch(`http://localhost:8000/api/recommendations/${encodeURIComponent(anime.title)}`)
      .then(res => res.json())
      .then(data => {
        setRecommendations(data.recommendations)
      })
      .catch(err => console.error('Error fetching recommendations:', err))
  }

  if (loading) return <div className="loading">Loading...</div>
  if (error) return <div className="error">{error}</div>

  return (
    <div className="container">
      <h1>Anime Recommender</h1>
      
      <div className="anime-grid">
        {topAnime.map(anime => (
          <AnimeCard 
            key={anime.mal_id} 
            anime={anime} 
            onSelect={handleAnimeSelect}
          />
        ))}
      </div>

      {recommendations.length > 0 && (
        <div className="recommendations">
          <h2>Recommended Anime</h2>
          <div className="recommendations-list">
            {recommendations.map((title, index) => (
              <div key={index} className="recommendation-item">
                {title}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
