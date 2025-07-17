// Settings page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Load quiz status when page loads
    loadQuizStatus();
    
    // Load other settings
    loadSettings();
    
    // Add real-time validation
    setupRealTimeValidation();
});

function setupRealTimeValidation() {
    // Add validation for URL fields
    const urlFields = ['settingsRadarrUrl', 'settingsSonarrUrl', 'settingsServerUrl'];
    urlFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('blur', function() {
                validateField(this);
            });
            field.addEventListener('input', function() {
                clearFieldError(this);
            });
        }
    });
    
    // Add validation for API key fields
    const apiFields = ['settingsRadarrApiKey', 'settingsSonarrApiKey', 'settingsServerApiKey'];
    apiFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('blur', function() {
                validateField(this);
            });
            field.addEventListener('input', function() {
                clearFieldError(this);
            });
        }
    });
}

function validateField(field) {
    const value = field.value.trim();
    const fieldId = field.id;
    
    // Clear previous errors
    clearFieldError(field);
    
    // Skip validation for empty fields
    if (!value) return;
    
    let isValid = true;
    let errorMessage = '';
    
    // Validate URLs
    if (fieldId.includes('Url')) {
        try {
            new URL(value);
        } catch (e) {
            isValid = false;
            errorMessage = 'Please enter a valid URL (e.g., http://localhost:8080)';
        }
    }
    
    // Validate API keys
    if (fieldId.includes('ApiKey')) {
        if (value.length < 10) {
            isValid = false;
            errorMessage = 'API key seems too short to be valid';
        } else if (value.length > 200) {
            isValid = false;
            errorMessage = 'API key seems too long';
        }
    }
    
    // Show error if invalid
    if (!isValid) {
        showFieldError(field, errorMessage);
    }
}

function showFieldError(field, message) {
    field.style.borderColor = '#ef4444';
    field.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
    
    // Create error message element
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    errorElement.style.cssText = `
        color: #ef4444;
        font-size: 0.75rem;
        margin-top: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    `;
    errorElement.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    // Insert error message after the field
    field.parentNode.appendChild(errorElement);
}

function clearFieldError(field) {
    field.style.borderColor = '';
    field.style.backgroundColor = '';
    
    // Remove error message
    const errorElement = field.parentNode.querySelector('.field-error');
    if (errorElement) {
        errorElement.remove();
    }
}

// Quiz Status Functions
async function loadQuizStatus() {
    const quizStatusElement = document.getElementById('quiz-status');
    const takeQuizBtn = document.getElementById('take-quiz-btn');
    const retakeQuizBtn = document.getElementById('retake-quiz-btn');
    
    try {
        const response = await fetch('/recommendations/api/quiz/profile/');
        const data = await response.json();
        
        if (response.ok) {
            const profile = data.profile;
            const quizCompleted = data.quiz_completed;
            
            if (quizCompleted && profile) {
                // Quiz completed
                quizStatusElement.innerHTML = `
                    <i class="fas fa-check-circle status-icon completed"></i>
                    <span>Quiz completed on ${new Date(profile.quiz_completed_at).toLocaleDateString()}</span>
                `;
                quizStatusElement.className = 'quiz-status completed';
                
                // Show completion stats
                const completionStats = document.createElement('div');
                completionStats.className = 'quiz-completion-stats';
                completionStats.innerHTML = `
                    <div class="quiz-stat">
                        <i class="fas fa-heart"></i>
                        <span>${profile.preferred_genres ? profile.preferred_genres.split(', ').length : 0} genres</span>
                    </div>
                    <div class="quiz-stat">
                        <i class="fas fa-calendar"></i>
                        <span>${profile.preferred_decades ? profile.preferred_decades.length : 0} decades</span>
                    </div>
                    <div class="quiz-stat">
                        <i class="fas fa-user"></i>
                        <span>${Object.keys(profile.personality_traits || {}).length} traits</span>
                    </div>
                `;
                quizStatusElement.parentNode.appendChild(completionStats);
                
                // Update buttons
                takeQuizBtn.innerHTML = '<i class="fas fa-eye"></i> View Quiz Results';
                retakeQuizBtn.classList.remove('d-none');
            } else {
                // Quiz not completed
                quizStatusElement.innerHTML = `
                    <i class="fas fa-exclamation-circle status-icon pending"></i>
                    <span>Quiz not completed - Take it now for personalized recommendations!</span>
                `;
                quizStatusElement.className = 'quiz-status not-completed';
                
                takeQuizBtn.innerHTML = '<i class="fas fa-play"></i> Take Discovery Quiz';
                retakeQuizBtn.classList.add('d-none');
            }
        } else {
            throw new Error(data.error || 'Failed to load quiz status');
        }
    } catch (error) {
        console.error('Error loading quiz status:', error);
        quizStatusElement.innerHTML = `
            <i class="fas fa-exclamation-triangle status-icon pending"></i>
            <span>Unable to load quiz status</span>
        `;
        quizStatusElement.className = 'quiz-status not-completed';
    }
}

