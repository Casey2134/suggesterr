// Recommendations and AI-related functionality
class RecommendationsModule {
    constructor(app) {
        this.app = app;
    }

    // AI recommendations loading functions
    async loadAIRecommendations() {
        const container = document.getElementById('aiRecommendations');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/movies/ai_recommendations/`);
            const data = await response.json();
            this.app.movies.renderMoviesWithAI(data, 'aiRecommendations');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading AI recommendations:', error);
        }
    }

    async loadAITVRecommendations() {
        const container = document.getElementById('aiTVRecommendations');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/tv-shows/ai_recommendations/`);
            const data = await response.json();
            this.app.tvShows.renderTVShowsWithAI(data, 'aiTVRecommendations');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading AI TV recommendations:', error);
        }
    }

    async loadPersonalizedRecommendations() {
        const container = document.getElementById('personalizedRecommendations');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/movies/ai_recommendations/`);
            const data = await response.json();
            this.app.movies.renderMoviesWithAI(data, 'personalizedRecommendations');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading personalized recommendations:', error);
        }
    }

    async loadPersonalizedTVRecommendations() {
        const container = document.getElementById('personalizedTVRecommendations');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/tv-shows/ai_recommendations/`);
            const data = await response.json();
            this.app.tvShows.renderTVShowsWithAI(data, 'personalizedTVRecommendations');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading personalized TV recommendations:', error);
        }
    }

    async loadGenreSections() {
        const genreSectionsContainer = document.getElementById('genre-sections');
        if (!genreSectionsContainer) return; // Skip if container doesn't exist
        
        try {
            const genresResponse = await fetch(`${this.app.apiBase}/genres/`);
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
                this.app.movies.loadGenreMovies(genre.id);
            }
        } catch (error) {
            console.error('Error loading genre sections:', error);
        }
    }

    // Enhanced AI recommendation functions with mood support
    async loadAIRecommendationsSection() {
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
            if (!container) return;
            
            container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            
            const response = await fetch(`${this.app.apiBase}/movies/mood_recommendations/?mood=${mood}`);
            const movies = await response.json();
            
            if (movies && movies.length > 0) {
                this.app.movies.renderMoviesWithAI(movies, 'aiRecommendations');
            } else {
                container.innerHTML = '<p>No recommendations available for this mood.</p>';
            }
        } catch (error) {
            console.error('Error loading mood recommendations:', error);
            const container = document.getElementById('aiRecommendations');
            if (container) {
                container.innerHTML = '<p>Error loading recommendations.</p>';
            }
        }
    }

    async loadPersonalizedMovieRecommendations() {
        try {
            const container = document.getElementById('personalizedRecommendations');
            if (!container) return;
            
            container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            
            const response = await fetch(`${this.app.apiBase}/movies/ai_recommendations/`);
            const movies = await response.json();
            
            if (movies && movies.length > 0) {
                this.app.movies.renderMoviesWithAI(movies, 'personalizedRecommendations');
            } else {
                container.innerHTML = '<p>No personalized recommendations available.</p>';
            }
        } catch (error) {
            console.error('Error loading personalized recommendations:', error);
            const container = document.getElementById('personalizedRecommendations');
            if (container) {
                container.innerHTML = '<p>Error loading recommendations.</p>';
            }
        }
    }

    async loadTVMoodRecommendations(mood) {
        try {
            const container = document.getElementById('aiTVRecommendations');
            if (!container) return;
            
            container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            
            const response = await fetch(`${this.app.apiBase}/tv-shows/mood_recommendations/?mood=${mood}`);
            const tvShows = await response.json();
            
            if (tvShows && tvShows.length > 0) {
                this.app.tvShows.renderTVShowsWithAI(tvShows, 'aiTVRecommendations');
            } else {
                container.innerHTML = '<p>No TV show recommendations available for this mood.</p>';
            }
        } catch (error) {
            console.error('Error loading TV show mood recommendations:', error);
            const container = document.getElementById('aiTVRecommendations');
            if (container) {
                container.innerHTML = '<p>Error loading TV show recommendations.</p>';
            }
        }
    }

    async loadPersonalizedTVShowRecommendations() {
        try {
            const container = document.getElementById('personalizedTVRecommendations');
            if (!container) return;
            
            container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            
            const response = await fetch(`${this.app.apiBase}/tv-shows/ai_recommendations/`);
            const tvShows = await response.json();
            
            if (tvShows && tvShows.length > 0) {
                this.app.tvShows.renderTVShowsWithAI(tvShows, 'personalizedTVRecommendations');
            } else {
                container.innerHTML = '<p>No personalized TV show recommendations available.</p>';
            }
        } catch (error) {
            console.error('Error loading personalized TV show recommendations:', error);
            const container = document.getElementById('personalizedTVRecommendations');
            if (container) {
                container.innerHTML = '<p>Error loading TV show recommendations.</p>';
            }
        }
    }



    // Similar movies/shows functionality
    async loadSimilarMovies(movieId) {
        try {
            const response = await fetch(`${this.app.apiBase}/movies/similar_movies/?movie_id=${movieId}`);
            const movies = await response.json();
            
            const container = document.getElementById('similarMovies');
            if (container && movies && movies.length > 0) {
                this.app.movies.renderMovies({ results: movies }, 'similarMovies');
            }
        } catch (error) {
            console.error('Error loading similar movies:', error);
        }
    }

    async loadSimilarTVShows(tvShowId) {
        try {
            const response = await fetch(`${this.app.apiBase}/tv-shows/similar_tv_shows/?tv_show_id=${tvShowId}`);
            const tvShows = await response.json();
            
            const container = document.getElementById('similarTVShows');
            if (container && tvShows && tvShows.length > 0) {
                this.app.tvShows.renderTVShows({ results: tvShows }, 'similarTVShows');
            }
        } catch (error) {
            console.error('Error loading similar TV shows:', error);
        }
    }

    // Generate new recommendations
    async generateRecommendations() {
        if (!this.app.isAuthenticated) {
            this.app.theme.showToast('Please log in to generate personalized recommendations', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.app.apiBase}/recommendations/generate/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.app.getCookie('csrftoken')
                }
            });

            if (response.ok) {
                this.app.theme.showToast('New recommendations generated!', 'success');
                // Refresh recommendations
                this.refreshAIRecommendations();
            } else {
                throw new Error('Failed to generate recommendations');
            }
        } catch (error) {
            console.error('Error generating recommendations:', error);
            this.app.theme.showToast('Failed to generate recommendations', 'error');
        }
    }
}