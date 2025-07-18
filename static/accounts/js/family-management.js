// Family Management JavaScript

let currentFamily = null;
let familyMembers = [];
let pendingRequests = [];

// Initialize family management
document.addEventListener('DOMContentLoaded', function() {
    loadFamilyInfo();
    setupEventListeners();
});

function setupEventListeners() {
    // Create family form
    document.getElementById('createFamilyForm').addEventListener('submit', function(e) {
        e.preventDefault();
        createFamily();
    });

    // Invite member form
    document.getElementById('inviteMemberForm').addEventListener('submit', function(e) {
        e.preventDefault();
        inviteMember();
    });

    // Member settings form
    document.getElementById('memberSettingsForm').addEventListener('submit', function(e) {
        e.preventDefault();
        updateMemberSettings();
    });
}

// Load family information
async function loadFamilyInfo() {
    try {
        const response = await fetch('/accounts/api/family/family-management/my_family/', {
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            currentFamily = await response.json();
            document.getElementById('familyInfo').textContent = 
                `${currentFamily.family_name} - ${currentFamily.member_count} members`;
            
            await loadFamilyMembers();
            showFamilyControls();
        } else {
            showNoFamilyCard();
        }
    } catch (error) {
        console.error('Error loading family info:', error);
        showNoFamilyCard();
    }
}

// Load family members
async function loadFamilyMembers() {
    try {
        const response = await fetch(`/accounts/api/family/family-groups/${currentFamily.family_id}/members/`, {
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            familyMembers = await response.json();
            renderFamilyMembers();
            loadPendingRequests();
        }
    } catch (error) {
        console.error('Error loading family members:', error);
    }
}

// Load pending requests count
async function loadPendingRequests() {
    try {
        const response = await fetch('/accounts/api/family/user-content-requests/pending/', {
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            pendingRequests = await response.json();
            updatePendingRequestsBadge();
        }
    } catch (error) {
        console.error('Error loading pending requests:', error);
    }
}

// Render family members
function renderFamilyMembers() {
    const membersGrid = document.getElementById('membersGrid');
    membersGrid.innerHTML = '';

    // Render existing members
    familyMembers.forEach(member => {
        const memberCard = createMemberCard(member);
        membersGrid.appendChild(memberCard);
    });

    // Add invite member card (only for admins)
    if (currentFamily.is_admin) {
        const inviteCard = createInviteMemberCard();
        membersGrid.appendChild(inviteCard);
    }
}

// Create member card element
function createMemberCard(member) {
    const card = document.createElement('div');
    card.className = `member-card ${member.is_admin ? 'admin' : ''}`;
    
    const initials = member.full_name ? 
        member.full_name.split(' ').map(n => n[0]).join('').toUpperCase() : 
        member.username[0].toUpperCase();

    card.innerHTML = `
        ${member.is_admin ? '<div class="member-badge"><i class="fas fa-crown"></i></div>' : ''}
        <div class="activity-indicator ${member.is_active ? '' : 'inactive'}"></div>
        ${currentFamily.is_admin && !member.is_admin ? `
            <div class="member-actions">
                <button class="member-action-btn" onclick="editMember(${member.id})" title="Edit Member">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="member-action-btn" onclick="removeMember(${member.id})" title="Remove Member">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        ` : ''}
        <div class="member-avatar ${member.is_admin ? 'admin' : ''}">
            ${initials}
        </div>
        <h3 class="member-name">${member.full_name || member.username}</h3>
        <div class="member-info">
            <p>${member.is_admin ? 'Admin' : `Age ${member.age || 'N/A'}`}</p>
            <p>${member.max_movie_rating || 'N/A'} / ${member.max_tv_rating || 'N/A'}</p>
        </div>
        <div class="member-stats">
            <div class="stat-item">
                <div class="stat-value">${member.total_requests || 0}</div>
                <div class="stat-label">Requests</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${member.pending_requests || 0}</div>
                <div class="stat-label">Pending</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${member.approved_requests || 0}</div>
                <div class="stat-label">Approved</div>
            </div>
        </div>
    `;

    return card;
}

// Create invite member card
function createInviteMemberCard() {
    const card = document.createElement('div');
    card.className = 'invite-member-card';
    card.onclick = showInviteMemberModal;
    
    card.innerHTML = `
        <i class="fas fa-user-plus invite-icon"></i>
        <p>Invite Member</p>
    `;

    return card;
}

// Show/hide UI elements
function showNoFamilyCard() {
    document.getElementById('noFamilyCard').style.display = 'block';
    document.getElementById('membersGrid').style.display = 'none';
    document.getElementById('familyControls').style.display = 'none';
    document.getElementById('familyInfo').textContent = 'No family group created';
}

function showFamilyControls() {
    document.getElementById('noFamilyCard').style.display = 'none';
    document.getElementById('membersGrid').style.display = 'grid';
    document.getElementById('familyControls').style.display = 'block';
}

function updatePendingRequestsBadge() {
    const badge = document.getElementById('pendingRequestsBadge');
    if (pendingRequests.length > 0) {
        badge.textContent = pendingRequests.length;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

// Modal functions
function showCreateFamilyModal() {
    document.getElementById('createFamilyModal').style.display = 'flex';
}

function showInviteMemberModal() {
    document.getElementById('inviteMemberModal').style.display = 'flex';
}

function showMemberSettingsModal() {
    document.getElementById('memberSettingsModal').style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Create family
async function createFamily() {
    const familyName = document.getElementById('familyName').value;
    
    try {
        const response = await fetch('/accounts/api/family/family-management/create_family/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                family_name: familyName
            })
        });

        if (response.ok) {
            const result = await response.json();
            showNotification('Family created successfully!', 'success');
            closeModal('createFamilyModal');
            await loadFamilyInfo();
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to create family', 'error');
        }
    } catch (error) {
        console.error('Error creating family:', error);
        showNotification('Error creating family', 'error');
    }
}

// Invite member
async function inviteMember() {
    const email = document.getElementById('memberEmail').value;
    const age = parseInt(document.getElementById('memberAge').value);
    const maxMovieRating = document.getElementById('memberMaxMovieRating').value;
    const maxTvRating = document.getElementById('memberMaxTvRating').value;
    const message = document.getElementById('inviteMessage').value;

    try {
        const response = await fetch(`/accounts/api/family/family-groups/${currentFamily.family_id}/invite_member/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                email,
                proposed_age: age,
                proposed_max_movie_rating: maxMovieRating,
                proposed_max_tv_rating: maxTvRating,
                message
            })
        });

        if (response.ok) {
            showNotification('Invitation sent successfully!', 'success');
            closeModal('inviteMemberModal');
            document.getElementById('inviteMemberForm').reset();
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to send invitation', 'error');
        }
    } catch (error) {
        console.error('Error inviting member:', error);
        showNotification('Error sending invitation', 'error');
    }
}

// Edit member
function editMember(memberId) {
    const member = familyMembers.find(m => m.id === memberId);
    if (!member) return;

    document.getElementById('editMemberId').value = memberId;
    document.getElementById('editMemberAge').value = member.age;
    document.getElementById('editMemberMaxMovieRating').value = member.max_movie_rating;
    document.getElementById('editMemberMaxTvRating').value = member.max_tv_rating;
    document.getElementById('editMemberActive').checked = member.is_active;

    showMemberSettingsModal();
}

// Update member settings
async function updateMemberSettings() {
    const memberId = document.getElementById('editMemberId').value;
    const age = parseInt(document.getElementById('editMemberAge').value);
    const maxMovieRating = document.getElementById('editMemberMaxMovieRating').value;
    const maxTvRating = document.getElementById('editMemberMaxTvRating').value;
    const isActive = document.getElementById('editMemberActive').checked;

    try {
        const response = await fetch(`/accounts/api/family/family-memberships/${memberId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                age,
                max_movie_rating: maxMovieRating,
                max_tv_rating: maxTvRating,
                is_active: isActive
            })
        });

        if (response.ok) {
            showNotification('Member settings updated successfully!', 'success');
            closeModal('memberSettingsModal');
            await loadFamilyMembers();
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to update member settings', 'error');
        }
    } catch (error) {
        console.error('Error updating member settings:', error);
        showNotification('Error updating member settings', 'error');
    }
}

// Remove member
async function removeMember(memberId) {
    if (!confirm('Are you sure you want to remove this member from the family?')) {
        return;
    }

    const member = familyMembers.find(m => m.id === memberId);
    if (!member) return;

    try {
        const response = await fetch(`/accounts/api/family/family-groups/${currentFamily.family_id}/remove_member/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                user_id: member.user
            })
        });

        if (response.ok) {
            showNotification('Member removed successfully!', 'success');
            await loadFamilyMembers();
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to remove member', 'error');
        }
    } catch (error) {
        console.error('Error removing member:', error);
        showNotification('Error removing member', 'error');
    }
}

// Navigation functions
function showFamilyDashboard() {
    window.location.href = '/accounts/family-dashboard/';
}

function showContentRequests() {
    window.location.href = '/accounts/content-requests/';
}

function showContentFiltersModal() {
    // TODO: Implement content filters modal
    showNotification('Content filters feature coming soon!', 'info');
}

function showUsageLimitsModal() {
    // TODO: Implement usage limits modal
    showNotification('Usage limits feature coming soon!', 'info');
}

// Utility functions
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

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Remove notification
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});