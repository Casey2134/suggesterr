// TV Shows page JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    loadTVShowData();
});

async function loadTVShowData() {
    try {
        // Load different TV show categories
        await Promise.all([
            loadPopularTVShows(),
            loadTopRatedTVShows(), 
            loadAiringTodayTVShows(),
            loadOnTheAirTVShows()
        ]);
    } catch (error) {
        console.error('Error loading TV show data:', error);
    }
}

async function loadPopularTVShows() {
    try {
        const response = await fetch('/api/tv-shows/popular/');
        const data = await response.json();
        renderTVShows(data, 'tvShowsPopular');
    } catch (error) {
        console.error('Error loading popular TV shows:', error);
        showError('tvShowsPopular', 'Failed to load popular TV shows');
    }
}

async function loadTopRatedTVShows() {
    try {
        const response = await fetch('/api/tv-shows/top_rated/');
        const data = await response.json();
        renderTVShows(data, 'tvShowsTopRated');
    } catch (error) {
        console.error('Error loading top rated TV shows:', error);
        showError('tvShowsTopRated', 'Failed to load top rated TV shows');
    }
}

async function loadAiringTodayTVShows() {
    try {
        const response = await fetch('/api/tv-shows/airing_today/');
        const data = await response.json();
        renderTVShows(data, 'tvShowsAiringToday');
    } catch (error) {
        console.error('Error loading airing today TV shows:', error);
        showError('tvShowsAiringToday', 'Failed to load airing today TV shows');
    }
}

async function loadOnTheAirTVShows() {
    try {
        const response = await fetch('/api/tv-shows/on_the_air/');
        const data = await response.json();
        renderTVShows(data, 'tvShowsOnTheAir');
    } catch (error) {
        console.error('Error loading on the air TV shows:', error);
        showError('tvShowsOnTheAir', 'Failed to load on the air TV shows');
    }
}

async function searchTVShows() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) return;
    
    try {
        const response = await fetch(`/api/tv-shows/search/?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        const resultsSection = document.getElementById('searchResults');
        resultsSection.style.display = 'block';
        renderTVShows(data, 'searchTVShows');
    } catch (error) {
        console.error('Error searching TV shows:', error);
        showError('searchTVShows', 'Search failed');
    }
}

function renderTVShows(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (data && data.results && data.results.length > 0) {
        container.innerHTML = '';
        data.results.forEach(tvShow => {
            const tvShowCard = createTVShowCard(tvShow);
            container.appendChild(tvShowCard);
        });
    } else {
        container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No TV shows found</p>';
    }
}

function createTVShowCard(tvShow) {
    const card = document.createElement('div');
    card.className = 'tv-show-card';
    
    const posterPath = tvShow.poster_path 
        ? `https://image.tmdb.org/t/p/w300${tvShow.poster_path}` 
        : '/static/img/no-poster.jpg';
    
    const year = tvShow.first_air_date ? new Date(tvShow.first_air_date).getFullYear() : '';
    const rating = tvShow.vote_average ? tvShow.vote_average.toFixed(1) : 'N/A';
    
    // Check if TV show is already requested
    const isRequested = tvShow.requested_on_sonarr || false;
    const requestButton = isRequested 
        ? '<button class="btn btn-success btn-sm" disabled><i class="fas fa-check"></i> Requested</button>'
        : '<button class="btn btn-primary btn-sm" onclick="requestTVShow(event, ' + tvShow.id + ')"><i class="fas fa-download"></i> Request</button>';
    
    card.innerHTML = `
        <img src="${posterPath}" alt="${tvShow.name}" class="movie-poster" 
             onerror="this.src='/static/img/no-poster.jpg'">
        <div class="tv-show-info">
            <h3 class="tv-show-title">${tvShow.name}</h3>
            <p class="tv-show-year">${year}</p>
            <div class="tv-show-rating">
                <i class="fas fa-star"></i>
                <span>${rating}</span>
            </div>
            ${isAuthenticated ? `<div class="tv-show-actions">${requestButton}</div>` : ''}
        </div>
    `;
    
    // Add click handler to show TV show details
    card.addEventListener('click', (e) => {
        // Don't show details if clicking on request button
        if (!e.target.closest('.tv-show-actions')) {
            showTVShowDetails(tvShow);
        }
    });
    
    return card;
}

function showTVShowDetails(tvShow) {
    // Show TV show modal with details
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
        
        modal.style.display = 'block';
    }
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">${message}</p>`;
    }
}

// TV show requesting functionality
async function requestTVShow(event, tvShowId) {
    event.stopPropagation(); // Prevent card click
    
    if (!isAuthenticated) {
        alert('Please log in to request TV shows');
        return;
    }
    
    try {
        // Get TV show details
        const response = await fetch(`/api/tv-shows/${tvShowId}/`);
        const tvShow = await response.json();
        
        if (!tvShow) {
            alert('TV show not found');
            return;
        }
        
        // Show request modal
        showTVShowRequestModal(tvShow);
        
    } catch (error) {
        console.error('Error requesting TV show:', error);
        alert('Failed to load TV show details');
    }
}

function showTVShowRequestModal(tvShow) {
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
    loadTVQualityProfiles();
    loadTVSeasons(tvShow.id);
    
    modal.style.display = 'block';
}

async function loadTVQualityProfiles() {
    try {
        const response = await fetch('/api/tv-shows/quality_profiles/');
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

async function loadTVSeasons(tvShowId) {
    try {
        const response = await fetch(`/api/tv-shows/${tvShowId}/seasons/`);
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
        const response = await fetch(`/api/tv-shows/${tvShowId}/request_tv_show/`, {
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

// Search on Enter key
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && e.target.id === 'searchInput') {
        searchTVShows();
    }
});