// Parental Dashboard JavaScript

let currentProfileId = 'all';
let dashboardData = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardData();
    startAutoRefresh();
});

// Load dashboard data
async function loadDashboardData() {
    try {
        let url = '/accounts/api/family/dashboard/';
        if (currentProfileId !== 'all') {
            url = `/accounts/api/family/dashboard/${currentProfileId}/`;
        }
        
        const response = await fetch(url);
        if (response.ok) {
            const data = await response.json();
            if (currentProfileId === 'all') {
                dashboardData = aggregateDashboardData(data);
            } else {
                dashboardData = data;
            }
            updateDashboard();
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Aggregate data for all profiles
function aggregateDashboardData(profilesData) {
    const aggregated = {
        total_requests: 0,
        pending_requests: 0,
        approved_requests: 0,
        denied_requests: 0,
        daily_request_count: 0,
        weekly_request_count: 0,
        monthly_request_count: 0,
        blocked_content_count: 0,
        approved_content_count: 0,
        recent_activities: [],
        profiles: profilesData
    };
    
    profilesData.forEach(profile => {
        aggregated.total_requests += profile.total_requests || 0;
        aggregated.pending_requests += profile.pending_requests || 0;
        aggregated.approved_requests += profile.approved_requests || 0;
        aggregated.denied_requests += profile.denied_requests || 0;
        aggregated.daily_request_count += profile.daily_request_count || 0;
        aggregated.weekly_request_count += profile.weekly_request_count || 0;
        aggregated.monthly_request_count += profile.monthly_request_count || 0;
        aggregated.blocked_content_count += profile.blocked_content_count || 0;
        aggregated.approved_content_count += profile.approved_content_count || 0;
        
        if (profile.recent_activities) {
            aggregated.recent_activities.push(...profile.recent_activities);
        }
    });
    
    // Sort recent activities by timestamp
    aggregated.recent_activities.sort((a, b) => 
        new Date(b.timestamp) - new Date(a.timestamp)
    );
    
    return aggregated;
}

// Update dashboard UI
function updateDashboard() {
    // Update statistics
    document.getElementById('totalRequests').textContent = dashboardData.total_requests || 0;
    document.getElementById('pendingRequests').textContent = dashboardData.pending_requests || 0;
    document.getElementById('contentViewed').textContent = dashboardData.approved_requests || 0;
    document.getElementById('blockedContent').textContent = dashboardData.blocked_content_count || 0;
    
    // Update pending requests
    updatePendingRequests();
    
    // Update recent activity
    updateRecentActivity();
    
    // Update usage limits
    updateUsageLimits();
}

// Update pending requests section
async function updatePendingRequests() {
    const container = document.getElementById('pendingRequestsList');
    
    try {
        const response = await fetch('/accounts/api/family/content-requests/pending/');
        if (response.ok) {
            const requests = await response.json();
            
            if (requests.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-check-circle"></i>
                        <p>No pending requests</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = requests.slice(0, 5).map(request => `
                <div class="request-item">
                    <div class="request-content">
                        <div class="activity-title">${request.profile_name} requested "${request.content_title}"</div>
                        <div class="activity-meta">${request.request_message || 'No message'}</div>
                    </div>
                    <div class="request-actions">
                        <button class="request-btn approve-btn" onclick="approveRequest(${request.id})">
                            <i class="fas fa-check"></i> Approve
                        </button>
                        <button class="request-btn deny-btn" onclick="denyRequest(${request.id})">
                            <i class="fas fa-times"></i> Deny
                        </button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading pending requests:', error);
    }
}

// Update recent activity section
function updateRecentActivity() {
    const container = document.getElementById('recentActivityList');
    const activities = dashboardData.recent_activities || [];
    
    if (activities.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-history"></i>
                <p>No recent activity</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = activities.slice(0, 10).map(activity => {
        const icon = getActivityIcon(activity.activity_type);
        const time = formatRelativeTime(activity.timestamp);
        
        return `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="fas fa-${icon}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.description}</div>
                    <div class="activity-meta">${activity.profile_name}</div>
                </div>
                <div class="activity-time">${time}</div>
            </div>
        `;
    }).join('');
}

// Update usage limits section
function updateUsageLimits() {
    const container = document.getElementById('usageLimitsGrid');
    
    if (currentProfileId === 'all') {
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <p>Select a specific profile to view usage limits</p>
            </div>
        `;
        return;
    }
    
    const limits = dashboardData.limits;
    if (!limits) {
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <p>No usage limits configured</p>
            </div>
        `;
        return;
    }
    
    const dailyPercentage = (dashboardData.daily_request_count / limits.daily_request_limit) * 100;
    const weeklyPercentage = (dashboardData.weekly_request_count / limits.weekly_request_limit) * 100;
    const monthlyPercentage = (dashboardData.monthly_request_count / limits.monthly_request_limit) * 100;
    
    container.innerHTML = `
        <div class="limit-item">
            <div class="limit-label">Daily Requests</div>
            <div class="limit-value">${dashboardData.daily_request_count} / ${limits.daily_request_limit}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${Math.min(dailyPercentage, 100)}%"></div>
            </div>
        </div>
        <div class="limit-item">
            <div class="limit-label">Weekly Requests</div>
            <div class="limit-value">${dashboardData.weekly_request_count} / ${limits.weekly_request_limit}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${Math.min(weeklyPercentage, 100)}%"></div>
            </div>
        </div>
        <div class="limit-item">
            <div class="limit-label">Monthly Requests</div>
            <div class="limit-value">${dashboardData.monthly_request_count} / ${limits.monthly_request_limit}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${Math.min(monthlyPercentage, 100)}%"></div>
            </div>
        </div>
        <div class="limit-item">
            <div class="limit-label">Viewing Hours</div>
            <div class="limit-value">${limits.wakeup_hour}:00 - ${limits.bedtime_hour}:00</div>
            <div class="limit-remaining">Weekend: until ${limits.weekend_bedtime_hour}:00</div>
        </div>
    `;
}

// Switch profile tab
function switchProfileTab(profileId) {
    currentProfileId = profileId;
    
    // Update active tab
    document.querySelectorAll('.profile-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Reload dashboard data
    loadDashboardData();
}

// Approve content request
async function approveRequest(requestId) {
    try {
        const response = await fetch(`/accounts/api/family/content-requests/${requestId}/approve/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify({
                parent_response: 'Approved via dashboard',
                temporary_access: false
            })
        });
        
        if (response.ok) {
            showToast('Request approved', 'success');
            loadDashboardData();
        } else {
            showToast('Failed to approve request', 'error');
        }
    } catch (error) {
        console.error('Error approving request:', error);
        showToast('Error approving request', 'error');
    }
}

// Deny content request
async function denyRequest(requestId) {
    try {
        const response = await fetch(`/accounts/api/family/content-requests/${requestId}/deny/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify({
                parent_response: 'Denied via dashboard'
            })
        });
        
        if (response.ok) {
            showToast('Request denied', 'success');
            loadDashboardData();
        } else {
            showToast('Failed to deny request', 'error');
        }
    } catch (error) {
        console.error('Error denying request:', error);
        showToast('Error denying request', 'error');
    }
}

// Show usage limits modal
function showUsageLimitsModal() {
    if (currentProfileId === 'all') {
        showToast('Please select a specific profile to edit limits', 'info');
        return;
    }
    
    // This would open a modal to edit usage limits
    showToast('Usage limits editor coming soon', 'info');
}

// Get activity icon based on type
function getActivityIcon(activityType) {
    const icons = {
        'content_view': 'play-circle',
        'content_request': 'hand-paper',
        'request_denied': 'times-circle',
        'request_approved': 'check-circle',
        'content_blocked': 'shield-alt',
        'limit_exceeded': 'exclamation-triangle',
        'profile_toggled': 'toggle-on'
    };
    return icons[activityType] || 'info-circle';
}

// Format relative time
function formatRelativeTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return date.toLocaleDateString();
}

// Toast notification
function showToast(message, type = 'info') {
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

// Auto-refresh dashboard
function startAutoRefresh() {
    setInterval(() => {
        loadDashboardData();
    }, 30000); // Refresh every 30 seconds
}