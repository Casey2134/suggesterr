// Shared utility functions for Suggesterr
class SuggesterrUtils {
    constructor() {
        this.apiBase = '/api';
    }

    // Movie rendering functions
    renderMovies(data, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Handle API response structure (either direct array or results object)
        const movies = data.results || data;
        
        if (movies && movies.length > 0) {
            container.innerHTML = '';
            movies.forEach(movie => {
                const movieCard = this.createMovieCard(movie);
                container.appendChild(movieCard);
            });
        } else {
            container.innerHTML = '<div class="no-content"><p>No movies found</p></div>';
        }
    }

    createMovieCard(movie) {
        const card = document.createElement('div');
        card.className = 'movie-card';
        
        const posterPath = movie.poster_path 
            ? `https://image.tmdb.org/t/p/w300${movie.poster_path}` 
            : '/static/img/no-poster.jpg';
        
        const year = movie.release_date ? new Date(movie.release_date).getFullYear() : '';
        const rating = movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A';
        
        // Check if movie is already requested
        const isRequested = movie.requested_on_radarr || false;
        
        card.innerHTML = `
            <div class="movie-poster-container">
                <img src="${posterPath}" alt="${movie.title}" class="movie-poster" 
                     onerror="this.src='/static/img/no-poster.jpg'">
                <div class="movie-overlay">
                    <div class="movie-actions">
                        ${isAuthenticated ? (isRequested 
                            ? '<button class="btn btn-success btn-sm" disabled><i class="fas fa-check"></i> Requested</button>'
                            : '<button class="btn btn-primary btn-sm request-btn" data-movie-id="' + movie.id + '"><i class="fas fa-download"></i> Request</button>'
                        ) : ''}
                        <button class="btn btn-secondary btn-sm details-btn"><i class="fas fa-info-circle"></i> Details</button>
                    </div>
                </div>
            </div>
            <div class="movie-info">
                <h3 class="movie-title">${movie.title}</h3>
                <p class="movie-year">${year}</p>
                <div class="movie-rating">
                    <i class="fas fa-star"></i>
                    <span>${rating}</span>
                </div>
            </div>
        `;
        
        // Add event handlers
        const requestBtn = card.querySelector('.request-btn');
        if (requestBtn) {
            requestBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.requestMovie(movie);
            });
        }
        
        const detailsBtn = card.querySelector('.details-btn');
        if (detailsBtn) {
            detailsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showMovieDetails(movie);
            });
        }
        
        return card;
    }

    // TV Show rendering functions
    renderTVShows(data, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Handle API response structure (either direct array or results object)
        const tvShows = data.results || data;
        
        if (tvShows && tvShows.length > 0) {
            container.innerHTML = '';
            tvShows.forEach(tvShow => {
                const tvShowCard = this.createTVShowCard(tvShow);
                container.appendChild(tvShowCard);
            });
        } else {
            container.innerHTML = '<div class="no-content"><p>No TV shows found</p></div>';
        }
    }

    createTVShowCard(tvShow) {
        const card = document.createElement('div');
        card.className = 'tv-show-card movie-card';
        
        const posterPath = tvShow.poster_path 
            ? `https://image.tmdb.org/t/p/w300${tvShow.poster_path}` 
            : '/static/img/no-poster.jpg';
        
        const year = tvShow.first_air_date ? new Date(tvShow.first_air_date).getFullYear() : '';
        const rating = tvShow.vote_average ? tvShow.vote_average.toFixed(1) : 'N/A';
        
        // Check if TV show is already requested
        const isRequested = tvShow.requested_on_sonarr || false;
        
        card.innerHTML = `
            <div class="movie-poster-container">
                <img src="${posterPath}" alt="${tvShow.name}" class="movie-poster" 
                     onerror="this.src='/static/img/no-poster.jpg'">
                <div class="movie-overlay">
                    <div class="movie-actions">
                        ${isAuthenticated ? (isRequested 
                            ? '<button class="btn btn-success btn-sm" disabled><i class="fas fa-check"></i> Requested</button>'
                            : '<button class="btn btn-primary btn-sm request-btn" data-tv-id="' + tvShow.id + '"><i class="fas fa-download"></i> Request</button>'
                        ) : ''}
                        <button class="btn btn-secondary btn-sm details-btn"><i class="fas fa-info-circle"></i> Details</button>
                    </div>
                </div>
            </div>
            <div class="movie-info">
                <h3 class="movie-title">${tvShow.name}</h3>
                <p class="movie-year">${year}</p>
                <div class="movie-rating">
                    <i class="fas fa-star"></i>
                    <span>${rating}</span>
                </div>
            </div>
        `;
        
        // Add event handlers
        const requestBtn = card.querySelector('.request-btn');
        if (requestBtn) {
            requestBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.requestTVShow(tvShow);
            });
        }
        
        const detailsBtn = card.querySelector('.details-btn');
        if (detailsBtn) {
            detailsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showTVShowDetails(tvShow.id || tvShow.tmdb_id);
            });
        }
        
        return card;
    }

    // Movie requesting functionality
    async requestMovie(movie) {
        if (!isAuthenticated) {
            alert('Please log in to request movies');
            return;
        }
        
        try {
            // Get full movie details if needed
            const movieData = movie.id ? movie : await this.getMovieDetails(movie.tmdb_id || movie.id);
            this.showMovieRequestModal(movieData);
        } catch (error) {
            console.error('Error requesting movie:', error);
            alert('Failed to load movie details');
        }
    }

    async getMovieDetails(movieId) {
        const response = await fetch(`${this.apiBase}/movies/${movieId}/`);
        return await response.json();
    }

    showMovieRequestModal(movie) {
        const modal = document.getElementById('movieRequestModal');
        const title = document.getElementById('requestModalTitle');
        const poster = document.getElementById('requestMoviePoster');
        const movieTitle = document.getElementById('requestMovieTitle');
        const movieYear = document.getElementById('requestMovieYear');
        const movieOverview = document.getElementById('requestMovieOverview');
        
        title.textContent = `Request: ${movie.title}`;
        poster.src = movie.poster_path ? `https://image.tmdb.org/t/p/w300${movie.poster_path}` : '/static/img/no-poster.jpg';
        movieTitle.textContent = movie.title;
        movieYear.textContent = movie.release_date ? new Date(movie.release_date).getFullYear() : '';
        movieOverview.textContent = movie.overview || 'No overview available.';
        
        // Store movie data for submission
        modal.dataset.movieId = movie.id;
        
        // Load quality profiles
        this.loadQualityProfiles();
        
        modal.style.display = 'block';
    }

    async loadQualityProfiles() {
        try {
            const response = await fetch(`${this.apiBase}/movies/quality_profiles/`);
            const profiles = await response.json();
            
            const select = document.getElementById('qualityProfile');
            select.innerHTML = '<option value="">Select Quality Profile</option>';
            
            if (profiles && profiles.length > 0) {
                profiles.forEach(profile => {
                    const option = document.createElement('option');
                    option.value = profile.id;
                    option.textContent = profile.name;
                    select.appendChild(option);
                });
            } else {
                select.innerHTML = '<option value="">No quality profiles available</option>';
            }
        } catch (error) {
            console.error('Error loading quality profiles:', error);
            const select = document.getElementById('qualityProfile');
            select.innerHTML = '<option value="">Failed to load profiles</option>';
        }
    }

    // TV Show requesting functionality
    async requestTVShow(tvShow) {
        if (!isAuthenticated) {
            alert('Please log in to request TV shows');
            return;
        }
        
        try {
            // Get full TV show details if needed
            const tvShowData = tvShow.id ? tvShow : await this.getTVShowDetails(tvShow.tmdb_id || tvShow.id);
            this.showTVShowRequestModal(tvShowData);
        } catch (error) {
            console.error('Error requesting TV show:', error);
            alert('Failed to load TV show details');
        }
    }

    async getTVShowDetails(tvShowId) {
        const response = await fetch(`${this.apiBase}/tv-shows/${tvShowId}/`);
        return await response.json();
    }

    showTVShowRequestModal(tvShow) {
        const modal = document.getElementById('tvRequestModal');
        const title = document.getElementById('tvRequestModalTitle');
        const poster = document.getElementById('requestTVPoster');
        const tvShowTitle = document.getElementById('requestTVTitle');
        const tvShowYear = document.getElementById('requestTVYear');
        const tvShowOverview = document.getElementById('requestTVOverview');
        
        title.textContent = `Request: ${tvShow.name}`;
        poster.src = tvShow.poster_path ? `https://image.tmdb.org/t/p/w300${tvShow.poster_path}` : '/static/img/no-poster.jpg';
        tvShowTitle.textContent = tvShow.name;
        tvShowYear.textContent = tvShow.first_air_date ? new Date(tvShow.first_air_date).getFullYear() : '';
        tvShowOverview.textContent = tvShow.overview || 'No overview available.';
        
        // Store TV show data for submission
        modal.dataset.tvShowId = tvShow.id;
        
        // Load quality profiles and seasons
        this.loadTVQualityProfiles();
        this.loadTVSeasons(tvShow.id);
        
        modal.style.display = 'block';
    }

    async loadTVQualityProfiles() {
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/quality_profiles/`);
            const profiles = await response.json();
            
            const select = document.getElementById('tvQualityProfile');
            select.innerHTML = '<option value="">Select Quality Profile</option>';
            
            if (profiles && profiles.length > 0) {
                profiles.forEach(profile => {
                    const option = document.createElement('option');
                    option.value = profile.id;
                    option.textContent = profile.name;
                    select.appendChild(option);
                });
            } else {
                select.innerHTML = '<option value="">No quality profiles available</option>';
            }
        } catch (error) {
            console.error('Error loading quality profiles:', error);
            const select = document.getElementById('tvQualityProfile');
            select.innerHTML = '<option value="">Failed to load profiles</option>';
        }
    }

    async loadTVSeasons(tvShowId) {
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/${tvShowId}/seasons/`);
            const seasons = await response.json();
            
            const container = document.getElementById('seasonSelection');
            container.innerHTML = '';
            
            if (seasons && seasons.length > 0) {
                seasons.forEach(season => {
                    const seasonDiv = document.createElement('div');
                    seasonDiv.className = 'season-item';
                    seasonDiv.innerHTML = `
                        <label>
                            <input type="checkbox" name="seasons" value="${season.season_number}" checked>
                            Season ${season.season_number} (${season.episode_count} episodes)
                        </label>
                    `;
                    container.appendChild(seasonDiv);
                });
            } else {
                container.innerHTML = '<p>No season information available</p>';
            }
        } catch (error) {
            console.error('Error loading seasons:', error);
            const container = document.getElementById('seasonSelection');
            container.innerHTML = '<p>Failed to load seasons</p>';
        }
    }

    // Modal functionality
    showMovieDetails(movie) {
        const modal = document.getElementById('movieModal');
        const title = document.getElementById('movieTitle');
        const details = document.getElementById('movieDetails');
        
        if (modal && title && details) {
            title.textContent = movie.title;
            
            const posterPath = movie.poster_path 
                ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` 
                : '/static/img/no-poster.jpg';
            
            details.innerHTML = `
                <div style="display: flex; gap: 2rem; margin-bottom: 1rem;">
                    <img src="${posterPath}" alt="${movie.title}" 
                         style="width: 200px; height: auto; border-radius: 8px;"
                         onerror="this.src='/static/img/no-poster.jpg'">
                    <div>
                        <p><strong>Release Date:</strong> ${movie.release_date || 'Unknown'}</p>
                        <p><strong>Rating:</strong> ${movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A'}/10</p>
                        <p><strong>Overview:</strong></p>
                        <p style="line-height: 1.6;">${movie.overview || 'No overview available.'}</p>
                    </div>
                </div>
            `;
            
            modal.classList.add('active');
        }
    }

    showTVShowDetails(tvShow) {
        const modal = document.getElementById('tvShowModal');
        const title = document.getElementById('tvShowTitle');
        const details = document.getElementById('tvShowDetails');
        
        if (modal && title && details) {
            title.textContent = tvShow.name;
            
            const posterPath = tvShow.poster_path 
                ? `https://image.tmdb.org/t/p/w500${tvShow.poster_path}` 
                : '/static/img/no-poster.jpg';
            
            details.innerHTML = `
                <div style="display: flex; gap: 2rem; margin-bottom: 1rem;">
                    <img src="${posterPath}" alt="${tvShow.name}" 
                         style="width: 200px; height: auto; border-radius: 8px;"
                         onerror="this.src='/static/img/no-poster.jpg'">
                    <div>
                        <p><strong>First Air Date:</strong> ${tvShow.first_air_date || 'Unknown'}</p>
                        <p><strong>Rating:</strong> ${tvShow.vote_average ? tvShow.vote_average.toFixed(1) : 'N/A'}/10</p>
                        ${tvShow.number_of_seasons ? `<p><strong>Seasons:</strong> ${tvShow.number_of_seasons}</p>` : ''}
                        ${tvShow.number_of_episodes ? `<p><strong>Episodes:</strong> ${tvShow.number_of_episodes}</p>` : ''}
                        <p><strong>Overview:</strong></p>
                        <p style="line-height: 1.6;">${tvShow.overview || 'No overview available.'}</p>
                    </div>
                </div>
            `;
            
            modal.classList.add('active');
        }
    }
}

