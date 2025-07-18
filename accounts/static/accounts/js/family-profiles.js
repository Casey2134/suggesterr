// Family Profiles Management JavaScript

// Profile Management Functions
function showAddProfileModal() {
    document.getElementById('addProfileModal').style.display = 'flex';
    document.getElementById('profileName').focus();
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Switch active profile
async function switchProfile(profileId) {
    try {
        const response = await fetch(`/accounts/switch-profile/${profileId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.csrfToken,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            showToast(`Switched to ${data.profile_name}`, 'success');
            
            // Update UI
            document.querySelectorAll('.profile-card').forEach(card => {
                card.classList.remove('active');
            });
            document.querySelector(`[data-profile-id="${profileId}"]`).classList.add('active');
            
            // Reload page to apply profile filters
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showToast('Failed to switch profile', 'error');
        }
    } catch (error) {
        console.error('Error switching profile:', error);
        showToast('Error switching profile', 'error');
    }
}

// Edit profile
async function editProfile(event, profileId) {
    event.stopPropagation();
    
    try {
        const response = await fetch(`/accounts/api/family/profiles/${profileId}/`);
        if (response.ok) {
            const profile = await response.json();
            
            // Populate edit form
            document.getElementById('editProfileId').value = profile.id;
            document.getElementById('editProfileName').value = profile.profile_name;
            document.getElementById('editProfileAge').value = profile.age;
            document.getElementById('editMaxMovieRating').value = profile.max_movie_rating;
            document.getElementById('editMaxTvRating').value = profile.max_tv_rating;
            document.getElementById('editProfileActive').checked = profile.is_active;
            
            document.getElementById('editProfileModal').style.display = 'flex';
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        showToast('Error loading profile', 'error');
    }
}

// Delete profile
async function deleteProfile(event, profileId) {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this profile? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/accounts/api/family/profiles/${profileId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': window.csrfToken
            }
        });

        if (response.ok) {
            showToast('Profile deleted successfully', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showToast('Failed to delete profile', 'error');
        }
    } catch (error) {
        console.error('Error deleting profile:', error);
        showToast('Error deleting profile', 'error');
    }
}

// Form submissions
document.getElementById('addProfileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const profileData = {
        profile_name: document.getElementById('profileName').value,
        age: parseInt(document.getElementById('profileAge').value),
        max_movie_rating: document.getElementById('maxMovieRating').value,
        max_tv_rating: document.getElementById('maxTvRating').value
    };
    
    try {
        const response = await fetch('/accounts/api/family/profiles/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify(profileData)
        });
        
        if (response.ok) {
            showToast('Profile created successfully', 'success');
            closeModal('addProfileModal');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to create profile', 'error');
        }
    } catch (error) {
        console.error('Error creating profile:', error);
        showToast('Error creating profile', 'error');
    }
});

document.getElementById('editProfileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const profileId = document.getElementById('editProfileId').value;
    const profileData = {
        profile_name: document.getElementById('editProfileName').value,
        age: parseInt(document.getElementById('editProfileAge').value),
        max_movie_rating: document.getElementById('editMaxMovieRating').value,
        max_tv_rating: document.getElementById('editMaxTvRating').value,
        is_active: document.getElementById('editProfileActive').checked
    };
    
    try {
        const response = await fetch(`/accounts/api/family/profiles/${profileId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify(profileData)
        });
        
        if (response.ok) {
            showToast('Profile updated successfully', 'success');
            closeModal('editProfileModal');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        showToast('Error updating profile', 'error');
    }
});

// Show content filters modal
function showContentFiltersModal() {
    // This would open a modal to manage content filters
    showToast('Content filters management coming soon', 'info');
}

// Show usage limits modal
function showUsageLimitsModal() {
    // This would open a modal to manage usage limits
    showToast('Usage limits management coming soon', 'info');
}

// Toast notification function
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add toast styles
const style = document.createElement('style');
style.textContent = `
    .toast {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: var(--bg-card);
        color: var(--text-primary);
        padding: 1rem 1.5rem;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        transform: translateY(100px);
        opacity: 0;
        transition: all 0.3s ease;
        z-index: 9999;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    .toast.show {
        transform: translateY(0);
        opacity: 1;
    }
    
    .toast-success {
        border-left: 4px solid #22c55e;
    }
    
    .toast-error {
        border-left: 4px solid #ef4444;
    }
    
    .toast-info {
        border-left: 4px solid #3b82f6;
    }
    
    .modal {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        z-index: 1000;
        align-items: center;
        justify-content: center;
    }
    
    .modal-content {
        background: var(--bg-card);
        border-radius: 12px;
        width: 90%;
        max-width: 500px;
        max-height: 90vh;
        overflow-y: auto;
    }
    
    .modal-header {
        padding: 1.5rem;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .modal-header h2 {
        margin: 0;
        font-size: 1.5rem;
    }
    
    .modal-close {
        background: none;
        border: none;
        color: var(--text-secondary);
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: all 0.2s ease;
    }
    
    .modal-close:hover {
        background: rgba(255, 255, 255, 0.1);
        color: var(--text-primary);
    }
    
    .modal-body {
        padding: 1.5rem;
    }
    
    .form-group {
        margin-bottom: 1.5rem;
    }
    
    .form-group label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: var(--text-primary);
    }
    
    .form-control {
        width: 100%;
        padding: 0.75rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
        font-size: 1rem;
        transition: all 0.2s ease;
    }
    
    .form-control:focus {
        outline: none;
        border-color: var(--accent-color);
        box-shadow: 0 0 0 3px rgba(var(--accent-color-rgb), 0.1);
    }
    
    .form-actions {
        display: flex;
        gap: 1rem;
        justify-content: flex-end;
        margin-top: 2rem;
    }
    
    .btn {
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .btn-primary {
        background: var(--accent-color);
        color: white;
    }
    
    .btn-primary:hover {
        background: var(--accent-hover);
    }
    
    .btn-secondary {
        background: var(--bg-secondary);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }
    
    .btn-secondary:hover {
        background: var(--border-color);
    }
`;
document.head.appendChild(style);