// Authentication-related functionality
class AuthModule {
    constructor(app) {
        this.app = app;
    }

    // Authentication Methods
    async checkAuthState() {
        try {
            const response = await fetch(`${this.app.apiBase}/auth/current_user/`);
            const data = await response.json();
            
            if (data.user) {
                this.app.currentUser = data.user;
                this.app.isAuthenticated = true;
            } else {
                this.app.currentUser = null;
                this.app.isAuthenticated = false;
            }
        } catch (error) {
            console.error('Error checking auth state:', error);
            this.app.isAuthenticated = false;
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
        if (usernameDisplay && this.app.currentUser) {
            usernameDisplay.textContent = `Welcome, ${this.app.currentUser.username}`;
        }
        
        // Create settings button if needed
        this.ensureSettingsButton();
        
        // Load dashboard data
        this.app.loadInitialData();
        this.app.checkSmartOnboarding();
    }

    showLoginPage() {
        console.log('Redirecting to Django login page');
        // Redirect to Django login page
        window.location.href = '/accounts/login/';
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
            usernameDisplay.textContent = `Welcome, ${this.app.currentUser.username}`;
            console.log('Set username to:', this.app.currentUser.username);
        }
        
        // Force create a working Settings button
        this.createWorkingSettingsButton();
        
        // Hero section buttons
        this.hideElements(['getStartedBtn', 'loginBtn', 'registerBtn']);
        
        console.log('=== DIAGNOSTIC: After showAuthenticatedUI ===');
        this.diagnoseElements();
        
        // Load user's theme preference
        this.app.theme.loadUserThemePreference();
        
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
            }
        }, 100);
    }

    createWorkingSettingsButton() {
        console.log('🔧 Creating working settings button...');
        
        // Find the user actions container
        const userActions = document.getElementById('user-actions');
        if (!userActions) {
            console.log('❌ user-actions container not found');
            return;
        }
        
        // Remove existing settings button if any
        const existingSettingsBtn = document.getElementById('settingsBtn');
        if (existingSettingsBtn) {
            existingSettingsBtn.remove();
            console.log('🗑️ Removed existing settings button');
        }
        
        // Create new settings button
        const settingsBtn = document.createElement('button');
        settingsBtn.id = 'settingsBtn';
        settingsBtn.className = 'btn btn-secondary';
        settingsBtn.innerHTML = '<i class="fas fa-cog"></i> Settings';
        settingsBtn.onclick = () => {
            console.log('⚙️ Settings button clicked!');
            this.app.navigateToSection('settings');
        };
        
        // Apply aggressive styling to ensure visibility
        settingsBtn.style.cssText = `
            display: inline-block !important;
            visibility: visible !important;
            padding: 0.75rem 1.5rem !important;
            font-size: 0.9rem !important;
            border: none !important;
            border-radius: 6px !important;
            background: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            cursor: pointer !important;
            text-decoration: none !important;
            transition: all 0.2s ease !important;
            margin-left: 0.5rem !important;
            white-space: nowrap !important;
            min-width: auto !important;
            min-height: auto !important;
            width: auto !important;
            height: auto !important;
            box-sizing: border-box !important;
        `;
        
        // Add hover effect
        settingsBtn.addEventListener('mouseenter', () => {
            settingsBtn.style.setProperty('background', 'var(--accent-color)', 'important');
        });
        settingsBtn.addEventListener('mouseleave', () => {
            settingsBtn.style.setProperty('background', 'var(--bg-secondary)', 'important');
        });
        
        // Insert at the beginning of user-actions
        userActions.insertBefore(settingsBtn, userActions.firstChild);
        
        console.log('✅ Created and inserted new settings button');
        
        // Force reflow and verify
        settingsBtn.offsetHeight;
        setTimeout(() => {
            const rect = settingsBtn.getBoundingClientRect();
            console.log('New settings button check:', {
                width: rect.width,
                height: rect.height,
                isVisible: rect.width > 0 && rect.height > 0,
                display: window.getComputedStyle(settingsBtn).display
            });
        }, 10);
    }

    ensureSettingsButton() {
        const settingsBtn = document.getElementById('settingsBtn');
        if (!settingsBtn) {
            this.createWorkingSettingsButton();
        } else {
            this.diagnoseSettingsButton();
        }
    }

    async markNotInterested(tmdbId, contentType) {
        if (!this.app.isAuthenticated) {
            this.app.showToast('Please log in to mark items as not interested', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.app.apiBase}/negative-feedback/mark_not_interested/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.app.getCookie('csrftoken')
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
                this.app.showToast(`Marked ${contentType} as not interested`, 'success');
                
                // Refresh the current section to hide the item
                if (this.app.currentSection === 'movies') {
                    this.app.loadInitialData();
                } else if (this.app.currentSection === 'tv-shows') {
                    this.app.showSection('tv-shows');
                }
            } else {
                throw new Error('Failed to mark as not interested');
            }
        } catch (error) {
            console.error('Error marking as not interested:', error);
            this.app.showToast('Failed to mark as not interested', 'error');
        }
    }

    async login(username, password) {
        try {
            const response = await fetch(`${this.app.apiBase}/auth/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.app.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.app.currentUser = data.user;
                this.app.isAuthenticated = true;
                this.showAuthenticatedUI();
                this.app.loadInitialData();
                return { success: true };
            } else {
                return { success: false, error: data.error || 'Login failed' };
            }
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: 'Network error occurred' };
        }
    }

    async register(username, email, password) {
        try {
            const response = await fetch(`${this.app.apiBase}/auth/register/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.app.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Auto login after successful registration
                const loginResult = await this.login(username, password);
                return loginResult;
            } else {
                return { success: false, error: data.error || 'Registration failed' };
            }
        } catch (error) {
            console.error('Registration error:', error);
            return { success: false, error: 'Network error occurred' };
        }
    }

    async logout() {
        try {
            await fetch(`${this.app.apiBase}/auth/logout/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.app.getCookie('csrftoken')
                }
            });

            this.app.currentUser = null;
            this.app.isAuthenticated = false;
            this.showGuestUI();
            
            // Clear any cached data
            localStorage.removeItem('suggesterr_settings');
            
            // Redirect to login page
            this.showLoginPage();
        } catch (error) {
            console.error('Logout error:', error);
        }
    }
}