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
                        <span>${profile.preferred_genres && Array.isArray(profile.preferred_genres) ? profile.preferred_genres.length : (profile.preferred_genres && typeof profile.preferred_genres === 'string' ? profile.preferred_genres.split(', ').length : 0)} genres</span>
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

// Settings Functions - simplified since we're using Django forms now
function loadSettings() {
    // Load quiz status
    loadQuizStatus();
    
    // Apply current theme from the form
    const themeSelect = document.querySelector('select[name="theme"]');
    if (themeSelect && themeSelect.value) {
        applyTheme(themeSelect.value);
    } else {
        // Fallback to saved theme
        const savedTheme = localStorage.getItem('theme') || 'dark';
        applyTheme(savedTheme);
    }
}

// App object for global access (maintaining compatibility)
window.app = {
    
    testConnections: async function() {
        try {
            // Show loading state
            showToast('Testing connections...', 'info');
            
            // Make API call to test connections
            const response = await fetch('/accounts/test_connections/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
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
            
            // Show results in a modal
            this.showTestResultsModal('Connection Test Results', resultsHtml);
            
        } catch (error) {
            console.error('Error testing connections:', error);
            showToast(`Error testing connections: ${error.message}`, 'error');
        }
    },
    
    getStatusIcon: function(status) {
        switch(status) {
            case 'success':
                return '<i class="fas fa-check-circle" style="color: #10b981;"></i>';
            case 'error':
                return '<i class="fas fa-times-circle" style="color: #ef4444;"></i>';
            case 'not_configured':
                return '<i class="fas fa-exclamation-circle" style="color: #f59e0b;"></i>';
            default:
                return '<i class="fas fa-question-circle" style="color: #6b7280;"></i>';
        }
    },
    
    showTestResultsModal: function(title, content) {
        // Create a simple modal to show results
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