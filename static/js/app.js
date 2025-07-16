class MovieApp {
    constructor() {
        this.apiBase = '/api';
        this.currentTab = 'popular';
        this.genres = [];
        this.init();
    }

    async init() {
        await this.loadGenres();
        this.setupEventListeners();
        this.loadInitialData();
    }

    async loadGenres() {
        try {
            const response = await fetch(`${this.apiBase}/genres/`);
            this.genres = await response.json();
            this.populateGenreFilter();
        } catch (error) {
            console.error('Error loading genres:', error);
        }
    }

    populateGenreFilter() {
        const genreFilter = document.getElementById('genreFilter');
        genreFilter.innerHTML = '<option value="">All Genres</option>';
        
        this.genres.forEach(genre => {
            const option = document.createElement('option');
            option.value = genre.id;
            option.textContent = genre.name;
            genreFilter.appendChild(option);
        });
    }

    setupEventListeners() {
        // Tab switching
        document.getElementById('popular-tab').addEventListener('click', () => {
            this.currentTab = 'popular';
            this.loadMovies('popular');
        });

        document.getElementById('top-rated-tab').addEventListener('click', () => {
            this.currentTab = 'top-rated';
            this.loadMovies('top_rated');
        });

        document.getElementById('recommendations-tab').addEventListener('click', () => {
            this.currentTab = 'recommendations';
            this.loadRecommendations();
        });

        // Search functionality
        const searchInput = document.getElementById('movieSearch');
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.searchMovies(e.target.value);
            }, 500);
        });

        // Filter functionality
        document.getElementById('genreFilter').addEventListener('change', (e) => {
            this.filterMovies();
        });

        document.getElementById('availableOnly').addEventListener('change', (e) => {
            this.filterMovies();
        });
    }

    async loadInitialData() {
        await this.loadMovies('popular');
        await this.loadPopularTVShows();
        await this.loadTopRatedTVShows();
    }

    async loadMovies(type) {
        try {
            const endpoint = type === 'popular' ? 'movies/popular/' : 'movies/top_rated/';
            const response = await fetch(`${this.apiBase}/${endpoint}`);
            const movies = await response.json();
            
            const containerId = type === 'popular' ? 'popularMovies' : 'topRatedMovies';
            this.renderMovies(movies, containerId);
        } catch (error) {
            console.error(`Error loading ${type} movies:`, error);
        }
    }

    async loadRecommendations() {
        try {
            const response = await fetch(`${this.apiBase}/recommendations/`);
            const recommendations = await response.json();
            
            this.renderRecommendations(recommendations, 'recommendedMovies');
        } catch (error) {
            console.error('Error loading recommendations:', error);
            document.getElementById('recommendedMovies').innerHTML = `
                <div class="col-12 text-center">
                    <p class="text-muted">Please log in to see personalized recommendations.</p>
                </div>
            `;
        }
    }

    async searchMovies(query) {
        if (!query.trim()) {
            this.loadMovies(this.currentTab);
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/movies/?search=${encodeURIComponent(query)}`);
            const movies = await response.json();
            
            const containerId = this.getActiveContainerId();
            this.renderMovies(movies.results || movies, containerId);
        } catch (error) {
            console.error('Error searching movies:', error);
        }
    }

    async filterMovies() {
        const genreFilter = document.getElementById('genreFilter').value;
        const availableOnly = document.getElementById('availableOnly').checked;
        
        let url = `${this.apiBase}/movies/?`;
        const params = new URLSearchParams();
        
        if (genreFilter) {
            params.append('genre', genreFilter);
        }
        
        if (availableOnly) {
            params.append('available_only', 'true');
        }

        try {
            const response = await fetch(url + params.toString());
            const movies = await response.json();
            
            const containerId = this.getActiveContainerId();
            this.renderMovies(movies.results || movies, containerId);
        } catch (error) {
            console.error('Error filtering movies:', error);
        }
    }

    getActiveContainerId() {
        const activeTab = document.querySelector('.nav-link.active').id;
        switch (activeTab) {
            case 'popular-tab':
                return 'popularMovies';
            case 'top-rated-tab':
                return 'topRatedMovies';
            case 'recommendations-tab':
                return 'recommendedMovies';
            default:
                return 'popularMovies';
        }
    }

    renderMovies(movies, containerId) {
        const container = document.getElementById(containerId);
        
        if (!movies || movies.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center">
                    <p class="text-muted">No movies found.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = movies.map(movie => this.createMovieCard(movie)).join('');
    }

    renderRecommendations(recommendations, containerId) {
        const container = document.getElementById(containerId);
        
        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center">
                    <p class="text-muted">No recommendations available. Rate some movies to get started!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = recommendations.map(rec => this.createRecommendationCard(rec)).join('');
    }

    createMovieCard(movie) {
        const posterUrl = movie.poster_path ? 
            `https://image.tmdb.org/t/p/w300${movie.poster_path}` : 
            'https://via.placeholder.com/300x450?text=No+Poster';

        const availabilityBadge = this.getAvailabilityBadge(movie);
        const genres = movie.genres ? movie.genres.map(g => g.name).join(', ') : '';

        return `
            <div class="col-xl-4 col-lg-6 col-md-12 mb-4">
                <div class="card movie-card h-100" onclick="app.showMovieModal(${movie.id})">
                    <div class="position-relative">
                        <img src="${posterUrl}" class="card-img-top movie-poster" alt="${movie.title}">
                        ${availabilityBadge}
                        <div class="rating-badge">
                            <i class="fas fa-star"></i> ${movie.vote_average || 'N/A'}
                        </div>
                        <div class="card-hover-buttons">
                            <button class="btn btn-primary btn-sm me-2" onclick="event.stopPropagation(); app.showMovieModal(${movie.id})">
                                <i class="fas fa-info-circle"></i> Info
                            </button>
                            <button class="btn btn-success btn-sm" onclick="event.stopPropagation(); app.requestMovie(${movie.id})">
                                <i class="fas fa-download"></i> Request
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <h6 class="movie-title">${movie.title}</h6>
                        <p class="movie-overview">${movie.overview || 'No overview available.'}</p>
                        <div class="genres">
                            ${genres.split(', ').map(g => `<span class="badge bg-secondary genre-badge">${g}</span>`).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    createRecommendationCard(recommendation) {
        const movie = recommendation.movie;
        const posterUrl = movie.poster_path ? 
            `https://image.tmdb.org/t/p/w300${movie.poster_path}` : 
            'https://via.placeholder.com/300x450?text=No+Poster';

        const availabilityBadge = this.getAvailabilityBadge(movie);

        return `
            <div class="col-xl-4 col-lg-6 col-md-12 mb-4">
                <div class="card movie-card h-100" onclick="app.showMovieModal(${movie.id})">
                    <div class="position-relative">
                        <img src="${posterUrl}" class="card-img-top movie-poster" alt="${movie.title}">
                        ${availabilityBadge}
                        <div class="rating-badge">
                            <i class="fas fa-star"></i> ${movie.vote_average || 'N/A'}
                        </div>
                        <div class="card-hover-buttons">
                            <button class="btn btn-primary btn-sm me-2" onclick="event.stopPropagation(); app.showMovieModal(${movie.id})">
                                <i class="fas fa-info-circle"></i> Info
                            </button>
                            <button class="btn btn-success btn-sm" onclick="event.stopPropagation(); app.requestMovie(${movie.id})">
                                <i class="fas fa-download"></i> Request
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <h6 class="movie-title">${movie.title}</h6>
                        <p class="movie-overview">${movie.overview || 'No overview available.'}</p>
                        <div class="recommendation-reason">
                            <i class="fas fa-lightbulb"></i> ${recommendation.reason}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getAvailabilityBadge(movie) {
        if (movie.available_on_jellyfin || movie.available_on_plex) {
            return '<div class="availability-badge available">Available</div>';
        } else if (movie.requested_on_radarr) {
            return '<div class="availability-badge requested">Requested</div>';
        } else {
            return '<div class="availability-badge unavailable">Unavailable</div>';
        }
    }

    async showMovieModal(movieId) {
        try {
            const response = await fetch(`${this.apiBase}/movies/${movieId}/`);
            const movie = await response.json();
            
            const modal = document.getElementById('movieModal');
            const modalTitle = document.getElementById('movieModalTitle');
            const modalBody = document.getElementById('movieModalBody');
            const requestBtn = document.getElementById('requestMovieBtn');
            
            modalTitle.textContent = movie.title;
            modalBody.innerHTML = this.createMovieModalContent(movie);
            
            // Setup request button
            requestBtn.onclick = () => this.requestMovie(movieId);
            requestBtn.style.display = (movie.available_on_jellyfin || movie.available_on_plex) ? 'none' : 'block';
            
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
        } catch (error) {
            console.error('Error loading movie details:', error);
        }
    }

    createMovieModalContent(movie) {
        const posterUrl = movie.poster_path ? 
            `https://image.tmdb.org/t/p/w500${movie.poster_path}` : 
            'https://via.placeholder.com/500x750?text=No+Poster';

        const genres = movie.genres ? movie.genres.map(g => g.name).join(', ') : 'Unknown';
        const releaseYear = movie.release_date ? new Date(movie.release_date).getFullYear() : 'Unknown';

        return `
            <div class="row">
                <div class="col-md-4">
                    <img src="${posterUrl}" class="img-fluid rounded" alt="${movie.title}">
                </div>
                <div class="col-md-8">
                    <h5>${movie.title} (${releaseYear})</h5>
                    <p><strong>Rating:</strong> ${movie.vote_average}/10 (${movie.vote_count} votes)</p>
                    <p><strong>Genres:</strong> ${genres}</p>
                    <p><strong>Runtime:</strong> ${movie.runtime ? movie.runtime + ' minutes' : 'Unknown'}</p>
                    <p><strong>Overview:</strong></p>
                    <p>${movie.overview || 'No overview available.'}</p>
                    
                    <div class="mt-3">
                        <h6>Availability:</h6>
                        <div class="d-flex gap-2">
                            ${movie.available_on_jellyfin ? '<span class="badge bg-success">Jellyfin</span>' : ''}
                            ${movie.available_on_plex ? '<span class="badge bg-success">Plex</span>' : ''}
                            ${movie.requested_on_radarr ? '<span class="badge bg-warning">Requested</span>' : ''}
                            ${!movie.available_on_jellyfin && !movie.available_on_plex && !movie.requested_on_radarr ? 
                                '<span class="badge bg-secondary">Not Available</span>' : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async requestMovie(movieId) {
        try {
            const response = await fetch(`${this.apiBase}/movies/${movieId}/request_movie/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });

            if (response.ok) {
                alert('Movie requested successfully!');
                // Refresh the current view
                this.loadMovies(this.currentTab);
            } else {
                alert('Failed to request movie. Please try again.');
            }
        } catch (error) {
            console.error('Error requesting movie:', error);
            alert('Error requesting movie. Please try again.');
        }
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // TV Show Methods
    async loadPopularTVShows() {
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/popular/`);
            const tvShows = await response.json();
            this.renderTVShows(tvShows, 'popularTVShows');
        } catch (error) {
            console.error('Error loading popular TV shows:', error);
        }
    }

    async loadTopRatedTVShows() {
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/top_rated/`);
            const tvShows = await response.json();
            this.renderTVShows(tvShows, 'topRatedTVShows');
        } catch (error) {
            console.error('Error loading top rated TV shows:', error);
        }
    }

    async loadTVShowsSection() {
        this.loadTVShows('popular', 'tvShowsPopular');
        this.loadTVShows('top_rated', 'tvShowsTopRated');
        this.loadTVShows('airing_today', 'tvShowsAiringToday');
        this.loadTVShows('on_the_air', 'tvShowsOnTheAir');
    }

    async loadTVShows(endpoint, containerId) {
        try {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            }
            
            const response = await fetch(`${this.apiBase}/tv-shows/${endpoint}/`);
            const tvShows = await response.json();
            
            if (tvShows && tvShows.length > 0) {
                this.renderTVShows(tvShows, containerId);
            } else {
                if (container) {
                    container.innerHTML = '<div class="loading"><p>No TV shows found.</p></div>';
                }
            }
        } catch (error) {
            console.error(`Error loading ${endpoint} TV shows:`, error);
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = '<div class="loading"><p>Error loading TV shows.</p></div>';
            }
        }
    }

    renderTVShows(tvShows, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!tvShows || tvShows.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center">
                    <p class="text-muted">No TV shows found.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = tvShows.map(tvShow => this.createTVShowCard(tvShow)).join('');
    }

    createTVShowCard(tvShow) {
        const posterUrl = tvShow.poster_path ? 
            `https://image.tmdb.org/t/p/w300${tvShow.poster_path}` : 
            'https://via.placeholder.com/300x450?text=No+Poster';

        const availabilityBadge = this.getAvailabilityBadge(tvShow);
        const genres = tvShow.genres ? tvShow.genres.map(g => g.name).join(', ') : '';
        const title = tvShow.title || tvShow.name || 'Unknown Title';
        const airDate = tvShow.first_air_date ? new Date(tvShow.first_air_date).getFullYear() : 'TBA';

        return `
            <div class="col-xl-4 col-lg-6 col-md-12 mb-4">
                <div class="card tv-card h-100" onclick="app.showTVShowModal(${tvShow.id})">
                    <div class="position-relative">
                        <img src="${posterUrl}" class="card-img-top tv-poster" alt="${title}">
                        ${availabilityBadge}
                        <div class="rating-badge">
                            <i class="fas fa-star"></i> ${tvShow.vote_average || 'N/A'}
                        </div>
                        <div class="card-hover-buttons">
                            <button class="btn btn-primary btn-sm me-2" onclick="event.stopPropagation(); app.showTVShowModal(${tvShow.id})">
                                <i class="fas fa-info-circle"></i> Info
                            </button>
                            <button class="btn btn-success btn-sm" onclick="event.stopPropagation(); app.requestTVShow(${tvShow.id})">
                                <i class="fas fa-download"></i> Request
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <h6 class="tv-title">${title}</h6>
                        <p class="tv-overview">${tvShow.overview || 'No overview available.'}</p>
                        <div class="tv-details">
                            <small class="text-muted">First Aired: ${airDate}</small>
                        </div>
                        <div class="genres">
                            ${genres.split(', ').map(g => `<span class="badge bg-secondary genre-badge">${g}</span>`).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async showTVShowModal(tvShowId) {
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/${tvShowId}/`);
            const tvShow = await response.json();
            
            const modal = document.getElementById('movieModal');
            const modalTitle = document.getElementById('movieModalTitle');
            const modalBody = document.getElementById('movieModalBody');
            const requestBtn = document.getElementById('requestMovieBtn');
            
            const title = tvShow.title || tvShow.name || 'Unknown Title';
            modalTitle.textContent = title;
            modalBody.innerHTML = this.createTVShowModalContent(tvShow);
            
            requestBtn.onclick = () => this.requestTVShow(tvShowId);
            requestBtn.style.display = (tvShow.available_on_jellyfin || tvShow.available_on_plex) ? 'none' : 'block';
            requestBtn.innerHTML = '<i class="fas fa-download"></i> Request TV Show';
            
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
        } catch (error) {
            console.error('Error loading TV show details:', error);
        }
    }

    createTVShowModalContent(tvShow) {
        const posterUrl = tvShow.poster_path ? 
            `https://image.tmdb.org/t/p/w500${tvShow.poster_path}` : 
            'https://via.placeholder.com/500x750?text=No+Poster';

        const genres = tvShow.genres ? tvShow.genres.map(g => g.name).join(', ') : 'Unknown';
        const airYear = tvShow.first_air_date ? new Date(tvShow.first_air_date).getFullYear() : 'Unknown';
        const title = tvShow.title || tvShow.name || 'Unknown Title';

        return `
            <div class="row">
                <div class="col-md-4">
                    <img src="${posterUrl}" class="img-fluid rounded" alt="${title}">
                </div>
                <div class="col-md-8">
                    <h5>${title} (${airYear})</h5>
                    <p><strong>Rating:</strong> ${tvShow.vote_average}/10 (${tvShow.vote_count} votes)</p>
                    <p><strong>Genres:</strong> ${genres}</p>
                    <p><strong>Status:</strong> ${tvShow.status || 'Unknown'}</p>
                    <p><strong>Seasons:</strong> ${tvShow.number_of_seasons || 'Unknown'}</p>
                    <p><strong>Episodes:</strong> ${tvShow.number_of_episodes || 'Unknown'}</p>
                    <p><strong>Overview:</strong></p>
                    <p>${tvShow.overview || 'No overview available.'}</p>
                    
                    <div class="mt-3">
                        <h6>Availability:</h6>
                        <div class="d-flex gap-2">
                            ${tvShow.available_on_jellyfin ? '<span class="badge bg-success">Jellyfin</span>' : ''}
                            ${tvShow.available_on_plex ? '<span class="badge bg-success">Plex</span>' : ''}
                            ${tvShow.requested_on_sonarr ? '<span class="badge bg-warning">Requested</span>' : ''}
                            ${!tvShow.available_on_jellyfin && !tvShow.available_on_plex && !tvShow.requested_on_sonarr ? 
                                '<span class="badge bg-secondary">Not Available</span>' : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async requestTVShow(tvShowId) {
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/${tvShowId}/request_tv_show/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });

            if (response.ok) {
                alert('TV show requested successfully!');
                this.loadTVShowsSection();
            } else {
                alert('Failed to request TV show. Please try again.');
            }
        } catch (error) {
            console.error('Error requesting TV show:', error);
            alert('Error requesting TV show. Please try again.');
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new MovieApp();
});