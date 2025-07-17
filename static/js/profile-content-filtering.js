// Profile-aware content filtering and interaction

class ProfileContentManager {
    constructor() {
        this.currentProfile = null;
        this.init();
    }

    init() {
        this.getCurrentProfile();
        this.setupContentInteraction();
        this.setupAccessRequestHandling();
    }

    getCurrentProfile() {
        // Get current profile from session/context
        const profileData = document.querySelector('[data-profile-context]');
        if (profileData) {
            this.currentProfile = JSON.parse(profileData.dataset.profileContext);
        }
    }

    setupContentInteraction() {
        // Override existing content click handlers for profile-aware behavior
        document.addEventListener('click', (e) => {
            const movieCard = e.target.closest('.movie-card');
            const tvShowCard = e.target.closest('.tv-show-card');
            
            if (movieCard) {
                this.handleContentClick(e, 'movie', movieCard.dataset.movieId);
            } else if (tvShowCard) {
                this.handleContentClick(e, 'tv_show', tvShowCard.dataset.tvShowId);
            }
        });
    }

    async handleContentClick(event, contentType, contentId) {
        // If not a child profile, use normal behavior
        if (!this.currentProfile || !this.currentProfile.profile_id) {
            return; // Let default handlers take over
        }

        // Prevent default behavior
        event.preventDefault();
        event.stopPropagation();

        // Check content access
        const accessResult = await this.checkContentAccess(contentType, contentId);
        
        if (accessResult.access_granted) {
            // Allow normal content viewing
            this.showContentDetails(contentType, contentId);
            this.logContentView(contentType, contentId);
        } else {
            // Show access denied modal with request option
            this.showAccessDeniedModal(contentType, contentId, accessResult);
        }
    }

    async checkContentAccess(contentType, contentId) {
        try {
            const response = await fetch(`/accounts/content-access-check/?content_type=${contentType}&content_id=${contentId}`);
            return await response.json();
        } catch (error) {
            console.error('Error checking content access:', error);
            return {
                access_granted: false,
                reason: 'error',
                message: 'Error checking access',
                can_request: false
            };
        }
    }

    showContentDetails(contentType, contentId) {
        // Show the appropriate modal based on content type
        if (contentType === 'movie') {
            // Trigger existing movie modal
            const movieCard = document.querySelector(`[data-movie-id="${contentId}"]`);
            if (movieCard) {
                movieCard.click();
            }
        } else {
            // Trigger existing TV show modal
            const tvShowCard = document.querySelector(`[data-tv-show-id="${contentId}"]`);
            if (tvShowCard) {
                tvShowCard.click();
            }
        }
    }