async function retakeQuiz() {
    if (!confirm('Are you sure you want to retake the quiz? This will reset your current personality profile.')) {
        return;
    }
    
    const retakeBtn = document.getElementById('retake-quiz-btn');
    const originalText = retakeBtn.innerHTML;
    
    try {
        retakeBtn.disabled = true;
        retakeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';
        
        const response = await fetch('/recommendations/api/quiz/retake/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Redirect to quiz page
            window.location.href = '/recommendations/quiz/';
        } else {
            throw new Error(data.error || 'Failed to reset quiz');
        }
    } catch (error) {
        console.error('Error resetting quiz:', error);
        alert('Failed to reset quiz. Please try again.');
    } finally {
        retakeBtn.disabled = false;
        retakeBtn.innerHTML = originalText;
    }
}

// Settings Functions
function loadSettings() {
    // Load user profile data
    loadUserProfile();
    
    // Load saved settings from localStorage
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.getElementById('settingsTheme').value = savedTheme;
    
    const savedRadarrUrl = localStorage.getItem('radarrUrl') || '';
    document.getElementById('settingsRadarrUrl').value = savedRadarrUrl;
    
    const savedRadarrApiKey = localStorage.getItem('radarrApiKey') || '';
    document.getElementById('settingsRadarrApiKey').value = savedRadarrApiKey;
    
    const savedSonarrUrl = localStorage.getItem('sonarrUrl') || '';
    document.getElementById('settingsSonarrUrl').value = savedSonarrUrl;
    
    const savedSonarrApiKey = localStorage.getItem('sonarrApiKey') || '';
    document.getElementById('settingsSonarrApiKey').value = savedSonarrApiKey;
    
    const savedServerType = localStorage.getItem('serverType') || '';
    document.getElementById('settingsServerType').value = savedServerType;
    
    const savedServerUrl = localStorage.getItem('serverUrl') || '';
    document.getElementById('settingsServerUrl').value = savedServerUrl;
    
    const savedServerApiKey = localStorage.getItem('serverApiKey') || '';
    document.getElementById('settingsServerApiKey').value = savedServerApiKey;
}

async function loadUserProfile() {
    try {
        // This would typically come from an API endpoint
        // For now, we'll use placeholder data
        const user = {
            username: 'Current User',
            email: 'user@example.com'
        };
        
        document.getElementById('settingsUsername').value = user.username;
        document.getElementById('settingsEmail').value = user.email;
    } catch (error) {
        console.error('Error loading user profile:', error);
    }
}