// Global utility instance
const utils = new SuggesterrUtils();

// Global submission functions for modal buttons
async function submitMovieRequest() {
    const modal = document.getElementById('movieRequestModal');
    const movieId = modal.dataset.movieId;
    const qualityProfileId = document.getElementById('qualityProfile').value;
    const searchImmediately = document.getElementById('searchImmediately').checked;
    
    if (!qualityProfileId) {
        alert('Please select a quality profile');
        return;
    }
    
    try {
        const response = await fetch(`${utils.apiBase}/movies/${movieId}/request_movie/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                quality_profile_id: qualityProfileId,
                search_immediately: searchImmediately
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Movie requested successfully!');
            closeRequestModal();
            // Reload the page to update request status
            location.reload();
        } else {
            alert(data.error || 'Failed to request movie');
        }
    } catch (error) {
        console.error('Error submitting movie request:', error);
        alert('Failed to request movie');
    }
}

async function submitTVRequest() {
    const modal = document.getElementById('tvRequestModal');
    const tvShowId = modal.dataset.tvShowId;
    const qualityProfileId = document.getElementById('tvQualityProfile').value;
    const searchImmediately = document.getElementById('tvSearchImmediately').checked;
    
    // Get selected seasons
    const selectedSeasons = [];
    const seasonCheckboxes = document.querySelectorAll('input[name="seasons"]:checked');
    seasonCheckboxes.forEach(checkbox => {
        selectedSeasons.push(parseInt(checkbox.value));
    });
    
    if (!qualityProfileId) {
        alert('Please select a quality profile');
        return;
    }
    
    if (selectedSeasons.length === 0) {
        alert('Please select at least one season');
        return;
    }
    
    try {
        const response = await fetch(`${utils.apiBase}/tv-shows/${tvShowId}/request_tv_show/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                quality_profile_id: qualityProfileId,
                seasons: selectedSeasons,
                search_immediately: searchImmediately
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('TV show requested successfully!');
            closeTVRequestModal();
            // Reload the page to update request status
            location.reload();
        } else {
            alert(data.error || 'Failed to request TV show');
        }
    } catch (error) {
        console.error('Error submitting TV show request:', error);
        alert('Failed to request TV show');
    }
}