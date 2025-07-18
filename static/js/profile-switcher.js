// Profile Switcher Component for Header

class ProfileSwitcher {
    constructor() {
        this.currentProfile = null;
        this.profiles = [];
        this.init();
    }

    async init() {
        await this.loadProfiles();
        this.renderSwitcher();
        this.attachEventListeners();
    }

    async loadProfiles() {
        try {
            const response = await fetch('/accounts/api/family/profiles/');
            if (response.ok) {
                this.profiles = await response.json();
            }
        } catch (error) {
            console.error('Error loading profiles:', error);
        }
    }

    renderSwitcher() {
        const userActions = document.querySelector('.user-actions');
        const profileSwitcher = document.createElement('div');
        profileSwitcher.className = 'profile-switcher';
        profileSwitcher.innerHTML = `
            <button class="profile-switcher-btn" id="profileSwitcherBtn">
                <i class="fas fa-user-circle"></i>
                <span class="profile-name">${this.getCurrentProfileName()}</span>
                <i class="fas fa-chevron-down"></i>
            </button>
            <div class="profile-dropdown" id="profileDropdown">
                <div class="profile-dropdown-header">
                    <h4>Who's watching?</h4>
                </div>
                <div class="profile-dropdown-list">
                    ${this.renderProfileList()}
                </div>
                <div class="profile-dropdown-footer">
                    <a href="/accounts/family-profiles/" class="manage-profiles-link">
                        <i class="fas fa-cog"></i> Manage Profiles
                    </a>
                </div>
            </div>
        `;
        
        // Insert before the search container
        const searchContainer = userActions.querySelector('.search-container');
        userActions.insertBefore(profileSwitcher, searchContainer);
    }

    renderProfileList() {
        let html = `
            <div class="profile-item ${!this.currentProfile ? 'active' : ''}" data-profile-id="0">
                <i class="fas fa-user"></i>
                <span>Parent Account</span>
            </div>
        `;
        
        this.profiles.forEach(profile => {
            const isActive = profile.id == this.currentProfile;
            html += `
                <div class="profile-item ${isActive ? 'active' : ''}" data-profile-id="${profile.id}">
                    <i class="fas fa-child"></i>
                    <span>${profile.profile_name}</span>
                    <span class="profile-age">Age ${profile.age}</span>
                </div>
            `;
        });
        
        return html;
    }

    getCurrentProfileName() {
        const activeProfileName = sessionStorage.getItem('active_profile_name');
        return activeProfileName || 'Parent Account';
    }

    attachEventListeners() {
        const btn = document.getElementById('profileSwitcherBtn');
        const dropdown = document.getElementById('profileDropdown');
        
        // Toggle dropdown
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            dropdown.classList.remove('show');
        });
        
        // Handle profile selection
        dropdown.addEventListener('click', async (e) => {
            const profileItem = e.target.closest('.profile-item');
            if (profileItem) {
                const profileId = profileItem.dataset.profileId;
                await this.switchProfile(profileId);
            }
        });
    }

    async switchProfile(profileId) {
        try {
            let response;
            if (profileId === '0') {
                // Switch back to parent account
                response = await fetch('/accounts/clear-profile/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.csrfToken
                    }
                });
            } else {
                // Switch to child profile
                response = await fetch(`/accounts/switch-profile/${profileId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.csrfToken
                    }
                });
            }
            
            if (response.ok) {
                // Reload to apply profile filters
                window.location.reload();
            }
        } catch (error) {
            console.error('Error switching profile:', error);
        }
    }
}

// Profile switcher styles
const profileSwitcherStyles = `
    .profile-switcher {
        position: relative;
        margin-right: 1rem;
    }
    
    .profile-switcher-btn {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.9rem;
    }
    
    .profile-switcher-btn:hover {
        background: var(--border-color);
        border-color: var(--accent-color);
    }
    
    .profile-switcher-btn i:first-child {
        font-size: 1.2rem;
    }
    
    .profile-switcher-btn i:last-child {
        font-size: 0.8rem;
        transition: transform 0.2s ease;
    }
    
    .profile-dropdown {
        position: absolute;
        top: calc(100% + 0.5rem);
        right: 0;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        min-width: 250px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        opacity: 0;
        visibility: hidden;
        transform: translateY(-10px);
        transition: all 0.2s ease;
        z-index: 1000;
    }
    
    .profile-dropdown.show {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
    }
    
    .profile-dropdown-header {
        padding: 1rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .profile-dropdown-header h4 {
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .profile-dropdown-list {
        padding: 0.5rem;
    }
    
    .profile-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .profile-item:hover {
        background: rgba(var(--accent-color-rgb), 0.1);
    }
    
    .profile-item.active {
        background: rgba(var(--accent-color-rgb), 0.2);
        color: var(--accent-color);
    }
    
    .profile-item i {
        font-size: 1.2rem;
        width: 24px;
        text-align: center;
    }
    
    .profile-age {
        margin-left: auto;
        font-size: 0.8rem;
        color: var(--text-secondary);
    }
    
    .profile-dropdown-footer {
        padding: 0.5rem;
        border-top: 1px solid var(--border-color);
    }
    
    .manage-profiles-link {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1rem;
        color: var(--text-primary);
        text-decoration: none;
        border-radius: 8px;
        transition: all 0.2s ease;
        font-size: 0.9rem;
    }
    
    .manage-profiles-link:hover {
        background: rgba(var(--accent-color-rgb), 0.1);
        color: var(--accent-color);
    }
    
    /* Add content request indicator */
    .content-request-badge {
        position: absolute;
        top: -8px;
        right: -8px;
        background: var(--accent-color);
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: bold;
    }
`;

// Add styles to page
const styleSheet = document.createElement('style');
styleSheet.textContent = profileSwitcherStyles;
document.head.appendChild(styleSheet);

// Initialize profile switcher when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ProfileSwitcher();
    });
} else {
    new ProfileSwitcher();
}