    async logContentView(contentType, contentId) {
        // Log content view for analytics
        try {
            await fetch('/accounts/log-content-view/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken
                },
                body: JSON.stringify({
                    content_type: contentType,
                    content_id: contentId
                })
            });
        } catch (error) {
            console.error('Error logging content view:', error);
        }
    }

    showAccessDeniedModal(contentType, contentId, accessResult) {
        // Remove existing modal if present
        const existingModal = document.getElementById('accessDeniedModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Create access denied modal
        const modal = document.createElement('div');
        modal.id = 'accessDeniedModal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Content Blocked</h2>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="access-denied-content">
                        <div class="access-denied-icon">
                            <i class="fas fa-shield-alt"></i>
                        </div>
                        <h3>Access Restricted</h3>
                        <p class="access-reason">${accessResult.message}</p>
                        
                        ${accessResult.can_request ? `
                            <div class="request-section">
                                <h4>Request Access</h4>
                                <p>You can ask your parent to approve access to this content.</p>
                                <div class="form-group">
                                    <label for="requestMessage">Message (optional)</label>
                                    <textarea id="requestMessage" class="form-control" rows="3" placeholder="Why would you like to watch this?"></textarea>
                                </div>
                                <div class="form-actions">
                                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                                    <button class="btn btn-primary" onclick="profileContentManager.submitAccessRequest('${contentType}', '${contentId}')">
                                        <i class="fas fa-paper-plane"></i> Send Request
                                    </button>
                                </div>
                            </div>
                        ` : `
                            <div class="no-request-section">
                                <p>This content cannot be requested. Please ask your parent directly.</p>
                                <button class="btn btn-primary" onclick="this.closest('.modal').remove()">OK</button>
                            </div>
                        `}
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.style.display = 'flex';
    }

    async submitAccessRequest(contentType, contentId) {
        const message = document.getElementById('requestMessage').value;
        
        try {
            const response = await fetch('/accounts/request-content-access/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken
                },
                body: JSON.stringify({
                    content_type: contentType,
                    content_id: contentId,
                    message: message
                })
            });

            const result = await response.json();

            if (result.success) {
                // Show success message
                this.showRequestSuccessModal(result.request_id);
            } else {
                // Show error message
                this.showToast(result.error || 'Failed to submit request', 'error');
            }
        } catch (error) {
            console.error('Error submitting access request:', error);
            this.showToast('Error submitting request', 'error');
        }

        // Close the access denied modal
        document.getElementById('accessDeniedModal').remove();
    }

    showRequestSuccessModal(requestId) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Request Sent!</h2>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="success-content">
                        <div class="success-icon">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <h3>Your request has been sent to your parent</h3>
                        <p>You'll be notified when they respond to your request.</p>
                        <div class="request-id">
                            <small>Request ID: ${requestId}</small>
                        </div>
                        <button class="btn btn-primary" onclick="this.closest('.modal').remove()">OK</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.style.display = 'flex';
    }

    setupAccessRequestHandling() {
        // Handle access request buttons on existing content
        document.addEventListener('click', (e) => {
            if (e.target.closest('.request-access-btn')) {
                const btn = e.target.closest('.request-access-btn');
                const contentType = btn.dataset.contentType;
                const contentId = btn.dataset.contentId;
                
                this.showAccessRequestModal(contentType, contentId);
            }
        });
    }

    showAccessRequestModal(contentType, contentId) {
        // Show request modal for content that's already known to be blocked
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Request Access</h2>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="request-form">
                        <p>Ask your parent to approve access to this content.</p>
                        <div class="form-group">
                            <label for="requestMessage">Message (optional)</label>
                            <textarea id="requestMessage" class="form-control" rows="3" placeholder="Why would you like to watch this?"></textarea>
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                            <button class="btn btn-primary" onclick="profileContentManager.submitAccessRequest('${contentType}', '${contentId}')">
                                <i class="fas fa-paper-plane"></i> Send Request
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.style.display = 'flex';
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Method to update content display based on profile
    updateContentDisplay() {
        if (!this.currentProfile || !this.currentProfile.profile_id) {
            // Parent view - show all content
            return;
        }

        // Child profile view - add visual indicators
        this.addProfileIndicators();
        this.addRatingBadges();
    }

    addProfileIndicators() {
        // Add profile indicator to header
        const header = document.querySelector('.header');
        if (header && !header.querySelector('.profile-indicator')) {
            const indicator = document.createElement('div');
            indicator.className = 'profile-indicator';
            indicator.innerHTML = `
                <i class="fas fa-child"></i>
                <span>Viewing as ${this.currentProfile.profile_name}</span>
            `;
            header.appendChild(indicator);
        }
    }

    addRatingBadges() {
        // Add rating badges to content cards
        const movieCards = document.querySelectorAll('.movie-card');
        const tvShowCards = document.querySelectorAll('.tv-show-card');

        movieCards.forEach(card => {
            const rating = card.dataset.rating;
            if (rating) {
                this.addRatingBadge(card, rating, 'movie');
            }
        });

        tvShowCards.forEach(card => {
            const rating = card.dataset.rating;
            if (rating) {
                this.addRatingBadge(card, rating, 'tv');
            }
        });
    }

    addRatingBadge(card, rating, type) {
        if (card.querySelector('.rating-badge')) {
            return; // Already has badge
        }

        const badge = document.createElement('div');
        badge.className = 'rating-badge';
        badge.textContent = rating;
        
        // Add color based on rating appropriateness
        const isAppropriate = this.isRatingAppropriate(rating, type);
        badge.classList.add(isAppropriate ? 'appropriate' : 'restricted');
        
        card.appendChild(badge);
    }

    isRatingAppropriate(rating, type) {
        if (!this.currentProfile || !this.currentProfile.profile_id) {
            return true; // Parent view
        }

        const maxRating = type === 'movie' ? 
            this.currentProfile.max_movie_rating : 
            this.currentProfile.max_tv_rating;

        if (type === 'movie') {
            const hierarchy = ['G', 'PG', 'PG-13', 'R', 'NC-17'];
            const currentIndex = hierarchy.indexOf(rating);
            const maxIndex = hierarchy.indexOf(maxRating);
            return currentIndex <= maxIndex;
        } else {
            const hierarchy = ['TV-Y', 'TV-Y7', 'TV-G', 'TV-PG', 'TV-14', 'TV-MA'];
            const currentIndex = hierarchy.indexOf(rating);
            const maxIndex = hierarchy.indexOf(maxRating);
            return currentIndex <= maxIndex;
        }
    }
}

// Initialize profile content manager
let profileContentManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        profileContentManager = new ProfileContentManager();
    });
} else {
    profileContentManager = new ProfileContentManager();
}

// Add CSS for profile-aware features
const profileStyles = `
    .profile-indicator {
        position: fixed;
        top: 80px;
        right: 2rem;
        background: rgba(var(--accent-color-rgb), 0.1);
        border: 1px solid var(--accent-color);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        z-index: 999;
        font-size: 0.9rem;
        color: var(--accent-color);
    }

    .rating-badge {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        z-index: 2;
    }

    .rating-badge.appropriate {
        border: 1px solid #22c55e;
    }

    .rating-badge.restricted {
        border: 1px solid #ef4444;
    }

    .access-denied-content {
        text-align: center;
        padding: 2rem;
    }

    .access-denied-icon {
        font-size: 4rem;
        color: var(--accent-color);
        margin-bottom: 1rem;
        opacity: 0.3;
    }

    .success-content {
        text-align: center;
        padding: 2rem;
    }

    .success-icon {
        font-size: 4rem;
        color: #22c55e;
        margin-bottom: 1rem;
    }

    .request-section {
        background: var(--bg-secondary);
        padding: 1.5rem;
        border-radius: 8px;
        margin-top: 1.5rem;
    }

    .request-id {
        margin-top: 1rem;
        color: var(--text-secondary);
    }

    .no-request-section {
        margin-top: 1.5rem;
    }

    .request-access-btn {
        background: var(--accent-color);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }

    .request-access-btn:hover {
        background: var(--accent-hover);
    }

    .movie-card.restricted,
    .tv-show-card.restricted {
        opacity: 0.6;
        position: relative;
    }

    .movie-card.restricted::after,
    .tv-show-card.restricted::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(239, 68, 68, 0.1);
        border: 2px solid #ef4444;
        border-radius: 8px;
    }
`;

// Add styles to page
const profileStyleSheet = document.createElement('style');
profileStyleSheet.textContent = profileStyles;
document.head.appendChild(profileStyleSheet);