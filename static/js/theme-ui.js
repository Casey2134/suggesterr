// Theme and UI-related functionality
class ThemeUIModule {
    constructor(app) {
        this.app = app;
    }

    // Theme management
    applyTheme(theme) {
        document.documentElement.removeAttribute('data-theme');
        
        if (theme !== 'dark') {
            document.documentElement.setAttribute('data-theme', theme);
        }

        this.app.currentTheme = theme;
        localStorage.setItem('theme', theme);
    }

    toggleTheme() {
        // Cycle through themes: dark -> light -> blue -> green -> dark
        const themes = ['dark', 'light', 'blue', 'green'];
        const currentIndex = themes.indexOf(this.app.currentTheme);
        const nextIndex = (currentIndex + 1) % themes.length;
        const nextTheme = themes[nextIndex];
        
        this.applyTheme(nextTheme);
        this.updateThemeIcon();
        
        // Save to backend if user is authenticated
        if (this.app.isAuthenticated) {
            this.saveThemePreference(nextTheme);
        }
    }

    updateThemeIcon() {
        const themeIcon = document.getElementById('themeIcon');
        const themeToggle = document.getElementById('themeToggle');
        
        if (!themeIcon || !themeToggle) return;
        
        // Update icon and tooltip based on current theme
        switch (this.app.currentTheme) {
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
            const response = await fetch(`${this.app.apiBase}/settings/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.app.getCookie('csrftoken')
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
        if (!this.app.isAuthenticated) return;
        
        try {
            const response = await fetch(`${this.app.apiBase}/settings/`);
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

    // UI utility functions
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

    // Modal management
    closeMovieModal() {
        document.getElementById('movieModal').classList.remove('active');
    }

    closeModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }

    // Navigation and section management
    navigateToSection(section) {
        // Track current section
        this.app.currentSection = section;
        
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
            const sectionsToHide = [
                'popular-section', 'recently-added-section', 'top-rated-section',
                'popular-tv-section', 'top-rated-tv-section', 'genre-sections',
                'movies-section', 'tv-shows-section', 'ai-section', 'settings-section'
            ];
            
            sectionsToHide.forEach(sectionId => {
                const element = document.getElementById(sectionId);
                if (element) element.style.display = 'none';
            });
        };

        // Show/hide sections based on navigation
        switch (section) {
            case 'home':
                hideAllSections();
                this.showElements(['popular-section', 'recently-added-section', 'top-rated-section', 
                                 'popular-tv-section', 'top-rated-tv-section', 'genre-sections'], 'block');
                break;
            case 'movies':
                hideAllSections();
                this.showElements(['movies-section'], 'block');
                // Load movies for the movies tab
                this.app.movies.loadMoviesSection();
                break;
            case 'tv-shows':
                hideAllSections();
                this.showElements(['tv-shows-section'], 'block');
                // Load TV shows for the TV shows tab
                this.app.tvShows.loadTVShowsSection();
                break;
            case 'ai':
                hideAllSections();
                this.showElements(['ai-section'], 'block');
                // Load AI recommendations
                this.app.recommendations.loadAIRecommendations();
                break;
            case 'settings':
                hideAllSections();
                this.showElements(['settings-section'], 'block');
                // Load settings data
                this.loadSettingsPage();
                break;
        }
    }

    showElements(elementIds, displayType = 'flex') {
        elementIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.style.display = displayType;
            }
        });
    }

    hideElements(elementIds) {
        elementIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.style.display = 'none';
            }
        });
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
        if (this.app.currentStep < this.app.maxSteps) {
            document.getElementById(`step${this.app.currentStep}`).classList.remove('active');
            this.app.currentStep++;
            document.getElementById(`step${this.app.currentStep}`).classList.add('active');
        }
    }

    prevStep() {
        if (this.app.currentStep > 1) {
            document.getElementById(`step${this.app.currentStep}`).classList.remove('active');
            this.app.currentStep--;
            document.getElementById(`step${this.app.currentStep}`).classList.add('active');
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
        if (this.app.isAuthenticated) {
            try {
                const response = await fetch(`${this.app.apiBase}/settings/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.app.getCookie('csrftoken')
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

    // Settings page functionality
    async loadSettingsPage() {
        // Load existing settings from backend
        try {
            const response = await fetch(`${this.app.apiBase}/settings/`);
            if (response.ok) {
                const settings = await response.json();
                this.populateSettingsForm(settings);
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    populateSettingsForm(settings) {
        if (!settings) return;
        
        // Populate form fields if they exist
        const fieldMappings = {
            'radarr_url': 'radarrUrl',
            'radarr_api_key': 'radarrApiKey',
            'sonarr_url': 'sonarrUrl',
            'sonarr_api_key': 'sonarrApiKey',
            'server_type': 'serverType',
            'server_url': 'serverUrl',
            'server_api_key': 'serverApiKey',
            'theme': 'theme'
        };

        Object.entries(fieldMappings).forEach(([settingKey, fieldId]) => {
            const field = document.getElementById(fieldId);
            if (field && settings[settingKey]) {
                field.value = settings[settingKey];
            }
        });
    }

    loadExistingSettings() {
        // Load from backend for authenticated users
        try {
            if (this.app.isAuthenticated) {
                this.loadSettingsPage();
            } else {
                // Load from localStorage for guests
                const savedSettings = localStorage.getItem('suggesterr_settings');
                if (savedSettings) {
                    const settings = JSON.parse(savedSettings);
                    this.populateSettingsForm(settings);
                }
            }
        } catch (error) {
            console.error('Error loading existing settings:', error);
        }
    }

    async saveSettings() {
        // Gather form data - use correct field IDs for settings page
        const settings = {
            radarr_url: this.getFieldValue('settingsRadarrUrl'),
            radarr_api_key: this.getFieldValue('settingsRadarrApiKey'),
            sonarr_url: this.getFieldValue('settingsSonarrUrl'),
            sonarr_api_key: this.getFieldValue('settingsSonarrApiKey'),
            server_type: this.getFieldValue('settingsServerType'),
            server_url: this.getFieldValue('settingsServerUrl'),
            server_api_key: this.getFieldValue('settingsServerApiKey'),
            theme: this.getFieldValue('settingsTheme') || this.app.currentTheme
        };
        
        console.log('Theme-UI saveSettings called with:', settings);

        // Save to localStorage
        localStorage.setItem('suggesterr_settings', JSON.stringify(settings));

        // Save to backend if authenticated
        if (this.app.isAuthenticated) {
            try {
                const response = await fetch(`${this.app.apiBase}/settings/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.app.getCookie('csrftoken')
                    },
                    body: JSON.stringify(settings)
                });

                if (response.ok) {
                    this.showToast('Settings saved successfully', 'success');
                } else {
                    this.showToast('Failed to save settings', 'error');
                }
            } catch (error) {
                console.error('Error saving settings:', error);
                this.showToast('Error saving settings', 'error');
            }
        } else {
            this.showToast('Settings saved locally', 'success');
        }
    }

    getFieldValue(fieldId) {
        const field = document.getElementById(fieldId);
        return field ? field.value.trim() : '';
    }

    // Infinite scroll and loading indicators
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

    // Smart onboarding check
    checkSmartOnboarding() {
        // Check if user has completed onboarding or has settings configured
        const onboardingCompleted = localStorage.getItem('onboardingCompleted');
        const hasSettings = localStorage.getItem('suggesterr_settings');
        
        if (!onboardingCompleted && !hasSettings && this.app.isAuthenticated) {
            // Show onboarding for new authenticated users
            setTimeout(() => this.showOnboarding(), 1000);
        }
    }

    async checkUserConfiguration() {
        try {
            const response = await fetch(`${this.app.apiBase}/settings/`);
            if (response.ok) {
                const settings = await response.json();
                
                // Check if user has configured basic settings
                const hasRadarr = settings.radarr_url && settings.radarr_api_key;
                const hasSonarr = settings.sonarr_url && settings.sonarr_api_key;
                const hasMediaServer = settings.server_url && settings.server_api_key;
                
                // Hide hero section if user has configured any media server
                if (hasRadarr || hasSonarr || hasMediaServer) {
                    this.hideHeroSection();
                } else {
                    // Show hero section if no configuration exists
                    this.showHeroSection();
                }
            }
        } catch (error) {
            console.error('Error checking user configuration:', error);
            // On error, default to showing the hero section
            this.showHeroSection();
        }
    }

    hideHeroSection() {
        const heroSection = document.getElementById('hero');
        if (heroSection) {
            heroSection.style.display = 'none';
        }
    }

    showHeroSection() {
        const heroSection = document.getElementById('hero');
        if (heroSection) {
            heroSection.style.display = 'block';
        }
    }
}