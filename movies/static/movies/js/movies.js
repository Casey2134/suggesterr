// Movies page JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    loadMovieData();
});

async function loadMovieData() {
    try {
        // Load different movie categories using shared utils
        await Promise.all([
            loadPopularMovies(),
            loadTopRatedMovies(), 
            loadNowPlayingMovies(),
            loadUpcomingMovies()
        ]);
    } catch (error) {
        console.error('Error loading movie data:', error);
    }
}

async function loadPopularMovies() {
    try {
        const response = await fetch('/api/movies/popular/');
        const data = await response.json();
        utils.renderMovies(data, 'moviesPopular');
    } catch (error) {
        console.error('Error loading popular movies:', error);
        showError('moviesPopular', 'Failed to load popular movies');
    }
}

async function loadTopRatedMovies() {
    try {
        const response = await fetch('/api/movies/top_rated/');
        const data = await response.json();
        utils.renderMovies(data, 'moviesTopRated');
    } catch (error) {
        console.error('Error loading top rated movies:', error);
        showError('moviesTopRated', 'Failed to load top rated movies');
    }
}

async function loadNowPlayingMovies() {
    try {
        const response = await fetch('/api/movies/now_playing/');
        const data = await response.json();
        utils.renderMovies(data, 'moviesNowPlaying');
    } catch (error) {
        console.error('Error loading now playing movies:', error);
        showError('moviesNowPlaying', 'Failed to load now playing movies');
    }
}

async function loadUpcomingMovies() {
    try {
        const response = await fetch('/api/movies/upcoming/');
        const data = await response.json();
        utils.renderMovies(data, 'moviesUpcoming');
    } catch (error) {
        console.error('Error loading upcoming movies:', error);
        showError('moviesUpcoming', 'Failed to load upcoming movies');
    }
}

async function searchMovies() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) return;
    
    try {
        const response = await fetch(`/api/movies/search/?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        const resultsSection = document.getElementById('searchResults');
        resultsSection.style.display = 'block';
        utils.renderMovies(data, 'searchMovies');
    } catch (error) {
        console.error('Error searching movies:', error);
        showError('searchMovies', 'Search failed');
    }
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">${message}</p>`;
    }
}

// Search on Enter key
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && e.target.id === 'searchInput') {
        searchMovies();
    }
});