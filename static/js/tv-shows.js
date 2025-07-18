// TV Show-related functionality
class TVShowModule {
    constructor(app) {
        this.app = app;
    }

    // TV Show loading functions
    async loadPopularTVShows() {
        const container = document.getElementById('popularTVShows');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/tv-shows/popular/`);
            const tvShows = await response.json();
            this.renderTVShows(tvShows, 'popularTVShows');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading popular TV shows:', error);
        }
    }

    async loadTopRatedTVShows() {
        const container = document.getElementById('topRatedTVShows');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/tv-shows/top_rated/`);
            const tvShows = await response.json();
            this.renderTVShows(tvShows, 'topRatedTVShows');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading top rated TV shows:', error);
        }
    }

    // Page-specific loading functions for TV shows templates
    async loadTVShowsPopular() {
        const container = document.getElementById('tvShowsPopular');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/tv-shows/popular/`);
            const data = await response.json();
            this.renderTVShows(data, 'tvShowsPopular');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading popular TV shows:', error);
        }
    }

    async loadTVShowsTopRated() {
        const container = document.getElementById('tvShowsTopRated');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/tv-shows/top_rated/`);
            const data = await response.json();
            this.renderTVShows(data, 'tvShowsTopRated');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading top rated TV shows:', error);
        }
    }

    async loadTVShowsAiringToday() {
        const container = document.getElementById('tvShowsAiringToday');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/tv-shows/airing_today/`);
            const data = await response.json();
            this.renderTVShows(data, 'tvShowsAiringToday');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading airing today TV shows:', error);
        }
    }

    async loadTVShowsOnTheAir() {
        const container = document.getElementById('tvShowsOnTheAir');
        if (!container) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/tv-shows/on_the_air/`);
            const data = await response.json();
            this.renderTVShows(data, 'tvShowsOnTheAir');
            setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
        } catch (error) {
            console.error('Error loading on the air TV shows:', error);
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
            
            const response = await fetch(`${this.app.apiBase}/tv-shows/${endpoint}/`);
            const tvShows = await response.json();
            
            // Handle both direct arrays and TMDB API response objects
            const tvShowList = tvShows.results || tvShows;
            if (tvShowList && tvShowList.length > 0) {
                this.renderTVShows(tvShows, containerId);
                // Setup horizontal scroll after content loads
                setTimeout(() => this.app.setupHorizontalInfiniteScroll(), 100);
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

    // TV Show rendering functions
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
        card.onclick = () => this.showTVShowDetails(tvShow.id || tvShow.tmdb_id);
        
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
                    <button class="action-btn" onclick="event.stopPropagation(); app.tvShows.showTVRequestModal(${tvShow.id || tvShow.tmdb_id})">
                        <i class="fas fa-download"></i> Request
                    </button>
                `}
            </div>
        `;
        
        return card;
    }

    // TV Show details and modal functions
    async showTVShowDetails(tvShowId) {
        try {
            const response = await fetch(`${this.app.apiBase}/tv-shows/${tvShowId}/`);
            const tvShow = await response.json();
            this.displayTVShowDetails(tvShow);
        } catch (error) {
            console.error('Error loading TV show details:', error);
        }
    }

    displayTVShowDetails(tvShow) {
        // Similar to showMovieDetails but for TV shows
        const modal = document.getElementById('tvShowModal');
        const title = document.getElementById('tvShowTitle');
        const details = document.getElementById('tvShowDetails');
        
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
                            <button class="btn btn-primary" onclick="app.tvShows.showTVRequestModal(${tvShow.id})">
                                <i class="fas fa-download"></i> Request TV Show
                            </button>
                        ` : '<span class="btn btn-success"><i class="fas fa-check"></i> Requested</span>'}
                        ${this.app.isAuthenticated ? `
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

    // TV Show request functions
    async showTVRequestModal(tvShowId) {
        try {
            // Get TV show details
            const response = await fetch(`${this.app.apiBase}/tv-shows/${tvShowId}/`);
            const tvShow = await response.json();
            
            if (!tvShow) {
                alert('TV show not found');
                return;
            }
            
            // Show request modal
            this.showTVShowRequestModal(tvShow);
            
        } catch (error) {
            console.error('Error requesting TV show:', error);
            alert('Failed to load TV show details');
        }
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
            const response = await fetch(`${this.app.apiBase}/tv-shows/quality_profiles/`);
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
            const response = await fetch(`${this.app.apiBase}/tv-shows/${tvShowId}/seasons/`);
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

    async submitTVRequest() {
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
            const response = await fetch(`${this.app.apiBase}/tv-shows/${tvShowId}/request_tv_show/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.app.getCookie('csrftoken')
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
                this.closeTVRequestModal();
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

    closeTVRequestModal() {
        document.getElementById('tvRequestModal').style.display = 'none';
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
}