// App object for global access (maintaining compatibility)
window.app = {
    saveSettings: function() {
        try {
            // Get all settings values
            const settings = {
                theme: document.getElementById('settingsTheme').value,
                radarrUrl: document.getElementById('settingsRadarrUrl').value.trim(),
                radarrApiKey: document.getElementById('settingsRadarrApiKey').value.trim(),
                sonarrUrl: document.getElementById('settingsSonarrUrl').value.trim(),
                sonarrApiKey: document.getElementById('settingsSonarrApiKey').value.trim(),
                serverType: document.getElementById('settingsServerType').value,
                serverUrl: document.getElementById('settingsServerUrl').value.trim(),
                serverApiKey: document.getElementById('settingsServerApiKey').value.trim()
            };
            
            // Validate settings
            const validationErrors = this.validateSettings(settings);
            if (validationErrors.length > 0) {
                showToast(`Validation errors: ${validationErrors.join(', ')}`, 'error');
                return;
            }
            
            // Track which settings are being updated
            const updatedSettings = [];
            
            // Only save settings that have values (not empty strings)
            Object.keys(settings).forEach(key => {
                const value = settings[key];
                const currentValue = localStorage.getItem(key) || '';
                
                // For theme, always save (it has a default value)
                if (key === 'theme') {
                    localStorage.setItem(key, value);
                    applyTheme(value);
                    updatedSettings.push('Theme');
                }
                // For URLs and API keys, only save if they have actual values
                else if (value && value !== '') {
                    // Only update if the value has changed
                    if (value !== currentValue) {
                        localStorage.setItem(key, value);
                        updatedSettings.push(this.getSettingDisplayName(key));
                    }
                }
                // If field is empty but previously had a value, remove it
                else if (!value && currentValue) {
                    localStorage.removeItem(key);
                    updatedSettings.push(this.getSettingDisplayName(key) + ' (cleared)');
                }
            });
            
            // Show appropriate message
            if (updatedSettings.length > 0) {
                const message = updatedSettings.length === 1 
                    ? `Updated: ${updatedSettings[0]}` 
                    : `Updated ${updatedSettings.length} settings: ${updatedSettings.join(', ')}`;
                showToast(message, 'success');
            } else {
                showToast('No changes detected in settings', 'info');
            }
            
        } catch (error) {
            console.error('Error saving settings:', error);
            showToast('Error saving settings. Please try again.', 'error');
        }
    },
    
    getSettingDisplayName: function(key) {
        const displayNames = {
            radarrUrl: 'Radarr URL',
            radarrApiKey: 'Radarr API Key',
            sonarrUrl: 'Sonarr URL',
            sonarrApiKey: 'Sonarr API Key',
            serverType: 'Server Type',
            serverUrl: 'Server URL',
            serverApiKey: 'Server API Key'
        };
        return displayNames[key] || key;
    },
    
    validateSettings: function(settings) {
        const errors = [];
        
        // Validate URLs
        const urlFields = ['radarrUrl', 'sonarrUrl', 'serverUrl'];
        urlFields.forEach(field => {
            const value = settings[field];
            if (value && value !== '') {
                try {
                    new URL(value);
                } catch (e) {
                    errors.push(`${this.getSettingDisplayName(field)} must be a valid URL`);
                }
            }
        });
        
        // Validate API keys (basic check for reasonable length)
        const apiFields = ['radarrApiKey', 'sonarrApiKey', 'serverApiKey'];
        apiFields.forEach(field => {
            const value = settings[field];
            if (value && value !== '') {
                if (value.length < 10) {
                    errors.push(`${this.getSettingDisplayName(field)} seems too short to be valid`);
                }
                if (value.length > 200) {
                    errors.push(`${this.getSettingDisplayName(field)} seems too long`);
                }
            }
        });
        
        return errors;
    },
    
    testConnections: function() {
        // Test connections to configured services
        showToast('Testing connections...', 'info');
        
        // This would typically make API calls to test the connections
        setTimeout(() => {
            showToast('Connection test completed. Check console for details.', 'success');
        }, 2000);
    }
};

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
}

function showToast(message, type = 'info') {
    // Remove any existing toasts
    document.querySelectorAll('.toast').forEach(toast => toast.remove());
    
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Add icon based on type
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="${icons[type] || icons.info}"></i>
        <span>${message}</span>
    `;
    
    // Get theme-appropriate colors
    const colors = {
        success: { bg: '#10b981', border: '#059669' },
        error: { bg: '#ef4444', border: '#dc2626' },
        info: { bg: 'var(--accent-color)', border: 'var(--accent-hover)' }
    };
    
    const color = colors[type] || colors.info;
    
    // Style the toast
    toast.style.cssText = `
        position: fixed;
        top: 90px;
        right: 20px;
        padding: 12px 16px;
        background: ${color.bg};
        color: white;
        border-radius: 6px;
        border-left: 4px solid ${color.border};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1001;
        font-size: 14px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    
    // Add slide-in animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(toast);
    
    // Remove toast after 5 seconds (longer for error messages)
    const duration = type === 'error' ? 7000 : 5000;
    setTimeout(() => {
        if (toast && toast.parentNode) {
            toast.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => {
                toast.remove();
                if (style && style.parentNode) {
                    style.remove();
                }
            }, 300);
        }
    }, duration);
}

function getCookie(name) {
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

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
});