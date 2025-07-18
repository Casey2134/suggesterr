// Main SuggesterrApp class - Core functionality only
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
        
        // Store request IDs
        this.currentRequestMovieId = null;
        this.currentRequestTVShowId = null;
        
        // Initialize modules
        this.movies = new MovieModule(this);
        this.tvShows = new TVShowModule(this);
        this.auth = new AuthModule(this);
        this.theme = new ThemeUIModule(this);
        this.recommendations = new RecommendationsModule(this);
        
        this.init();
    }

    async init() {
        this.theme.applyTheme(this.currentTheme);
        this.theme.updateThemeIcon();
        this.setupEventListeners();
        
        // Check if we're on an auth page (login, register, etc.)
        const currentPath = window.location.pathname;
        const authPages = ['/accounts/login/', '/accounts/register/', '/accounts/logout/'];
        
        if (authPages.includes(currentPath)) {
            // Don't check auth or redirect on auth pages
            console.log('On auth page, skipping auth check');
            return;
        }
        
        // For non-auth pages, check if we're authenticated
        await this.auth.checkAuthState();
        
        // If authenticated, just load the initial data
        if (this.isAuthenticated) {
            this.loadInitialData();
            this.theme.checkSmartOnboarding();
        }
        // If not authenticated and not on an auth page, redirect to login
        else if (!this.isAuthenticated) {
            this.auth.showLoginPage();
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

        // Global search functionality
        this.initializeGlobalSearch();

        // Infinite scroll - vertical scroll for full page sections
        window.addEventListener('scroll', () => {
            if (this.currentSection === 'movies' && window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
                this.movies.loadMoreMovies();
            }
        });

        // Horizontal infinite scroll for movie rows - set up after DOM loads
        setTimeout(() => this.setupHorizontalInfiniteScroll(), 1000);
        
        // Also setup on window resize
        window.addEventListener('resize', () => {
            setTimeout(() => this.setupHorizontalInfiniteScroll(), 100);
        });

        // Modal close on background click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.theme.closeModals();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + D for theme toggle
            if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
                e.preventDefault();
                this.theme.toggleTheme();
            }
        });
    }

    async loadInitialData() {
        const loadTasks = [];
        
        // Load content based on what containers exist on the page
        if (document.getElementById('popularMovies')) {
            loadTasks.push(this.movies.loadPopularMovies());
        }
        
        if (document.getElementById('topRatedMovies')) {
            loadTasks.push(this.movies.loadTopRatedMovies());
        }
        
        if (document.getElementById('popularTVShows')) {
            loadTasks.push(this.tvShows.loadPopularTVShows());
        }
        
        if (document.getElementById('topRatedTVShows')) {
            loadTasks.push(this.tvShows.loadTopRatedTVShows());
        }
        
        if (document.getElementById('recentlyAddedMovies')) {
            loadTasks.push(this.movies.loadRecentlyAddedMovies());
        }
        
        if (document.getElementById('genre-sections')) {
            loadTasks.push(this.recommendations.loadGenreSections());
        }
        
        // Load page-specific containers
        if (document.getElementById('moviesPopular')) {
            loadTasks.push(this.movies.loadMoviesPopular());
        }
        
        if (document.getElementById('moviesTopRated')) {
            loadTasks.push(this.movies.loadMoviesTopRated());
        }
        
        if (document.getElementById('moviesNowPlaying')) {
            loadTasks.push(this.movies.loadMoviesNowPlaying());
        }
        
        if (document.getElementById('moviesUpcoming')) {
            loadTasks.push(this.movies.loadMoviesUpcoming());
        }
        
        if (document.getElementById('tvShowsPopular')) {
            loadTasks.push(this.tvShows.loadTVShowsPopular());
        }
        
        if (document.getElementById('tvShowsTopRated')) {
            loadTasks.push(this.tvShows.loadTVShowsTopRated());
        }
        
        if (document.getElementById('tvShowsAiringToday')) {
            loadTasks.push(this.tvShows.loadTVShowsAiringToday());
        }
        
        if (document.getElementById('tvShowsOnTheAir')) {
            loadTasks.push(this.tvShows.loadTVShowsOnTheAir());
        }
        
        // AI Recommendations
        if (document.getElementById('aiRecommendations')) {
            loadTasks.push(this.recommendations.loadAIRecommendations());
        }
        
        if (document.getElementById('personalizedRecommendations')) {
            loadTasks.push(this.recommendations.loadPersonalizedRecommendations());
        }
        
        if (document.getElementById('aiTVRecommendations')) {
            loadTasks.push(this.recommendations.loadAITVRecommendations());
        }
        
        if (document.getElementById('personalizedTVRecommendations')) {
            loadTasks.push(this.recommendations.loadPersonalizedTVRecommendations());
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
        this.theme.showLoadingIndicator(containerId);
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
                    this.tvShows.appendTVShows(contentArray, containerId);
                } else {
                    this.movies.appendMovies(contentArray, containerId);
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
            this.theme.hideLoadingIndicator(containerId);
        }
    }

    // Delegate methods to modules
    navigateToSection(section) {
        return this.theme.navigateToSection(section);
    }

    showToast(message, type) {
        return this.theme.showToast(message, type);
    }

    closeModals() {
        return this.theme.closeModals();
    }

    markNotInterested(tmdbId, contentType) {
        return this.auth.markNotInterested(tmdbId, contentType);
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

    // Legacy methods for backward compatibility
    async showMovieRequestModal(movieId) {
        return this.movies.showMovieRequestModal(movieId);
    }

    async showTVRequestModal(tvShowId) {
        return this.tvShows.showTVRequestModal(tvShowId);
    }

    async submitMovieRequest() {
        return this.movies.submitMovieRequest();
    }

    async submitTVRequest() {
        return this.tvShows.submitTVRequest();
    }

    closeRequestModal() {
        return this.movies.closeRequestModal();
    }

    closeTVRequestModal() {
        return this.tvShows.closeTVRequestModal();
    }

    closeMovieModal() {
        return this.theme.closeMovieModal();
    }

    closeTVShowModal() {
        document.getElementById('tvShowModal')?.classList.remove('active');
    }

    showOnboarding() {
        return this.theme.showOnboarding();
    }

    closeOnboarding() {
        return this.theme.closeOnboarding();
    }

    nextStep() {
        return this.theme.nextStep();
    }

    prevStep() {
        return this.theme.prevStep();
    }

    async completeOnboarding() {
        return this.theme.completeOnboarding();
    }

    async saveSettings() {
        return this.theme.saveSettings();
    }

    async loadSettingsPage() {
        return this.theme.loadSettingsPage();
    }

    // Connection testing (keep in main app since it's specific functionality)
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
        // Create a simple modal to show results (without Bootstrap dependency)
        const modalHtml = `
            <div class="modal active" id="testResultsModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>${title}</h2>
                        <button type="button" class="modal-close" onclick="this.closest('.modal').remove()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        ${content}
                        <div class="step-actions" style="margin-top: 1.5rem;">
                            <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
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
        
        // Add click outside to close functionality
        const modal = document.getElementById('testResultsModal');
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    // Global search functionality
    initializeGlobalSearch() {
        const searchInput = document.getElementById('searchInput');
        const searchSuggestions = document.getElementById('searchSuggestions');
        
        if (!searchInput) return;

        let searchTimeout;

        // Handle search input with debouncing for suggestions
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            clearTimeout(searchTimeout);
            
            // Hide suggestions if query is too short
            if (query.length < 2) {
                if (searchSuggestions) {
                    searchSuggestions.style.display = 'none';
                }
                return;
            }
            
            // Only show suggestions if we're not on the search page already
            if (!window.location.pathname.includes('/search/')) {
                searchTimeout = setTimeout(() => {
                    this.fetchSearchSuggestions(query);
                }, 300);
            }
        });

        // Handle Enter key for search
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const query = searchInput.value.trim();
                if (query) {
                    this.performSearch(query);
                }
            }
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (searchSuggestions && !e.target.closest('.search-box')) {
                searchSuggestions.style.display = 'none';
            }
        });
    }

    // Perform search navigation
    performSearch(query) {
        window.location.href = `/search/?q=${encodeURIComponent(query)}`;
    }

    // Fetch search suggestions
    async fetchSearchSuggestions(query) {
        const searchSuggestions = document.getElementById('searchSuggestions');
        if (!searchSuggestions) return;

        try {
            const response = await fetch(`/api/tmdb-search/?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
            
            if (!response.ok) throw new Error('Search failed');
            
            const data = await response.json();
            this.displaySearchSuggestions(data, searchSuggestions);
        } catch (error) {
            console.error('Search suggestions error:', error);
            searchSuggestions.style.display = 'none';
        }
    }

    // Display search suggestions
    displaySearchSuggestions(data, container) {
        container.innerHTML = '';

        const totalResults = data.movies.length + data.tv_shows.length;
        
        if (totalResults === 0) {
            container.style.display = 'none';
            return;
        }

        // Add movie suggestions
        data.movies.forEach(movie => {
            const item = this.createSuggestionItem(movie, 'movie');
            container.appendChild(item);
        });

        // Add TV show suggestions
        data.tv_shows.forEach(tv => {
            const item = this.createSuggestionItem(tv, 'tv');
            container.appendChild(item);
        });

        container.style.display = 'block';
    }

    // Create suggestion item element
    createSuggestionItem(item, type) {
        const div = document.createElement('div');
        div.className = 'suggestion-item';
        
        const posterUrl = item.poster_path 
            ? `https://image.tmdb.org/t/p/w92${item.poster_path}`
            : '';
        
        const year = type === 'movie' 
            ? item.release_date 
            : item.first_air_date;
        
        div.innerHTML = `
            <img src="${posterUrl}" alt="${item.title}" class="suggestion-poster" 
                 onerror="this.style.display='none'" style="${posterUrl ? '' : 'display:none'}">
            <div class="suggestion-details">
                <div class="suggestion-title">${item.title}</div>
                <div class="suggestion-meta">
                    ${type === 'movie' ? 'Movie' : 'TV Show'} 
                    ${year ? `• ${year}` : ''}
                    ${item.vote_average ? `• ★ ${item.vote_average}` : ''}
                </div>
            </div>
        `;
        
        div.addEventListener('click', () => {
            const searchSuggestions = document.getElementById('searchSuggestions');
            if (searchSuggestions) {
                searchSuggestions.style.display = 'none';
            }
            
            if (type === 'movie') {
                this.movies.showMovieDetails(item.id);
            } else {
                this.tvShows.showTVShowDetails(item.id);
            }
        });
        
        return div;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new SuggesterrApp();
});