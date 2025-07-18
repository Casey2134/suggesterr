// Movie-related functionality
class MovieModule {
    constructor(app) {
        this.app = app;
    }

    // Movie loading functions
    async loadPopularMovies() {
        const container = document.getElementById('popularMovies');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/movies/popular/`);
            const data = await response.json();
            this.renderMovies(data, 'popularMovies');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading popular movies:', error);
        }
    }

    async loadTopRatedMovies() {
        const container = document.getElementById('topRatedMovies');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/movies/top_rated/`);
            const data = await response.json();
            this.renderMovies(data, 'topRatedMovies');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading top rated movies:', error);
        }
    }

    async loadRecentlyAddedMovies() {
        const container = document.getElementById('recentlyAddedMovies');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/movies/recently_added/`);
            const movies = await response.json();
            
            if (movies && movies.length > 0) {
                this.renderMovies(movies, 'recentlyAddedMovies');
            } else {
                container.innerHTML = '<div class="no-content"><p>No recently added movies found. Configure your media server in Settings.</p></div>';
            }
            
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading recently added movies:', error);
            container.innerHTML = '<div class="no-content"><p>Unable to load recently added content. Check your media server configuration.</p></div>';
        }
    }

    // Page-specific loading functions for movies templates
    async loadMoviesPopular() {
        const container = document.getElementById('moviesPopular');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/movies/popular/`);
            const data = await response.json();
            this.renderMovies(data, 'moviesPopular');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading popular movies:', error);
        }
    }

    async loadMoviesTopRated() {
        const container = document.getElementById('moviesTopRated');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/movies/top_rated/`);
            const data = await response.json();
            this.renderMovies(data, 'moviesTopRated');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading top rated movies:', error);
        }
    }

    async loadMoviesNowPlaying() {
        const container = document.getElementById('moviesNowPlaying');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/movies/now_playing/`);
            const data = await response.json();
            this.renderMovies(data, 'moviesNowPlaying');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading now playing movies:', error);
        }
    }

    async loadMoviesUpcoming() {
        const container = document.getElementById('moviesUpcoming');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/movies/upcoming/`);
            const data = await response.json();
            this.renderMovies(data, 'moviesUpcoming');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading upcoming movies:', error);
        }
    }

    async loadGenreMovies(genreId) {
        try {
            const response = await fetch(`${this.app.apiBase}/movies/by_genre/?genre_id=${genreId}`);
            const movies = await response.json();
            this.renderMovies(movies, `genre-${genreId}`);
        } catch (error) {
            console.error(`Error loading movies for genre ${genreId}:`, error);
        }
    }

    async loadMoreMovies() {
        if (this.app.isLoading) return;
        
        this.app.isLoading = true;
        const currentPage = this.app.pageTrackers.moviesPopular || 1;
        const nextPage = currentPage + 1;
        
        try {
            const response = await fetch(`${this.app.apiBase}/movies/popular/?page=${nextPage}`);
            const movies = await response.json();
            
            if (movies && movies.results && movies.results.length > 0) {
                this.appendMovies(movies.results, 'moviesPopular');
                this.app.pageTrackers.moviesPopular = nextPage;
            }
        } catch (error) {
            console.error('Error loading more movies:', error);
        } finally {
            this.app.isLoading = false;
        }
    }

    async searchMovies(query) {
        if (!query.trim()) {
            this.app.loadInitialData();
            return;
        }

        try {
            const response = await fetch(`${this.app.apiBase}/movies/search/?q=${encodeURIComponent(query)}`);
            const movies = await response.json();
            
            // Hide other sections and show search results
            document.getElementById('popular-section').style.display = 'none';
            document.getElementById('top-rated-section').style.display = 'none';
            document.getElementById('all-movies-section').style.display = 'block';
            
            this.renderMovies(movies, 'allMovies');
        } catch (error) {
            console.error('Error searching movies:', error);
        }
    }

    async loadMoviesSection() {
        // Load all movie categories for the movies tab
        this.loadMovies('popular', 'moviesPopular');
        this.loadMovies('top_rated', 'moviesTopRated');
        this.loadMovies('now_playing', 'moviesNowPlaying');
        this.loadMovies('upcoming', 'moviesUpcoming');
    }

    async loadMovies(endpoint, containerId) {
        try {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            }
            
            const response = await fetch(`${this.app.apiBase}/movies/${endpoint}/`);
            const movies = await response.json();
            
            // Handle both direct arrays and TMDB API response objects
            const movieList = movies.results || movies;
            if (movieList && movieList.length > 0) {
                this.renderMovies(movies, containerId);
                // Setup horizontal scroll after content loads
                setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
            } else {
                if (container) {
                    container.innerHTML = '<div class="loading"><p>No movies found.</p></div>';
                }
            }
        } catch (error) {
            console.error(`Error loading ${endpoint} movies:`, error);
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = '<div class="loading"><p>Error loading movies.</p></div>';
            }
        }
    }

    // Movie rendering functions
    renderMovies(movies, containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.log('Container not found:', containerId);
            return;
        }
        
        if (!movies) {
            container.innerHTML = '<div class="loading"><p>No movies found.</p></div>';
            return;
        }

        // Handle both direct arrays and TMDB API response objects
        const movieList = movies.results || movies;
        
        if (!movieList || movieList.length === 0) {
            container.innerHTML = '<div class="loading"><p>No movies found.</p></div>';
            return;
        }

        container.innerHTML = movieList.map(movie => this.createMovieCard(movie)).join('');
    }

    appendMovies(movies, containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            return;
        }
        
        const movieCards = movies.map(movie => this.createMovieCard(movie)).join('');
        container.innerHTML += movieCards;
        
        // Remove any loading indicators
        this.app.hideLoadingIndicator(containerId);
    }

    createMovieCard(movie) {
        const posterUrl = movie.poster_path ? 
            (movie.poster_path.startsWith('https://') ? movie.poster_path : `https://image.tmdb.org/t/p/w300${movie.poster_path}`) : 
            'https://via.placeholder.com/300x450?text=No+Poster';

        const year = movie.release_date ? new Date(movie.release_date).getFullYear() : 'Unknown';
        
        return `
            <div class="movie-card" onclick="app.movies.showMovieDetails(${movie.id})">
                <img src="${posterUrl}" class="movie-poster" alt="${movie.title}">
                <div class="movie-info">
                    <h3 class="movie-title">${movie.title}</h3>
                    <div class="movie-meta">
                        <span class="movie-year">${year}</span>
                        <span class="movie-rating">
                            <i class="fas fa-star"></i> ${movie.vote_average || 'N/A'}
                        </span>
                    </div>
                    <p class="movie-overview">${movie.overview || 'No overview available.'}</p>
                </div>
                <div class="movie-actions">
                    ${movie.requested_on_radarr ? `
                        <button class="action-btn secondary">
                            <i class="fas fa-clock"></i> Requested
                        </button>
                    ` : `
                        <button class="action-btn" onclick="event.stopPropagation(); app.movies.showMovieRequestModal(${movie.id})">
                            <i class="fas fa-download"></i> Request
                        </button>
                    `}
                </div>
            </div>
        `;
    }

    // Movie details and modal functions
    async showMovieDetails(movieId) {
        try {
            const response = await fetch(`${this.app.apiBase}/movies/${movieId}/`);
            const movie = await response.json();
            
            document.getElementById('movieTitle').textContent = movie.title;
            document.getElementById('movieDetails').innerHTML = this.createMovieDetailsHTML(movie);
            document.getElementById('movieModal').classList.add('active');
        } catch (error) {
            console.error('Error loading movie details:', error);
        }
    }

    createMovieDetailsHTML(movie) {
        const posterUrl = movie.poster_path ? 
            `https://image.tmdb.org/t/p/w500${movie.poster_path}` : 
            'https://via.placeholder.com/500x750?text=No+Poster';

        const genres = movie.genres ? movie.genres.map(g => g.name).join(', ') : 'Unknown';
        const year = movie.release_date ? new Date(movie.release_date).getFullYear() : 'Unknown';
        const runtime = movie.runtime ? `${movie.runtime} minutes` : 'Unknown';
        const rating = movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A';

        return `
            <div class="movie-details-content">
                <div class="movie-details-poster">
                    <img src="${posterUrl}" 
                         style="width: 100%; height: 350px; object-fit: cover; border-radius: 8px;" 
                         alt="${movie.title}">
                </div>
                <div class="movie-details-info">
                    <div class="movie-details-meta">
                        <span class="detail-item">
                            <i class="fas fa-calendar"></i>
                            Release: ${year}
                        </span>
                        <span class="detail-item">
                            <i class="fas fa-star"></i>
                            Rating: ${rating}/10
                        </span>
                        <span class="detail-item">
                            <i class="fas fa-clock"></i>
                            Runtime: ${runtime}
                        </span>
                        <span class="detail-item">
                            <i class="fas fa-film"></i>
                            Genres: ${genres}
                        </span>
                        ${movie.status ? `<span class="detail-item">
                            <i class="fas fa-info-circle"></i>
                            Status: ${movie.status}
                        </span>` : ''}
                    </div>
                    <div class="movie-details-overview">
                        <h4>Overview</h4>
                        <p>${movie.overview || 'No overview available.'}</p>
                    </div>
                    <div class="movie-details-actions">
                        ${!movie.requested_on_radarr ? `
                            <button class="btn btn-primary" onclick="app.movies.showMovieRequestModal(${movie.id})">
                                <i class="fas fa-download"></i> Request Movie
                            </button>
                        ` : '<span class="btn btn-success"><i class="fas fa-check"></i> Requested</span>'}
                        ${this.app.isAuthenticated ? `
                            <button class="btn btn-danger" onclick="app.markNotInterested(${movie.id || movie.tmdb_id}, 'movie')" style="background: #dc3545; border-color: #dc3545;">
                                <i class="fas fa-times"></i> Not Interested
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    // Movie request functions
    async showMovieRequestModal(movieId) {
        console.log('showMovieRequestModal called with movieId:', movieId);
        try {
            // Get movie details
            const response = await fetch(`${this.app.apiBase}/movies/${movieId}/`);
            const movie = await response.json();
            
            if (!movie) {
                alert('Movie not found');
                return;
            }
            
            // Populate movie information
            document.getElementById('requestMovieTitle').textContent = movie.title;
            document.getElementById('requestMovieYear').textContent = movie.release_date ? new Date(movie.release_date).getFullYear() : 'Unknown';
            document.getElementById('requestMovieOverview').textContent = movie.overview || 'No overview available';
            
            const posterUrl = movie.poster_path ? 
                (movie.poster_path.startsWith('https://') ? movie.poster_path : `https://image.tmdb.org/t/p/w300${movie.poster_path}`) : 
                'https://via.placeholder.com/300x450?text=No+Poster';
            document.getElementById('requestMoviePoster').src = posterUrl;
            
            // Load quality profiles
            await this.loadQualityProfiles();
            
            // Store movie ID for later use
            this.app.currentRequestMovieId = movieId;
            
            // Show the modal
            document.getElementById('movieRequestModal').style.display = 'block';
            
        } catch (error) {
            console.error('Error loading movie for request:', error);
            alert('Error loading movie details');
        }
    }
    
    async loadQualityProfiles() {
        try {
            const response = await fetch(`${this.app.apiBase}/movies/quality_profiles/`, {
                headers: {
                    'X-CSRFToken': this.app.getCookie('csrftoken')
                }
            });
            
            const profiles = await response.json();
            const select = document.getElementById('qualityProfile');
            
            // Clear existing options
            select.innerHTML = '';
            
            if (profiles && profiles.length > 0) {
                profiles.forEach(profile => {
                    const option = document.createElement('option');
                    option.value = profile.id;
                    option.textContent = profile.name;
                    select.appendChild(option);
                });
                
                // Select first option by default
                select.selectedIndex = 0;
            } else {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No quality profiles available';
                select.appendChild(option);
            }
        } catch (error) {
            console.error('Error loading quality profiles:', error);
            const select = document.getElementById('qualityProfile');
            select.innerHTML = '<option value="">Error loading profiles</option>';
        }
    }
    
    closeRequestModal() {
        document.getElementById('movieRequestModal').style.display = 'none';
        this.app.currentRequestMovieId = null;
    }
    
    async submitMovieRequest() {
        if (!this.app.currentRequestMovieId) {
            alert('No movie selected');
            return;
        }
        
        const qualityProfileId = document.getElementById('qualityProfile').value;
        const searchImmediately = document.getElementById('searchImmediately').checked;
        
        try {
            const submitBtn = document.getElementById('submitRequestBtn');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Requesting...';
            
            const requestData = {};
            if (qualityProfileId) {
                requestData.quality_profile_id = qualityProfileId;
            }
            if (!searchImmediately) {
                requestData.search_immediately = false;
            }
            
            const response = await fetch(`${this.app.apiBase}/movies/${this.app.currentRequestMovieId}/request_movie/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.app.getCookie('csrftoken')
                },
                body: JSON.stringify(requestData)
            });
            
            if (response.ok) {
                this.closeRequestModal();
                this.app.showToast('Movie requested successfully! It will be downloaded automatically.', 'success');
                this.app.loadInitialData(); // Refresh the movie data
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to request movie');
            }
        } catch (error) {
            console.error('Error requesting movie:', error);
            this.app.showToast('Error requesting movie: ' + error.message, 'error');
        } finally {
            const submitBtn = document.getElementById('submitRequestBtn');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-download"></i> Request Movie';
        }
    }

    async requestMovie(movieId) {
        try {
            const response = await fetch(`${this.app.apiBase}/movies/${movieId}/request_movie/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.app.getCookie('csrftoken')
                }
            });

            if (response.ok) {
                alert('Movie requested successfully! It will be downloaded automatically.');
                this.app.loadInitialData(); // Refresh the movie data
            } else {
                alert('Failed to request movie. Please check your Radarr configuration.');
            }
        } catch (error) {
            console.error('Error requesting movie:', error);
            alert('Error requesting movie. Please try again.');
        }
    }

    renderMoviesWithAI(movies, containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Container not found:', containerId);
            return;
        }
        container.innerHTML = '';
        
        movies.forEach((movie, index) => {
            try {
                // Create a temporary container to parse the HTML string
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = this.createMovieCard(movie);
                const movieCard = tempDiv.firstElementChild;
                
                if (!movieCard) {
                    console.error('Failed to create movie card for:', movie.title);
                    return;
                }
                
                // Add AI reason if available
                if (movie.ai_reason) {
                    const movieInfo = movieCard.querySelector('.movie-info');
                    if (movieInfo) {
                        const aiReason = document.createElement('div');
                        aiReason.className = 'ai-reason';
                        aiReason.style.cssText = 'font-size: 0.75rem; color: var(--accent-color); margin-top: 0.25rem; font-style: italic;';
                        aiReason.textContent = movie.ai_reason;
                        movieInfo.appendChild(aiReason);
                    }
                }
                
                container.appendChild(movieCard);
            } catch (error) {
                console.error('Error rendering movie card:', error, movie);
            }
        });
    }
}