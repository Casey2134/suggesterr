class SuggesterrApp {
    constructor() {
        this.apiBase = '/api';
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        this.currentPage = 1;
        this.isLoading = false;
        this.currentStep = 1;
        this.maxSteps = 5;
        this.currentSection = 'home';
        this.currentUser = null;
        this.isAuthenticated = false;
        
        // Page tracking for infinite scroll
        this.pageTrackers = {
            popularMovies: 1,
            topRatedMovies: 1,
            recentlyAddedMovies: 1,
            moviesPopular: 1,
            moviesTopRated: 1,
            moviesNowPlaying: 1,
            moviesUpcoming: 1,
            tvShowsPopular: 1,
            tvShowsTopRated: 1,
            tvShowsAiringToday: 1,
            tvShowsOnTheAir: 1
        };
        
        // Loading state tracking
        this.loadingStates = {};
        
        // Track if we've reached the end of content for each container
        this.endOfContent = {};
        
        this.init();
    }

    async init() {
        this.applyTheme(this.currentTheme);
        this.updateThemeIcon();
        this.setupEventListeners();
        
        // Check authentication state first
        await this.checkAuthState();
        
        // Show appropriate page based on auth state
        if (this.isAuthenticated) {
            this.showDashboard();
        } else {
            this.showLoginPage();
        }
    }

    setupEventListeners() {
        // Header scroll effect
        window.addEventListener('scroll', () => {
            const header = document.getElementById('header');
            if (window.scrollY > 100) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });

        // Search functionality
        const searchInput = document.getElementById('searchInput');
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.searchMovies(e.target.value);
            }, 500);
        });

        // Infinite scroll - vertical scroll for full page sections
        window.addEventListener('scroll', () => {
            if (this.currentSection === 'movies' && window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
                this.loadMoreMovies();
            }
        });

        // Horizontal infinite scroll for movie rows - set up after DOM loads
        setTimeout(() => this.setupHorizontalInfiniteScroll(), 1000);
        
        // Also setup on window resize
        window.addEventListener('resize', () => {
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        });

        // Navigation now handled by Django URLs - no JavaScript intervention needed

        // Modal close on background click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModals();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + D for theme toggle
            if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }

    async loadInitialData() {
        const loadTasks = [];
        
        // Load content based on what containers exist on the page
        if (document.getElementById('popularMovies')) {
            loadTasks.push(this.loadPopularMovies());
        }
        
        if (document.getElementById('topRatedMovies')) {
            loadTasks.push(this.loadTopRatedMovies());
        }
        
        if (document.getElementById('popularTVShows')) {
            loadTasks.push(this.loadPopularTVShows());
        }
        
        if (document.getElementById('topRatedTVShows')) {
            loadTasks.push(this.loadTopRatedTVShows());
        }
        
        if (document.getElementById('recentlyAddedMovies')) {
            loadTasks.push(this.loadRecentlyAddedMovies());
        }
        
        if (document.getElementById('genre-sections')) {
            loadTasks.push(this.loadGenreSections());
        }
        
        // Load page-specific containers
        if (document.getElementById('moviesPopular')) {
            loadTasks.push(this.loadMoviesPopular());
        }
        
        if (document.getElementById('moviesTopRated')) {
            loadTasks.push(this.loadMoviesTopRated());
        }
        
        if (document.getElementById('moviesNowPlaying')) {
            loadTasks.push(this.loadMoviesNowPlaying());
        }
        
        if (document.getElementById('moviesUpcoming')) {
            loadTasks.push(this.loadMoviesUpcoming());
        }
        
        if (document.getElementById('tvShowsPopular')) {
            loadTasks.push(this.loadTVShowsPopular());
        }
        
        if (document.getElementById('tvShowsTopRated')) {
            loadTasks.push(this.loadTVShowsTopRated());
        }
        
        if (document.getElementById('tvShowsAiringToday')) {
            loadTasks.push(this.loadTVShowsAiringToday());
        }
        
        if (document.getElementById('tvShowsOnTheAir')) {
            loadTasks.push(this.loadTVShowsOnTheAir());
        }
        
        // AI Recommendations
        if (document.getElementById('aiRecommendations')) {
            loadTasks.push(this.loadAIRecommendations());
        }
        
        if (document.getElementById('personalizedRecommendations')) {
            loadTasks.push(this.loadPersonalizedRecommendations());
        }
        
        if (document.getElementById('aiTVRecommendations')) {
            loadTasks.push(this.loadAITVRecommendations());
        }
        
        if (document.getElementById('personalizedTVRecommendations')) {
            loadTasks.push(this.loadPersonalizedTVRecommendations());
        }
        
        // Execute all applicable loading tasks
        if (loadTasks.length > 0) {
            await Promise.all(loadTasks);
            
            // Setup infinite scroll after all content is loaded
            setTimeout(() => {
                this.setupHorizontalInfiniteScroll();
            }, 500);
        }
    }

    async loadPopularMovies() {
        const container = document.getElementById('popularMovies');
        if (!container) return; // Skip if container doesn't exist
        
        try {
            const response = await fetch(`${this.apiBase}/movies/popular/`);
            const data = await response.json();
            this.renderMovies(data, 'popularMovies');
            // Setup horizontal scroll after content loads
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading popular movies:', error);
        }
    }

    async loadTopRatedMovies() {
        const container = document.getElementById('topRatedMovies');
        if (!container) return; // Skip if container doesn't exist
        
        try {
            const response = await fetch(`${this.apiBase}/movies/top_rated/`);
            const data = await response.json();
            this.renderMovies(data, 'topRatedMovies');
            // Setup horizontal scroll after content loads
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading top rated movies:', error);
        }
    }

    async loadPopularTVShows() {
        const container = document.getElementById('popularTVShows');
        if (!container) return; // Skip if container doesn't exist
        
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/popular/`);
            const tvShows = await response.json();
            this.renderTVShows(tvShows, 'popularTVShows');
            // Setup horizontal scroll after content loads
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading popular TV shows:', error);
        }
    }

    async loadTopRatedTVShows() {
        const container = document.getElementById('topRatedTVShows');
        if (!container) return; // Skip if container doesn't exist
        
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/top_rated/`);
            const tvShows = await response.json();
            this.renderTVShows(tvShows, 'topRatedTVShows');
            // Setup horizontal scroll after content loads
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading top rated TV shows:', error);
        }
    }

    async loadRecentlyAddedMovies() {
        const container = document.getElementById('recentlyAddedMovies');
        if (!container) return; // Skip if container doesn't exist
        
        try {
            const response = await fetch(`${this.apiBase}/movies/recently_added/`);
            const movies = await response.json();
            
            if (movies && movies.length > 0) {
                this.renderMovies(movies, 'recentlyAddedMovies');
            } else {
                // Show message if no recently added content
                container.innerHTML = '<div class="no-content"><p>No recently added movies found. Configure your media server in Settings.</p></div>';
            }
            
            // Setup horizontal scroll after content loads
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading recently added movies:', error);
            // Show error message
            container.innerHTML = '<div class="no-content"><p>Unable to load recently added content. Check your media server configuration.</p></div>';
        }
    }

    // Page-specific loading functions for movies templates
    async loadMoviesPopular() {
        const container = document.getElementById('moviesPopular');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.apiBase}/movies/popular/`);
            const data = await response.json();
            this.renderMovies(data, 'moviesPopular');
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading popular movies:', error);
        }
    }

    async loadMoviesTopRated() {
        const container = document.getElementById('moviesTopRated');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.apiBase}/movies/top_rated/`);
            const data = await response.json();
            this.renderMovies(data, 'moviesTopRated');
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading top rated movies:', error);
        }
    }

    async loadMoviesNowPlaying() {
        const container = document.getElementById('moviesNowPlaying');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.apiBase}/movies/now_playing/`);
            const data = await response.json();
            this.renderMovies(data, 'moviesNowPlaying');
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading now playing movies:', error);
        }
    }

    async loadMoviesUpcoming() {
        const container = document.getElementById('moviesUpcoming');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.apiBase}/movies/upcoming/`);
            const data = await response.json();
            this.renderMovies(data, 'moviesUpcoming');
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading upcoming movies:', error);
        }
    }

    // Page-specific loading functions for TV shows templates
    async loadTVShowsPopular() {
        const container = document.getElementById('tvShowsPopular');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/popular/`);
            const data = await response.json();
            this.renderTVShows(data, 'tvShowsPopular');
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading popular TV shows:', error);
        }
    }

    async loadTVShowsTopRated() {
        const container = document.getElementById('tvShowsTopRated');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/top_rated/`);
            const data = await response.json();
            this.renderTVShows(data, 'tvShowsTopRated');
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading top rated TV shows:', error);
        }
    }

    async loadTVShowsAiringToday() {
        const container = document.getElementById('tvShowsAiringToday');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/airing_today/`);
            const data = await response.json();
            this.renderTVShows(data, 'tvShowsAiringToday');
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading airing today TV shows:', error);
        }
    }

    async loadTVShowsOnTheAir() {
        const container = document.getElementById('tvShowsOnTheAir');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/on_the_air/`);
            const data = await response.json();
            this.renderTVShows(data, 'tvShowsOnTheAir');
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading on the air TV shows:', error);
        }
    }

    // AI recommendations loading functions
    async loadAIRecommendations() {
        const container = document.getElementById('aiRecommendations');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.apiBase}/movies/ai_recommendations/`);
            const data = await response.json();
            this.renderMoviesWithAI(data, 'aiRecommendations');
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading AI recommendations:', error);
        }
    }


    async loadAITVRecommendations() {
        const container = document.getElementById('aiTVRecommendations');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/ai_recommendations/`);
            const data = await response.json();
            this.renderTVShowsWithAI(data, 'aiTVRecommendations');
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading AI TV recommendations:', error);
        }
    }

    async loadPersonalizedTVRecommendations() {
        const container = document.getElementById('personalizedTVRecommendations');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.apiBase}/tv-recommendations/`);
            const data = await response.json();
            this.renderTVShowsWithAI(data, 'personalizedTVRecommendations');
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading personalized TV recommendations:', error);
        }
    }

    async loadGenreSections() {
        const genreSectionsContainer = document.getElementById('genre-sections');
        if (!genreSectionsContainer) return; // Skip if container doesn't exist
        
        try {
            const genresResponse = await fetch(`${this.apiBase}/genres/`);
            const genres = await genresResponse.json();
            
            // Popular genres to show on home page
            const popularGenres = [
                { id: 28, name: 'Action' },
                { id: 35, name: 'Comedy' },
                { id: 18, name: 'Drama' },
                { id: 27, name: 'Horror' },
                { id: 878, name: 'Science Fiction' },
                { id: 53, name: 'Thriller' },
                { id: 10749, name: 'Romance' },
                { id: 16, name: 'Animation' }
            ];
            
            for (const genre of popularGenres) {
                const genreSection = document.createElement('section');
                genreSection.className = 'section genre-section';
                genreSection.innerHTML = `
                    <div class="section-header">
                        <h2 class="section-title">${genre.name}</h2>
                        <a href="#" class="view-all" data-genre="${genre.id}">View All</a>
                    </div>
                    <div class="movie-row" id="genre-${genre.id}">
                        <div class="loading">
                            <div class="spinner"></div>
                        </div>
                    </div>
                `;
                genreSectionsContainer.appendChild(genreSection);
                
                // Load movies for this genre
                this.loadGenreMovies(genre.id);
            }
        } catch (error) {
            console.error('Error loading genre sections:', error);
        }
    }

    async loadGenreMovies(genreId) {
        try {
            const response = await fetch(`${this.apiBase}/movies/by_genre/?genre_id=${genreId}`);
            const movies = await response.json();
            this.renderMovies(movies, `genre-${genreId}`);
        } catch (error) {
            console.error(`Error loading movies for genre ${genreId}:`, error);
        }
    }

    async loadMoreMovies() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        const currentPage = this.pageTrackers.moviesPopular || 1;
        const nextPage = currentPage + 1;
        
        try {
            const response = await fetch(`${this.apiBase}/movies/popular/?page=${nextPage}`);
            const movies = await response.json();
            
            if (movies && movies.results && movies.results.length > 0) {
                this.appendMovies(movies.results, 'moviesPopular');
                this.pageTrackers.moviesPopular = nextPage;
            }
        } catch (error) {
            console.error('Error loading more movies:', error);
        } finally {
            this.isLoading = false;
        }
    }

    async searchMovies(query) {
        if (!query.trim()) {
            this.loadInitialData();
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/movies/search/?q=${encodeURIComponent(query)}`);
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

    setupHorizontalInfiniteScroll() {
        const movieRows = document.querySelectorAll('.movie-row');
        
        movieRows.forEach(row => {
            // Remove existing listener if it exists
            if (row.infiniteScrollHandler) {
                row.removeEventListener('scroll', row.infiniteScrollHandler);
            }
            
            // Create debounced scroll handler
            row.infiniteScrollHandler = this.debounce(() => {
                const { scrollLeft, scrollWidth, clientWidth } = row;
                const scrollPercentage = (scrollLeft + clientWidth) / scrollWidth;
                const scrolledToEnd = scrollLeft + clientWidth >= scrollWidth - 20; // 20px buffer
                
                // Load more when user scrolls to 80% of the row OR near the end
                if (scrollPercentage >= 0.8 || scrolledToEnd) {
                    this.loadMoreForRow(row.id);
                }
            }, 200);
            
            row.addEventListener('scroll', row.infiniteScrollHandler);
        });
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }


    async loadMoreForRow(containerId) {
        // Check if we've reached the end of content
        if (this.endOfContent[containerId]) {
            return;
        }
        
        // Prevent duplicate requests
        if (this.loadingStates[containerId]) {
            return;
        }
        
        this.loadingStates[containerId] = true;
        this.showLoadingIndicator(containerId);
        const currentPage = this.pageTrackers[containerId] || 1;
        const nextPage = currentPage + 1;
        
        try {
            let endpoint = '';
            let isTV = false;
            
            // Map container IDs to API endpoints
            switch (containerId) {
                case 'popularMovies':
                    endpoint = 'movies/popular/';
                    break;
                case 'topRatedMovies':
                    endpoint = 'movies/top_rated/';
                    break;
                case 'recentlyAddedMovies':
                    endpoint = 'movies/recently_added/';
                    break;
                case 'moviesPopular':
                    endpoint = 'movies/popular/';
                    break;
                case 'moviesTopRated':
                    endpoint = 'movies/top_rated/';
                    break;
                case 'moviesNowPlaying':
                    endpoint = 'movies/now_playing/';
                    break;
                case 'moviesUpcoming':
                    endpoint = 'movies/upcoming/';
                    break;
                case 'popularTVShows':
                    endpoint = 'tv-shows/popular/';
                    isTV = true;
                    break;
                case 'topRatedTVShows':
                    endpoint = 'tv-shows/top_rated/';
                    isTV = true;
                    break;
                case 'tvShowsPopular':
                    endpoint = 'tv-shows/popular/';
                    isTV = true;
                    break;
                case 'tvShowsTopRated':
                    endpoint = 'tv-shows/top_rated/';
                    isTV = true;
                    break;
                case 'tvShowsAiringToday':
                    endpoint = 'tv-shows/airing_today/';
                    isTV = true;
                    break;
                case 'tvShowsOnTheAir':
                    endpoint = 'tv-shows/on_the_air/';
                    isTV = true;
                    break;
                default:
                    return; // Unknown container
            }
            
            const response = await fetch(`${this.apiBase}/${endpoint}?page=${nextPage}`);
            const data = await response.json();
            
            // Handle different response formats
            let contentArray = [];
            if (data && data.results && Array.isArray(data.results)) {
                contentArray = data.results;
            } else if (data && Array.isArray(data)) {
                contentArray = data;
            }
            
            if (contentArray.length > 0) {
                if (isTV) {
                    this.appendTVShows(contentArray, containerId);
                } else {
                    this.appendMovies(contentArray, containerId);
                }
                this.pageTrackers[containerId] = nextPage;
                
                // Check if we've reached the end based on TMDB API response
                if (data.page && data.total_pages && data.page >= data.total_pages) {
                    this.endOfContent[containerId] = true;
                }
                
                // Re-setup scroll listener for new content
                setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
            } else {
                // No more content available
                this.endOfContent[containerId] = true;
            }
        } catch (error) {
            console.error(`Error loading more content for ${containerId}:`, error);
        } finally {
            this.loadingStates[containerId] = false;
            this.hideLoadingIndicator(containerId);
        }
    }

    showLoadingIndicator(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // Check if loading indicator already exists
        if (container.querySelector('.infinite-loading')) return;
        
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'infinite-loading';
        loadingDiv.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
            flex-shrink: 0;
            width: 100px;
        `;
        loadingDiv.innerHTML = '<div class="spinner" style="width: 20px; height: 20px;"></div>';
        
        container.appendChild(loadingDiv);
    }

    hideLoadingIndicator(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const loadingIndicator = container.querySelector('.infinite-loading');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }

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
        this.hideLoadingIndicator(containerId);
    }

    appendTVShows(tvShows, containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Container not found:', containerId);
            return;
        }
        
        tvShows.forEach((tvShow, index) => {
            container.appendChild(this.createTVShowCard(tvShow, index));
        });
    }

    createMovieCard(movie) {
        const posterUrl = movie.poster_path ? 
            (movie.poster_path.startsWith('https://') ? movie.poster_path : `https://image.tmdb.org/t/p/w300${movie.poster_path}`) : 
            'https://via.placeholder.com/300x450?text=No+Poster';

        const year = movie.release_date ? new Date(movie.release_date).getFullYear() : 'Unknown';
        
        return `
            <div class="movie-card" onclick="app.showMovieDetails(${movie.id})">
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
                        <button class="action-btn" onclick="event.stopPropagation(); app.showMovieRequestModal(${movie.id})">
                            <i class="fas fa-download"></i> Request
                        </button>
                    `}
                </div>
            </div>
        `;
    }

    async showMovieDetails(movieId) {
        try {
            const response = await fetch(`${this.apiBase}/movies/${movieId}/`);
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

        return `
            <div style="display: flex; gap: 2rem; margin-bottom: 2rem;">
                <div style="flex-shrink: 0;">
                    <img src="${posterUrl}" style="width: 100%; height: 350px; object-fit: cover; border-radius: 8px;" alt="${movie.title}">
                </div>
                <div style="flex: 1;">
                    <h3>${movie.title} (${year})</h3>
                    <p><strong>Rating:</strong> ${movie.vote_average}/10 (${movie.vote_count} votes)</p>
                    <p><strong>Genres:</strong> ${genres}</p>
                    <p><strong>Runtime:</strong> ${runtime}</p>
                    <p><strong>Overview:</strong></p>
                    <p>${movie.overview || 'No overview available.'}</p>
                    
                    <div style="margin-top: 1rem;">
                        <strong>Status:</strong>
                        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                            ${movie.requested_on_radarr ? '<span class="btn btn-success">Requested</span>' : '<span class="btn btn-outline-primary">Available to Request</span>'}
                        </div>
                    </div>
                    
                    <div style="margin-top: 1rem; display: flex; gap: 1rem; flex-wrap: wrap;">
                        ${!movie.requested_on_radarr ? `
                            <button class="btn btn-primary" onclick="app.showMovieRequestModal(${movie.id})">
                                <i class="fas fa-download"></i> Request Movie
                            </button>
                        ` : ''}
                        ${this.isAuthenticated ? `
                            <button class="btn btn-danger" onclick="app.markNotInterested(${movie.id || movie.tmdb_id}, 'movie')" style="background: #dc3545; border-color: #dc3545;">
                                <i class="fas fa-times"></i> Not Interested
                            </button>
                        ` : ''}
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
                alert('Movie requested successfully! It will be downloaded automatically.');
                this.loadInitialData(); // Refresh the movie data
            } else {
                alert('Failed to request movie. Please check your Radarr configuration.');
            }
        } catch (error) {
            console.error('Error requesting movie:', error);
            alert('Error requesting movie. Please try again.');
        }
    }

    async markNotInterested(tmdbId, contentType) {
        if (!this.isAuthenticated) {
            this.showToast('Please log in to mark items as not interested', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/negative-feedback/mark_not_interested/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    tmdb_id: tmdbId,
                    content_type: contentType,
                    reason: 'not_interested'
                })
            });

            if (response.ok) {
                // Close the modal
                document.getElementById('movieModal').classList.remove('active');
                
                // Show success message
                this.showToast(`Marked ${contentType} as not interested`, 'success');
                
                // Refresh the current section to hide the item
                if (this.currentSection === 'movies') {
                    this.loadInitialData();
                } else if (this.currentSection === 'tv-shows') {
                    this.showSection('tv-shows');
                }
            } else {
                throw new Error('Failed to mark as not interested');
            }
        } catch (error) {
            console.error('Error marking as not interested:', error);
            this.showToast('Failed to mark as not interested', 'error');
        }
    }

    // New Request Modal Methods
    async showMovieRequestModal(movieId) {
        console.log('showMovieRequestModal called with movieId:', movieId);
        try {
            // Get movie details
            const response = await fetch(`${this.apiBase}/movies/${movieId}/`);
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
            this.currentRequestMovieId = movieId;
            
            // Show the modal
            document.getElementById('movieRequestModal').style.display = 'block';
            
        } catch (error) {
            console.error('Error loading movie for request:', error);
            alert('Error loading movie details');
        }
    }
    
    async loadQualityProfiles() {
        try {
            const response = await fetch(`${this.apiBase}/movies/quality_profiles/`, {
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
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
        this.currentRequestMovieId = null;
    }
    
    async submitMovieRequest() {
        if (!this.currentRequestMovieId) {
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
            
            const response = await fetch(`${this.apiBase}/movies/${this.currentRequestMovieId}/request_movie/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(requestData)
            });
            
            if (response.ok) {
                this.closeRequestModal();
                this.showToast('Movie requested successfully! It will be downloaded automatically.', 'success');
                this.loadInitialData(); // Refresh the movie data
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to request movie');
            }
        } catch (error) {
            console.error('Error requesting movie:', error);
            this.showToast('Error requesting movie: ' + error.message, 'error');
        } finally {
            const submitBtn = document.getElementById('submitRequestBtn');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-download"></i> Request Movie';
        }
    }

    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#007bff'};
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            font-weight: 500;
            z-index: 9999;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    // Onboarding functionality
    showOnboarding() {
        document.getElementById('onboardingModal').classList.add('active');
        this.loadExistingSettings();
    }

    closeOnboarding() {
        document.getElementById('onboardingModal').classList.remove('active');
        
        // Mark onboarding as completed/skipped
        localStorage.setItem('onboardingCompleted', 'true');
    }

    nextStep() {
        if (this.currentStep < this.maxSteps) {
            document.getElementById(`step${this.currentStep}`).classList.remove('active');
            this.currentStep++;
            document.getElementById(`step${this.currentStep}`).classList.add('active');
        }
    }

    prevStep() {
        if (this.currentStep > 1) {
            document.getElementById(`step${this.currentStep}`).classList.remove('active');
            this.currentStep--;
            document.getElementById(`step${this.currentStep}`).classList.add('active');
        }
    }

    async completeOnboarding() {
        // Gather all the onboarding data
        const settings = {
            radarr_url: document.getElementById('radarrUrl').value,
            radarr_api_key: document.getElementById('radarrApiKey').value,
            sonarr_url: document.getElementById('sonarrUrl').value,
            sonarr_api_key: document.getElementById('sonarrApiKey').value,
            server_type: document.getElementById('serverType').value,
            server_url: document.getElementById('serverUrl').value,
            server_api_key: document.getElementById('serverApiKey').value
        };

        // Save to localStorage for backward compatibility
        localStorage.setItem('suggesterr_settings', JSON.stringify(settings));
        
        // Save to backend if user is authenticated
        if (this.isAuthenticated) {
            try {
                const response = await fetch(`${this.apiBase}/settings/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify(settings)
                });

                if (response.ok) {
                    console.log('Settings saved to backend successfully');
                } else {
                    console.error('Failed to save settings to backend');
                }
            } catch (error) {
                console.error('Error saving settings to backend:', error);
            }
        }
        
        this.closeOnboarding();
        localStorage.setItem('onboardingCompleted', 'true');
    }

    closeMovieModal() {
        document.getElementById('movieModal').classList.remove('active');
    }

    closeModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }

    navigateToSection(section) {
        // Track current section
        this.currentSection = section;
        
        // Update active nav link (only if it exists in navigation)
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        const navLink = document.querySelector(`[data-section="${section}"]`);
        if (navLink) {
            navLink.classList.add('active');
        }

        // Helper function to hide all main sections
        const hideAllSections = () => {
            document.getElementById('popular-section').style.display = 'none';
            const recentlyAddedSection = document.getElementById('recently-added-section');
            if (recentlyAddedSection) recentlyAddedSection.style.display = 'none';
            document.getElementById('top-rated-section').style.display = 'none';
            document.getElementById('popular-tv-section').style.display = 'none';
            document.getElementById('top-rated-tv-section').style.display = 'none';
            document.getElementById('genre-sections').style.display = 'none';
            document.getElementById('movies-section').style.display = 'none';
            document.getElementById('tv-shows-section').style.display = 'none';
            document.getElementById('ai-section').style.display = 'none';
            document.getElementById('settings-section').style.display = 'none';
        };

        // Show/hide sections based on navigation
        switch (section) {
            case 'home':
                hideAllSections();
                document.getElementById('popular-section').style.display = 'block';
                document.getElementById('recently-added-section').style.display = 'block';
                document.getElementById('top-rated-section').style.display = 'block';
                document.getElementById('popular-tv-section').style.display = 'block';
                document.getElementById('top-rated-tv-section').style.display = 'block';
                document.getElementById('genre-sections').style.display = 'block';
                break;
            case 'movies':
                hideAllSections();
                document.getElementById('movies-section').style.display = 'block';
                // Load movies for the movies tab
                this.loadMoviesSection();
                break;
            case 'tv-shows':
                hideAllSections();
                document.getElementById('tv-shows-section').style.display = 'block';
                // Load TV shows for the TV shows tab
                this.loadTVShowsSection();
                break;
            case 'ai':
                hideAllSections();
                document.getElementById('ai-section').style.display = 'block';
                // Load AI recommendations
                this.loadAIRecommendations();
                break;
            case 'settings':
                hideAllSections();
                document.getElementById('settings-section').style.display = 'block';
                // Load settings data
                this.loadSettingsPage();
                break;
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
            
            const response = await fetch(`${this.apiBase}/movies/${endpoint}/`);
            const movies = await response.json();
            
            // Handle both direct arrays and TMDB API response objects
            const movieList = movies.results || movies;
            if (movieList && movieList.length > 0) {
                this.renderMovies(movies, containerId);
                // Setup horizontal scroll after content loads
                setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
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

    async loadTVShowsSection() {
        // Load all TV show categories for the TV shows tab
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
            
            // Handle both direct arrays and TMDB API response objects
            const tvShowList = tvShows.results || tvShows;
            if (tvShowList && tvShowList.length > 0) {
                this.renderTVShows(tvShows, containerId);
                // Setup horizontal scroll after content loads
                setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
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
        if (!container) {
            console.error('Container not found:', containerId);
            return;
        }
        container.innerHTML = '';
        
        // Handle both direct arrays and TMDB API response objects
        const tvShowList = tvShows.results || tvShows;
        if (!tvShowList || tvShowList.length === 0) {
            container.innerHTML = '<div class="loading"><p>No TV shows found.</p></div>';
            return;
        }
        
        tvShowList.forEach((tvShow, index) => {
            container.appendChild(this.createTVShowCard(tvShow, index));
        });
    }

    createTVShowCard(tvShow, index) {
        // Format air date - TV shows use first_air_date
        const airDate = tvShow.first_air_date ? new Date(tvShow.first_air_date).getFullYear() : 'TBA';
        
        // Format rating
        const rating = tvShow.vote_average ? tvShow.vote_average.toFixed(1) : 'N/A';
        
        // Use title field that should be consistent
        const title = tvShow.title || tvShow.name || 'Unknown Title';
        
        // Use the same structure as createMovieCard for consistency
        const posterUrl = tvShow.poster_path || 'https://via.placeholder.com/300x450?text=No+Image';
        
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.style.animationDelay = `${index * 0.1}s`;
        card.onclick = () => this.showTVShowDetails(tvShow);
        
        card.innerHTML = `
            <img src="${posterUrl}" class="movie-poster" alt="${title}" loading="lazy"
                 onerror="this.src='https://via.placeholder.com/300x450?text=No+Image'">
            <div class="movie-info">
                <h3 class="movie-title" title="${title}">${title}</h3>
                <div class="movie-meta">
                    <span class="movie-year">${airDate}</span>
                    <span class="movie-rating">
                        <i class="fas fa-star"></i>
                        ${rating}
                    </span>
                </div>
                <p class="movie-overview">${tvShow.overview || 'No overview available.'}</p>
            </div>
            <div class="movie-actions">
                ${tvShow.requested_on_sonarr ? `
                    <button class="action-btn secondary">
                        <i class="fas fa-clock"></i> Requested
                    </button>
                ` : `
                    <button class="action-btn" onclick="event.stopPropagation(); app.showTVRequestModal(${tvShow.id || tvShow.tmdb_id})">
                        <i class="fas fa-download"></i> Request
                    </button>
                `}
            </div>
        `;
        
        return card;
    }

    showTVShowDetails(tvShow) {
        // Similar to showMovieDetails but for TV shows
        const modal = document.getElementById('movieModal');
        const title = document.getElementById('movieTitle');
        const details = document.getElementById('movieDetails');
        
        const showTitle = tvShow.title || tvShow.name || 'Unknown Title';
        title.textContent = showTitle;
        
        const airDate = tvShow.first_air_date ? new Date(tvShow.first_air_date).getFullYear() : 'TBA';
        const rating = tvShow.vote_average ? tvShow.vote_average.toFixed(1) : 'N/A';
        const seasons = tvShow.number_of_seasons ? `${tvShow.number_of_seasons} season(s)` : 'Unknown';
        const episodes = tvShow.number_of_episodes ? `${tvShow.number_of_episodes} episode(s)` : 'Unknown';
        
        details.innerHTML = `
            <div class="movie-details-content">
                <div class="movie-details-poster">
                    <img src="${tvShow.poster_path || 'https://via.placeholder.com/300x450?text=No+Image'}" 
                         style="width: 100%; height: 350px; object-fit: cover; border-radius: 8px;"
                         alt="${showTitle}">
                </div>
                <div class="movie-details-info">
                    <div class="movie-details-meta">
                        <span class="detail-item">
                            <i class="fas fa-calendar"></i>
                            First Air Date: ${airDate}
                        </span>
                        <span class="detail-item">
                            <i class="fas fa-star"></i>
                            Rating: ${rating}/10
                        </span>
                        <span class="detail-item">
                            <i class="fas fa-tv"></i>
                            ${seasons}, ${episodes}
                        </span>
                        ${tvShow.status ? `<span class="detail-item">
                            <i class="fas fa-info-circle"></i>
                            Status: ${tvShow.status}
                        </span>` : ''}
                    </div>
                    <div class="movie-details-overview">
                        <h4>Overview</h4>
                        <p>${tvShow.overview || 'No overview available.'}</p>
                    </div>
                    <div class="movie-details-actions">
                        ${!tvShow.requested_on_sonarr ? `
                            <button class="btn btn-primary" onclick="app.showTVRequestModal(${tvShow.id})">
                                <i class="fas fa-download"></i> Request TV Show
                            </button>
                        ` : ''}
                        <button class="btn btn-secondary" onclick="app.addToWatchlist(${tvShow.id}, 'tv')">
                            <i class="fas fa-plus"></i>
                            Add to Watchlist
                        </button>
                        ${this.isAuthenticated ? `
                            <button class="btn btn-danger" onclick="app.markNotInterested(${tvShow.id || tvShow.tmdb_id}, 'tv')" style="background: #dc3545; border-color: #dc3545;">
                                <i class="fas fa-times"></i> Not Interested
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        modal.classList.add('active');
    }


    async loadAIRecommendations() {
        this.setupMoodButtons();
        this.loadMoodRecommendations('happy');
        this.loadPersonalizedRecommendations();
        this.loadTVMoodRecommendations('happy');
        this.loadPersonalizedTVRecommendations();
    }

    async refreshAIRecommendations() {
        // Get the current active mood
        const activeMoodBtn = document.querySelector('.mood-btn.active');
        const currentMood = activeMoodBtn ? activeMoodBtn.dataset.mood : 'happy';
        
        // Reload recommendations with current mood
        this.loadMoodRecommendations(currentMood);
        this.loadPersonalizedRecommendations();
        this.loadTVMoodRecommendations(currentMood);
        this.loadPersonalizedTVRecommendations();
    }

    setupMoodButtons() {
        const moodButtons = document.querySelectorAll('.mood-btn');
        moodButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Remove active class from all buttons
                moodButtons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                e.target.classList.add('active');
                // Load recommendations for selected mood
                const mood = e.target.dataset.mood;
                this.loadMoodRecommendations(mood);
                this.loadTVMoodRecommendations(mood);
            });
        });
    }

    async loadMoodRecommendations(mood) {
        try {
            const container = document.getElementById('aiRecommendations');
            container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            
            const response = await fetch(`${this.apiBase}/movies/mood_recommendations/?mood=${mood}`);
            const movies = await response.json();
            
            if (movies && movies.length > 0) {
                this.renderMoviesWithAI(movies, 'aiRecommendations');
            } else {
                container.innerHTML = '<p>No recommendations available for this mood.</p>';
            }
        } catch (error) {
            console.error('Error loading mood recommendations:', error);
            document.getElementById('aiRecommendations').innerHTML = '<p>Error loading recommendations.</p>';
        }
    }

    async loadPersonalizedRecommendations() {
        try {
            const container = document.getElementById('personalizedRecommendations');
            container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            
            const response = await fetch(`${this.apiBase}/movies/ai_recommendations/`);
            const movies = await response.json();
            
            if (movies && movies.length > 0) {
                this.renderMoviesWithAI(movies, 'personalizedRecommendations');
            } else {
                container.innerHTML = '<p>No personalized recommendations available.</p>';
            }
        } catch (error) {
            console.error('Error loading personalized recommendations:', error);
            document.getElementById('personalizedRecommendations').innerHTML = '<p>Error loading recommendations.</p>';
        }
    }

    async loadTVMoodRecommendations(mood) {
        try {
            const container = document.getElementById('aiTVRecommendations');
            container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            
            const response = await fetch(`${this.apiBase}/tv-shows/mood_recommendations/?mood=${mood}`);
            const tvShows = await response.json();
            
            if (tvShows && tvShows.length > 0) {
                this.renderTVShowsWithAI(tvShows, 'aiTVRecommendations');
            } else {
                container.innerHTML = '<p>No TV show recommendations available for this mood.</p>';
            }
        } catch (error) {
            console.error('Error loading TV show mood recommendations:', error);
            document.getElementById('aiTVRecommendations').innerHTML = '<p>Error loading TV show recommendations.</p>';
        }
    }

    async loadPersonalizedTVRecommendations() {
        try {
            const container = document.getElementById('personalizedTVRecommendations');
            container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            
            const response = await fetch(`${this.apiBase}/tv-shows/ai_recommendations/`);
            const tvShows = await response.json();
            
            if (tvShows && tvShows.length > 0) {
                this.renderTVShowsWithAI(tvShows, 'personalizedTVRecommendations');
            } else {
                container.innerHTML = '<p>No personalized TV show recommendations available.</p>';
            }
        } catch (error) {
            console.error('Error loading personalized TV show recommendations:', error);
            document.getElementById('personalizedTVRecommendations').innerHTML = '<p>Error loading TV show recommendations.</p>';
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

    renderTVShowsWithAI(tvShows, containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Container not found:', containerId);
            return;
        }
        container.innerHTML = '';
        
        tvShows.forEach((tvShow, index) => {
            try {
                // Create TV show card using the createTVShowCard method
                const tvShowCard = this.createTVShowCard(tvShow, index);
                
                if (!tvShowCard) {
                    console.error('Failed to create TV show card for:', tvShow.title || tvShow.name);
                    return;
                }
                
                // Add AI reason if available
                if (tvShow.ai_reason) {
                    const tvShowInfo = tvShowCard.querySelector('.movie-info');
                    if (tvShowInfo) {
                        const aiReason = document.createElement('div');
                        aiReason.className = 'ai-reason';
                        aiReason.style.cssText = 'font-size: 0.75rem; color: var(--accent-color); margin-top: 0.25rem; font-style: italic;';
                        aiReason.textContent = tvShow.ai_reason;
                        tvShowInfo.appendChild(aiReason);
                    }
                }
                
                container.appendChild(tvShowCard);
            } catch (error) {
                console.error('Error rendering TV show card:', error, tvShow);
            }
        });
    }

    applyTheme(theme) {
        document.documentElement.removeAttribute('data-theme');
        
        if (theme !== 'dark') {
            document.documentElement.setAttribute('data-theme', theme);
        }

        this.currentTheme = theme;
        localStorage.setItem('theme', theme);
    }

    toggleTheme() {
        // Cycle through themes: dark -> light -> blue -> green -> dark
        const themes = ['dark', 'light', 'blue', 'green'];
        const currentIndex = themes.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % themes.length;
        const nextTheme = themes[nextIndex];
        
        this.applyTheme(nextTheme);
        this.updateThemeIcon();
        
        // Save to backend if user is authenticated
        if (this.isAuthenticated) {
            this.saveThemePreference(nextTheme);
        }
    }

    updateThemeIcon() {
        const themeIcon = document.getElementById('themeIcon');
        const themeToggle = document.getElementById('themeToggle');
        
        if (!themeIcon || !themeToggle) return;
        
        // Update icon and tooltip based on current theme
        switch (this.currentTheme) {
            case 'dark':
                themeIcon.className = 'fas fa-sun';
                themeToggle.title = 'Switch to Light theme';
                break;
            case 'light':
                themeIcon.className = 'fas fa-palette';
                themeToggle.title = 'Switch to Blue theme';
                break;
            case 'blue':
                themeIcon.className = 'fas fa-leaf';
                themeToggle.title = 'Switch to Green theme';
                break;
            case 'green':
                themeIcon.className = 'fas fa-moon';
                themeToggle.title = 'Switch to Dark theme';
                break;
            default:
                themeIcon.className = 'fas fa-sun';
                themeToggle.title = 'Switch theme';
        }
    }

    async saveThemePreference(theme) {
        try {
            const response = await fetch(`${this.apiBase}/settings/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ theme: theme })
            });
            
            if (!response.ok) {
                console.error('Failed to save theme preference');
            }
        } catch (error) {
            console.error('Error saving theme preference:', error);
        }
    }

    async loadUserThemePreference() {
        if (!this.isAuthenticated) return;
        
        try {
            const response = await fetch(`${this.apiBase}/settings/`);
            if (response.ok) {
                const settings = await response.json();
                if (settings && settings.theme) {
                    this.applyTheme(settings.theme);
                    this.updateThemeIcon();
                }
            }
        } catch (error) {
            console.error('Error loading theme preference:', error);
        }
    }

    // Authentication Methods
    async checkAuthState() {
        try {
            const response = await fetch(`${this.apiBase}/auth/current_user/`);
            const data = await response.json();
            
            if (data.user) {
                this.currentUser = data.user;
                this.isAuthenticated = true;
            } else {
                this.currentUser = null;
                this.isAuthenticated = false;
            }
        } catch (error) {
            console.error('Error checking auth state:', error);
            this.isAuthenticated = false;
        }
    }

    showDashboard() {
        console.log('Showing dashboard for authenticated user');
        
        // Hide login page elements
        const loginPage = document.getElementById('login-page');
        if (loginPage) loginPage.style.display = 'none';
        
        // Show dashboard elements
        const dashboard = document.getElementById('dashboard');
        if (dashboard) dashboard.style.display = 'block';
        
        // Show authenticated header
        const guestActions = document.getElementById('guest-actions');
        const userActions = document.getElementById('user-actions');
        if (guestActions) guestActions.style.display = 'none';
        if (userActions) userActions.style.display = 'flex';
        
        // Set username
        const usernameDisplay = document.getElementById('username-display');
        if (usernameDisplay && this.currentUser) {
            usernameDisplay.textContent = `Welcome, ${this.currentUser.username}`;
        }
        
        // Create settings button if needed
        this.ensureSettingsButton();
        
        // Load dashboard data
        this.loadInitialData();
        this.checkSmartOnboarding();
    }

    showLoginPage() {
        console.log('Showing login page for unauthenticated user');
        
        // Hide dashboard elements
        const dashboard = document.getElementById('dashboard');
        if (dashboard) dashboard.style.display = 'none';
        
        // Show or create login page
        let loginPage = document.getElementById('login-page');
        if (!loginPage) {
            this.createLoginPage();
        } else {
            loginPage.style.display = 'block';
        }
        
        // Hide authenticated header elements
        const userActions = document.getElementById('user-actions');
        if (userActions) userActions.style.display = 'none';
    }

    showAuthenticatedUI() {
        console.log('=== DIAGNOSTIC: Before showAuthenticatedUI ===');
        this.diagnoseElements();
        
        // Header auth buttons
        this.hideElements(['guest-actions']);
        this.showElements(['user-actions']);
        
        // Set welcome message
        const usernameDisplay = document.getElementById('username-display');
        if (usernameDisplay) {
            usernameDisplay.textContent = `Welcome, ${this.currentUser.username}`;
            console.log('Set username to:', this.currentUser.username);
        }
        
        // Force create a working Settings button
        this.createWorkingSettingsButton();
        
        // Hero section buttons
        this.hideElements(['getStartedBtn', 'loginBtn', 'registerBtn']);
        
        console.log('=== DIAGNOSTIC: After showAuthenticatedUI ===');
        this.diagnoseElements();
        
        // Load user's theme preference
        this.loadUserThemePreference();
        
        console.log('Authenticated UI state set');
    }

    showGuestUI() {
        // Header auth buttons
        this.showElements(['guest-actions']);
        this.hideElements(['user-actions']);
        
        // Hero section buttons - show login/register, hide get started
        this.hideElements(['getStartedBtn']);
        this.showElements(['loginBtn', 'registerBtn'], 'inline-block');
        
        console.log('Guest UI state set');
    }

    hideElements(elementIds) {
        elementIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                const beforeDisplay = window.getComputedStyle(element).display;
                element.style.display = 'none';
                element.style.visibility = 'visible'; // Reset visibility to default
                const afterDisplay = window.getComputedStyle(element).display;
                console.log(`Hidden element: ${id} (was: ${beforeDisplay}, now: ${afterDisplay})`);
            } else {
                console.warn(`Element not found: ${id}`);
            }
        });
    }

    showElements(elementIds, displayType = 'flex') {
        elementIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                const beforeDisplay = window.getComputedStyle(element).display;
                
                // Force the style with !important and multiple approaches
                element.style.setProperty('display', displayType, 'important');
                element.style.visibility = 'visible';
                
                // Also try setting directly in case of CSS conflicts
                element.setAttribute('style', `display: ${displayType} !important; visibility: visible;`);
                
                // Force a reflow
                element.offsetHeight;
                
                const afterDisplay = window.getComputedStyle(element).display;
                console.log(`Showed element: ${id} as ${displayType} (was: ${beforeDisplay}, now: ${afterDisplay})`);
                
                // Double-check that it actually worked
                setTimeout(() => {
                    const finalDisplay = window.getComputedStyle(element).display;
                    const rect = element.getBoundingClientRect();
                    console.log(`${id} final check: display=${finalDisplay}, visible=${rect.width > 0 && rect.height > 0}`);
                }, 10);
            } else {
                console.warn(`Element not found: ${id}`);
            }
        });
    }

    diagnoseElements() {
        const elements = ['guest-actions', 'user-actions', 'loginBtn', 'registerBtn', 'settingsBtn', 'username-display'];
        console.log('🔍 Element Diagnostic:');
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                const style = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();
                console.log(`  ${id}:`, {
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    position: style.position,
                    width: rect.width,
                    height: rect.height,
                    isVisible: rect.width > 0 && rect.height > 0 && style.display !== 'none',
                    innerHTML: element.innerHTML.substring(0, 50) + (element.innerHTML.length > 50 ? '...' : '')
                });
            } else {
                console.log(`  ${id}: NOT FOUND`);
            }
        });
    }

    diagnoseSettingsButton() {
        const settingsBtn = document.getElementById('settingsBtn');
        if (!settingsBtn) {
            console.log('🔍 Settings Button: NOT FOUND');
            return;
        }

        console.log('🔍 Settings Button Deep Diagnosis:');
        const style = window.getComputedStyle(settingsBtn);
        const rect = settingsBtn.getBoundingClientRect();
        
        console.log('Settings Button Properties:', {
            padding: style.padding,
            margin: style.margin,
            border: style.border,
            fontSize: style.fontSize,
            fontFamily: style.fontFamily,
            lineHeight: style.lineHeight,
            boxSizing: style.boxSizing,
            minWidth: style.minWidth,
            minHeight: style.minHeight,
            maxWidth: style.maxWidth,
            maxHeight: style.maxHeight,
            overflow: style.overflow,
            whiteSpace: style.whiteSpace
        });

        // Check parent container
        const parent = settingsBtn.parentElement;
        if (parent) {
            const parentStyle = window.getComputedStyle(parent);
            const parentRect = parent.getBoundingClientRect();
            console.log('Parent Container:', {
                id: parent.id,
                className: parent.className,
                display: parentStyle.display,
                width: parentRect.width,
                height: parentRect.height,
                overflow: parentStyle.overflow,
                flexDirection: parentStyle.flexDirection,
                alignItems: parentStyle.alignItems,
                justifyContent: parentStyle.justifyContent
            });
        }

        // Force some styles to see if it helps
        console.log('🔧 Attempting to fix Settings button...');
        
        // Apply aggressive styling like we did for user-actions
        settingsBtn.style.setProperty('display', 'inline-block', 'important');
        settingsBtn.style.setProperty('visibility', 'visible', 'important');
        settingsBtn.style.setProperty('padding', '0.75rem 1.5rem', 'important');
        settingsBtn.style.setProperty('font-size', '0.9rem', 'important');
        settingsBtn.style.setProperty('border', 'none', 'important');
        settingsBtn.style.setProperty('border-radius', '6px', 'important');
        settingsBtn.style.setProperty('background', 'var(--bg-secondary)', 'important');
        settingsBtn.style.setProperty('color', 'var(--text-primary)', 'important');
        settingsBtn.style.setProperty('min-width', 'auto', 'important');
        settingsBtn.style.setProperty('min-height', 'auto', 'important');
        settingsBtn.style.setProperty('width', 'auto', 'important');
        settingsBtn.style.setProperty('height', 'auto', 'important');
        
        // Force reflow
        settingsBtn.offsetHeight;
        
        // Check dimensions after forcing styles
        setTimeout(() => {
            const newRect = settingsBtn.getBoundingClientRect();
            console.log('Settings button final check:', {
                width: newRect.width,
                height: newRect.height,
                isVisible: newRect.width > 0 && newRect.height > 0
            });
            
            // If still zero dimensions, try replacing the content
            if (newRect.width === 0 && newRect.height === 0) {
                console.log('🚨 Settings button still zero dimensions, trying content replacement...');
                
                // Check current content
                console.log('Current innerHTML:', settingsBtn.innerHTML);
                console.log('Current textContent:', settingsBtn.textContent);
                
                // Try replacing with simple text first
                settingsBtn.innerHTML = '⚙️ Settings';
                settingsBtn.style.setProperty('white-space', 'nowrap', 'important');
                
                // Force another reflow
                settingsBtn.offsetHeight;
                
                const testRect = settingsBtn.getBoundingClientRect();
                console.log('After text replacement:', {
                    width: testRect.width,
                    height: testRect.height,
                    isVisible: testRect.width > 0 && testRect.height > 0
                });
                
                // If that didn't work, try creating a completely new button
                if (testRect.width === 0) {
                    console.log('🔄 Creating new Settings button...');
                    const newBtn = document.createElement('button');
                    newBtn.id = 'settingsBtn';
                    newBtn.className = 'btn btn-secondary';
                    newBtn.innerHTML = '⚙️ Settings';
                    newBtn.onclick = () => window.location.href = '/accounts/settings/';
                    newBtn.style.setProperty('display', 'inline-block', 'important');
                    newBtn.style.setProperty('padding', '0.75rem 1.5rem', 'important');
                    newBtn.style.setProperty('margin', '0 0.5rem', 'important');
                    
                    // Replace the old button
                    settingsBtn.parentNode.replaceChild(newBtn, settingsBtn);
                    
                    const finalRect = newBtn.getBoundingClientRect();
                    console.log('New button dimensions:', {
                        width: finalRect.width,
                        height: finalRect.height,
                        isVisible: finalRect.width > 0 && finalRect.height > 0
                    });
                }
            }
        }, 10);
    }

    createWorkingSettingsButton() {
        console.log('🔧 Creating working Settings button...');
        
        const userActions = document.getElementById('user-actions');
        if (!userActions) {
            console.warn('user-actions container not found');
            return;
        }
        
        // Remove existing broken settings button if it exists
        const existingBtn = document.getElementById('settingsBtn');
        if (existingBtn) {
            existingBtn.remove();
        }
        
        // Create new working button
        const settingsBtn = document.createElement('button');
        settingsBtn.id = 'settingsBtn';
        settingsBtn.className = 'btn btn-secondary';
        settingsBtn.innerHTML = '⚙️ Settings';
        settingsBtn.style.cssText = `
            display: inline-block !important;
            padding: 0.75rem 1.5rem !important;
            margin: 0 0.5rem !important;
            border: none !important;
            border-radius: 6px !important;
            background: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            font-size: 0.9rem !important;
            cursor: pointer !important;
            white-space: nowrap !important;
        `;
        
        // Add click handler
        settingsBtn.onclick = () => {
            console.log('Settings clicked!');
            window.location.href = '/accounts/settings/';
        };
        
        // Insert into user-actions container
        userActions.appendChild(settingsBtn);
        
        // Verify it worked
        setTimeout(() => {
            const rect = settingsBtn.getBoundingClientRect();
            console.log('New settings button check:', {
                width: rect.width,
                height: rect.height,
                isVisible: rect.width > 0 && rect.height > 0
            });
        }, 10);
    }

    createLoginPage() {
        console.log('Creating login page');
        
        const loginPage = document.createElement('div');
        loginPage.id = 'login-page';
        loginPage.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: var(--bg-primary);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        `;
        
        loginPage.innerHTML = `
            <div style="background: var(--bg-card); padding: 3rem; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); max-width: 400px; width: 90%;">
                <div style="text-align: center; margin-bottom: 2rem;">
                    <h1 style="color: var(--accent-color); font-size: 2.5rem; margin-bottom: 0.5rem;">
                        <i class="fas fa-film"></i> Suggesterr
                    </h1>
                    <p style="color: var(--text-secondary); margin: 0;">AI-powered movie recommendations</p>
                </div>
                
                <div id="login-form">
                    <h2 style="color: var(--text-primary); margin-bottom: 1.5rem; text-align: center;">Sign In</h2>
                    <form onsubmit="return false;">
                        <div style="margin-bottom: 1rem;">
                            <input type="text" id="loginPageUsername" placeholder="Username" 
                                   style="width: 100%; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary); font-size: 1rem;">
                        </div>
                        <div style="margin-bottom: 1.5rem;">
                            <input type="password" id="loginPagePassword" placeholder="Password"
                                   style="width: 100%; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary); font-size: 1rem;">
                        </div>
                        <button type="button" onclick="app.login(); return false;" 
                                style="width: 100%; padding: 0.75rem; background: var(--accent-color); color: white; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; margin-bottom: 1rem;">
                            Sign In
                        </button>
                    </form>
                    <div style="text-align: center;">
                        <span style="color: var(--text-secondary);">Don't have an account? </span>
                        <a href="#" onclick="app.showRegisterForm()" style="color: var(--accent-color); text-decoration: none;">Sign Up</a>
                    </div>
                </div>
                
                <div id="register-form" style="display: none;">
                    <h2 style="color: var(--text-primary); margin-bottom: 1.5rem; text-align: center;">Create Account</h2>
                    <form onsubmit="return false;">
                        <div style="margin-bottom: 1rem;">
                            <input type="text" id="registerUsername" placeholder="Username"
                                   style="width: 100%; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary); font-size: 1rem;">
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <input type="email" id="registerEmail" placeholder="Email"
                                   style="width: 100%; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary); font-size: 1rem;">
                        </div>
                        <div style="margin-bottom: 1.5rem;">
                            <input type="password" id="registerPassword" placeholder="Password"
                                   style="width: 100%; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary); font-size: 1rem;">
                        </div>
                        <button type="button" onclick="app.register(); return false;"
                                style="width: 100%; padding: 0.75rem; background: var(--accent-color); color: white; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; margin-bottom: 1rem;">
                            Create Account
                        </button>
                    </form>
                    <div style="text-align: center;">
                        <span style="color: var(--text-secondary);">Already have an account? </span>
                        <a href="#" onclick="app.showLoginForm()" style="color: var(--accent-color); text-decoration: none;">Sign In</a>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(loginPage);
    }

    showLoginForm() {
        document.getElementById('login-form').style.display = 'block';
        document.getElementById('register-form').style.display = 'none';
    }

    showRegisterForm() {
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('register-form').style.display = 'block';
    }

    ensureSettingsButton() {
        const userActions = document.getElementById('user-actions');
        if (!userActions) return;
        
        // Check if settings button already exists
        let settingsBtn = document.getElementById('settingsBtn');
        if (!settingsBtn) {
            settingsBtn = document.createElement('button');
            settingsBtn.id = 'settingsBtn';
            settingsBtn.className = 'btn btn-secondary';
            settingsBtn.innerHTML = '<i class="fas fa-cog"></i> Settings';
            settingsBtn.onclick = () => window.location.href = '/accounts/settings/';
            userActions.appendChild(settingsBtn);
        }
    }

    checkSmartOnboarding() {
        if (this.isAuthenticated) {
            // For authenticated users, check if they have settings configured
            this.checkUserConfiguration();
        } else {
            // For guests, don't show onboarding unless they specifically request it
            // Only show if they've never seen it and explicitly click "Get Started"
            return;
        }
    }

    async checkUserConfiguration() {
        try {
            const response = await fetch(`${this.apiBase}/settings/`);
            if (response.ok) {
                const settings = await response.json();
                
                // Settings API returns an object, not an array
                let hasConfiguration = false;
                if (settings && typeof settings === 'object') {
                    hasConfiguration = !!(
                        settings.server_url || 
                        settings.server_type
                    );
                }
                
                // Only show onboarding if user has no configuration and hasn't skipped it
                if (!hasConfiguration && !localStorage.getItem('onboardingCompleted')) {
                    this.showOnboarding();
                }
            }
        } catch (error) {
            console.error('Error checking user configuration:', error);
        }
    }

    showAuthModal(mode) {
        const modal = document.getElementById('authModal');
        const title = document.getElementById('authModalTitle');
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');

        if (mode === 'login') {
            title.textContent = 'Login';
            loginForm.style.display = 'block';
            registerForm.style.display = 'none';
        } else {
            title.textContent = 'Create Account';
            loginForm.style.display = 'none';
            registerForm.style.display = 'block';
        }

        modal.classList.add('active');
    }

    closeAuthModal() {
        document.getElementById('authModal').classList.remove('active');
    }

    switchAuthMode(mode) {
        this.closeAuthModal();
        this.showAuthModal(mode);
    }

    async login() {
        console.log('Login function called');
        
        // Try login page elements first, then fall back to modal elements
        let usernameEl = document.getElementById('loginPageUsername');
        let passwordEl = document.getElementById('loginPagePassword');
        
        if (!usernameEl || !passwordEl) {
            // Fall back to modal elements
            usernameEl = document.getElementById('loginUsername');
            passwordEl = document.getElementById('loginPassword');
        }
        
        console.log('Form elements:', {
            usernameEl: usernameEl,
            passwordEl: passwordEl,
            usernameElValue: usernameEl ? usernameEl.value : 'element not found',
            passwordElValue: passwordEl ? passwordEl.value : 'element not found'
        });
        
        if (!usernameEl || !passwordEl) {
            alert('Login form not found. Please refresh the page.');
            return;
        }
        
        const username = usernameEl.value.trim();
        const password = passwordEl.value.trim();
        
        console.log('Trimmed values:', {
            username: username || 'empty',
            password: password ? 'has value' : 'empty'
        });

        if (!username || !password) {
            alert('Please enter both username and password');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/auth/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                console.log('Login successful:', data);
                this.currentUser = data.user;
                this.isAuthenticated = true;
                
                // Transition to dashboard
                this.showDashboard();
            } else {
                alert(data.error || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('Login error. Please try again.');
        }
    }

    async register() {
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;

        if (!username || !email || !password) {
            alert('Please fill in all fields');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/auth/register/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken
                },
                body: JSON.stringify({ username, email, password })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.currentUser = data.user;
                this.isAuthenticated = true;
                
                // Transition to dashboard and show onboarding for new users
                this.showDashboard();
                this.showOnboarding();
            } else {
                alert(data.error || 'Registration failed');
            }
        } catch (error) {
            console.error('Registration error:', error);
            alert('Registration error. Please try again.');
        }
    }

    async logout() {
        try {
            const response = await fetch(`${this.apiBase}/auth/logout/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken
                }
            });

            if (response.ok) {
                this.currentUser = null;
                this.isAuthenticated = false;
                
                // Show login page instead of reloading
                this.showLoginPage();
            }
        } catch (error) {
            console.error('Logout error:', error);
            alert('Logout error. Please try again.');
        }
    }

    getCookie(name) {
        // For CSRF token, try to get from meta tag first
        if (name === 'csrftoken') {
            const metaToken = document.querySelector('meta[name=csrf-token]');
            if (metaToken) {
                return metaToken.getAttribute('content');
            }
        }
        
        // Fallback to cookie-based lookup
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

    // Dynamic step checking - skip steps that are already configured
    async loadExistingSettings() {
        if (!this.isAuthenticated) {
            // Load from localStorage for guests
            const savedSettings = localStorage.getItem('suggesterr_settings');
            if (savedSettings) {
                const settings = JSON.parse(savedSettings);
                this.populateOnboardingFields(settings);
            }
            return;
        }

        // Load from backend for authenticated users
        try {
            const response = await fetch(`${this.apiBase}/settings/`);
            if (response.ok) {
                const settings = await response.json();
                // Settings API returns an object, not an array
                if (settings && typeof settings === 'object') {
                    this.populateOnboardingFields(settings);
                }
            }
        } catch (error) {
            console.error('Error loading existing settings:', error);
        }
    }

    populateOnboardingFields(settings) {
        // Populate form fields with existing values
        if (settings.radarr_url) document.getElementById('radarrUrl').value = settings.radarr_url;
        if (settings.radarr_api_key) document.getElementById('radarrApiKey').value = settings.radarr_api_key;
        if (settings.sonarr_url) document.getElementById('sonarrUrl').value = settings.sonarr_url;
        if (settings.sonarr_api_key) document.getElementById('sonarrApiKey').value = settings.sonarr_api_key;
        if (settings.server_type) document.getElementById('serverType').value = settings.server_type;
        if (settings.server_url) document.getElementById('serverUrl').value = settings.server_url;
        if (settings.server_api_key) document.getElementById('serverApiKey').value = settings.server_api_key;
    }

    // Settings Page Methods
    async loadSettingsPage() {
        console.log('Loading settings page, authenticated:', this.isAuthenticated);
        
        if (!this.isAuthenticated) {
            console.log('User not authenticated, redirecting to home');
            window.location.href = '/';
            return;
        }

        // Load user profile data
        if (this.currentUser) {
            document.getElementById('settingsUsername').value = this.currentUser.username || '';
            document.getElementById('settingsEmail').value = this.currentUser.email || '';
        }

        // Load current theme
        document.getElementById('settingsTheme').value = this.currentTheme;

        // Load existing settings from backend
        try {
            const response = await fetch(`${this.apiBase}/settings/`);
            if (response.ok) {
                const settings = await response.json();
                if (settings && typeof settings === 'object') {
                    // Populate form fields
                    document.getElementById('settingsRadarrUrl').value = settings.radarr_url || '';
                    document.getElementById('settingsRadarrApiKey').value = settings.radarr_api_key || '';
                    document.getElementById('settingsSonarrUrl').value = settings.sonarr_url || '';
                    document.getElementById('settingsSonarrApiKey').value = settings.sonarr_api_key || '';
                    document.getElementById('settingsServerType').value = settings.server_type || '';
                    document.getElementById('settingsServerUrl').value = settings.server_url || '';
                    document.getElementById('settingsServerApiKey').value = settings.server_api_key || '';
                    document.getElementById('settingsTheme').value = settings.theme || this.currentTheme;
                }
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }

        // Add theme change listener
        document.getElementById('settingsTheme').addEventListener('change', (e) => {
            this.applyTheme(e.target.value);
            this.updateThemeIcon();
        });
    }

    async saveSettings() {
        if (!this.isAuthenticated) {
            alert('Please log in to save settings');
            return;
        }

        const settings = {
            radarr_url: document.getElementById('settingsRadarrUrl').value,
            radarr_api_key: document.getElementById('settingsRadarrApiKey').value,
            sonarr_url: document.getElementById('settingsSonarrUrl').value,
            sonarr_api_key: document.getElementById('settingsSonarrApiKey').value,
            server_type: document.getElementById('settingsServerType').value,
            server_url: document.getElementById('settingsServerUrl').value,
            server_api_key: document.getElementById('settingsServerApiKey').value,
            theme: document.getElementById('settingsTheme').value
        };

        try {
            const response = await fetch(`${this.apiBase}/settings/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                alert('Settings saved successfully!');
                
                // Apply theme change
                this.applyTheme(settings.theme);
                this.updateThemeIcon();
            } else {
                alert('Failed to save settings. Please try again.');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            alert('Error saving settings. Please try again.');
        }
    }

    async testConnections() {
        try {
            // Show loading state
            const button = document.querySelector('button[onclick="app.testConnections()"]');
            if (button) {
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing connections...';
            }
            
            // Make API call to test connections
            const response = await fetch('/accounts/test_connections/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                }
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to test connections');
            }
            
            // Display results
            let resultsHtml = '<div class="connection-test-results">';
            
            // Radarr status
            const radarrResult = data.results.radarr;
            resultsHtml += `
                <div class="test-result ${radarrResult.status}">
                    <strong>Radarr:</strong> 
                    <span class="status-icon">${this.getStatusIcon(radarrResult.status)}</span>
                    ${radarrResult.message}
                </div>
            `;
            
            // Sonarr status
            const sonarrResult = data.results.sonarr;
            resultsHtml += `
                <div class="test-result ${sonarrResult.status}">
                    <strong>Sonarr:</strong> 
                    <span class="status-icon">${this.getStatusIcon(sonarrResult.status)}</span>
                    ${sonarrResult.message}
                </div>
            `;
            
            // Media server status
            const mediaResult = data.results.media_server;
            const serverName = mediaResult.type ? mediaResult.type.charAt(0).toUpperCase() + mediaResult.type.slice(1) : 'Media Server';
            resultsHtml += `
                <div class="test-result ${mediaResult.status}">
                    <strong>${serverName}:</strong> 
                    <span class="status-icon">${this.getStatusIcon(mediaResult.status)}</span>
                    ${mediaResult.message}
                </div>
            `;
            
            resultsHtml += '</div>';
            
            // Show results in a modal or alert
            this.showTestResultsModal('Connection Test Results', resultsHtml);
            
        } catch (error) {
            console.error('Error testing connections:', error);
            alert(`Error testing connections: ${error.message}`);
        } finally {
            // Reset button state
            const button = document.querySelector('button[onclick="app.testConnections()"]');
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-network-wired"></i> Test Connections';
            }
        }
    }
    
    getStatusIcon(status) {
        switch(status) {
            case 'success':
                return '<i class="fas fa-check-circle text-success"></i>';
            case 'error':
                return '<i class="fas fa-times-circle text-danger"></i>';
            case 'not_configured':
                return '<i class="fas fa-exclamation-circle text-warning"></i>';
            default:
                return '<i class="fas fa-question-circle text-muted"></i>';
        }
    }
    
    showTestResultsModal(title, content) {
        // Create a simple modal to show results
        const modalHtml = `
            <div class="modal fade" id="testResultsModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${content}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove any existing modal
        const existingModal = document.getElementById('testResultsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('testResultsModal'));
        modal.show();
        
        // Clean up after modal is hidden
        document.getElementById('testResultsModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }

    // TV Show Request Modal Methods
    async showTVRequestModal(tvShowId) {
        console.log('showTVRequestModal called with tvShowId:', tvShowId);
        try {
            // Get TV show details
            const response = await fetch(`${this.apiBase}/tv-shows/${tvShowId}/`);
            const tvShow = await response.json();
            
            if (!response.ok) {
                throw new Error(tvShow.error || 'Failed to get TV show details');
            }
            
            // Store the current TV show ID for submission
            this.currentRequestTVShowId = tvShowId;
            
            // Update modal content
            document.getElementById('requestTVTitle').textContent = tvShow.title || tvShow.name;
            document.getElementById('requestTVYear').textContent = `${tvShow.first_air_date ? new Date(tvShow.first_air_date).getFullYear() : 'Unknown'} • ${tvShow.number_of_seasons || 'Unknown'} Season${(tvShow.number_of_seasons || 0) !== 1 ? 's' : ''}`;
            document.getElementById('requestTVOverview').textContent = tvShow.overview || 'No description available';
            
            // Set poster
            const poster = document.getElementById('requestTVPoster');
            if (tvShow.poster_path) {
                poster.src = tvShow.poster_path;
                poster.alt = `${tvShow.title} Poster`;
            } else {
                poster.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDEyMCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMjAiIGhlaWdodD0iMTgwIiBmaWxsPSIjMzMzMzMzIi8+Cjx0ZXh0IHg9IjYwIiB5PSI5MCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNjY2NjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5ObyBJbWFnZTwvdGV4dD4KPC9zdmc+';
                poster.alt = 'No poster available';
            }
            
            // Load quality profiles and seasons
            await Promise.all([
                this.loadTVQualityProfiles(),
                this.loadTVSeasons(tvShowId)
            ]);
            
            // Show modal
            document.getElementById('tvRequestModal').style.display = 'flex';
            
        } catch (error) {
            console.error('Error showing TV request modal:', error);
            this.showToast('Failed to load TV show details', 'error');
        }
    }

    async loadTVQualityProfiles() {
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/quality_profiles/`);
            const profiles = await response.json();
            
            const select = document.getElementById('tvQualityProfile');
            select.innerHTML = '<option value="">Select quality profile...</option>';
            
            if (Array.isArray(profiles)) {
                profiles.forEach(profile => {
                    const option = document.createElement('option');
                    option.value = profile.id;
                    option.textContent = profile.name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading TV quality profiles:', error);
            const select = document.getElementById('tvQualityProfile');
            select.innerHTML = '<option value="">Error loading profiles</option>';
        }
    }

    async loadTVSeasons(tvShowId) {
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/${tvShowId}/seasons/`);
            const seasons = await response.json();
            
            const container = document.getElementById('seasonSelection');
            container.innerHTML = '';
            
            if (Array.isArray(seasons) && seasons.length > 0) {
                seasons.forEach(season => {
                    if (season.season_number === 0) return; // Skip specials
                    
                    const seasonDiv = document.createElement('div');
                    seasonDiv.className = 'season-item';
                    seasonDiv.innerHTML = `
                        <label style="display: flex; align-items: center; cursor: pointer;">
                            <input type="checkbox" class="season-checkbox" value="${season.season_number}" checked>
                            <div>
                                <h4>Season ${season.season_number}</h4>
                                <p>${season.episode_count || 0} episodes</p>
                                ${season.air_date ? `<p>Aired: ${new Date(season.air_date).getFullYear()}</p>` : ''}
                            </div>
                        </label>
                    `;
                    
                    // Add click handler to toggle checkbox
                    seasonDiv.addEventListener('click', (e) => {
                        if (e.target.type !== 'checkbox') {
                            const checkbox = seasonDiv.querySelector('input[type="checkbox"]');
                            checkbox.checked = !checkbox.checked;
                        }
                        seasonDiv.classList.toggle('selected', seasonDiv.querySelector('input[type="checkbox"]').checked);
                    });
                    
                    // Initial state
                    seasonDiv.classList.add('selected');
                    container.appendChild(seasonDiv);
                });
            } else {
                container.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">No season information available</p>';
            }
        } catch (error) {
            console.error('Error loading TV seasons:', error);
            const container = document.getElementById('seasonSelection');
            container.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">Error loading seasons</p>';
        }
    }

    closeTVRequestModal() {
        document.getElementById('tvRequestModal').style.display = 'none';
        this.currentRequestTVShowId = null;
    }

    async submitTVRequest() {
        if (!this.currentRequestTVShowId) {
            alert('No TV show selected');
            return;
        }
        
        const qualityProfileId = document.getElementById('tvQualityProfile').value;
        const searchImmediately = document.getElementById('tvSearchImmediately').checked;
        
        // Get selected seasons
        const selectedSeasons = [];
        document.querySelectorAll('.season-checkbox:checked').forEach(checkbox => {
            selectedSeasons.push(parseInt(checkbox.value));
        });
        
        if (selectedSeasons.length === 0) {
            alert('Please select at least one season');
            return;
        }
        
        const requestData = {
            quality_profile_id: qualityProfileId || null,
            seasons: selectedSeasons,
            search_immediately: searchImmediately
        };
        
        try {
            const response = await fetch(`${this.apiBase}/tv-shows/${this.currentRequestTVShowId}/request_tv_show/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(requestData)
            });
            
            if (response.ok) {
                this.closeTVRequestModal();
                this.showToast(`TV show requested successfully! ${selectedSeasons.length} season${selectedSeasons.length !== 1 ? 's' : ''} will be downloaded.`, 'success');
                this.loadInitialData(); // Refresh the data
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to request TV show');
            }
        } catch (error) {
            console.error('Error submitting TV request:', error);
            this.showToast('Failed to request TV show: ' + error.message, 'error');
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new SuggesterrApp();
});