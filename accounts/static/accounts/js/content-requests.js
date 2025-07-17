// Content Requests Management JavaScript

let allRequests = [];
let filteredRequests = [];
let selectedRequests = [];
let currentPage = 1;
let requestsPerPage = 10;
let currentRequestId = null;

// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
    await loadRequests();
    setupEventListeners();
});

// Load all requests
async function loadRequests() {
    try {
        const response = await fetch('/accounts/api/family/content-requests/');
        if (response.ok) {
            allRequests = await response.json();
            filteredRequests = [...allRequests];
            updateStats();
            renderRequests();
        }
    } catch (error) {
        console.error('Error loading requests:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Temporary access checkbox
    document.getElementById('temporaryAccess').addEventListener('change', function() {
        const expirationGroup = document.getElementById('expirationGroup');
        expirationGroup.style.display = this.checked ? 'block' : 'none';
        
        if (this.checked) {
            // Set default expiration to 7 days from now
            const now = new Date();
            now.setDate(now.getDate() + 7);
            document.getElementById('expirationDate').value = now.toISOString().slice(0, 16);
        }
    });
    
    // Bulk select all
    document.getElementById('selectAll')?.addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('.request-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateBulkActions();
    });
}

// Filter requests
function filterRequests() {
    const statusFilter = document.getElementById('statusFilter').value;
    const profileFilter = document.getElementById('profileFilter').value;
    const contentTypeFilter = document.getElementById('contentTypeFilter').value;
    const dateFilter = document.getElementById('dateFilter').value;
    
    filteredRequests = allRequests.filter(request => {
        let matches = true;
        
        if (statusFilter && request.status !== statusFilter) {
            matches = false;
        }
        
        if (profileFilter && request.profile.toString() !== profileFilter) {
            matches = false;
        }
        
        if (contentTypeFilter) {
            const hasMovie = request.movie !== null;
            const hasTvShow = request.tv_show !== null;
            
            if (contentTypeFilter === 'movie' && !hasMovie) {
                matches = false;
            } else if (contentTypeFilter === 'tv_show' && !hasTvShow) {
                matches = false;
            }
        }
        
        if (dateFilter) {
            const requestDate = new Date(request.created_at);
            const now = new Date();
            
            switch (dateFilter) {
                case 'today':
                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    if (requestDate < today) matches = false;
                    break;
                case 'week':
                    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                    if (requestDate < weekAgo) matches = false;
                    break;
                case 'month':
                    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                    if (requestDate < monthAgo) matches = false;
                    break;
            }
        }
        
        return matches;
    });
    
    currentPage = 1;
    updateStats();
    renderRequests();
}

// Update statistics
function updateStats() {
    const pending = filteredRequests.filter(r => r.status === 'pending').length;
    const approved = filteredRequests.filter(r => r.status === 'approved').length;
    const denied = filteredRequests.filter(r => r.status === 'denied').length;
    
    document.getElementById('pendingCount').textContent = pending;
    document.getElementById('approvedCount').textContent = approved;
    document.getElementById('deniedCount').textContent = denied;
    document.getElementById('totalCount').textContent = filteredRequests.length;
}

// Render requests
function renderRequests() {
    const container = document.getElementById('requestsList');
    
    if (filteredRequests.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>No requests found</h3>
                <p>Content requests will appear here when child profiles request access to blocked content.</p>
            </div>
        `;
        return;
    }
    
    // Pagination
    const startIndex = (currentPage - 1) * requestsPerPage;
    const endIndex = startIndex + requestsPerPage;
    const paginatedRequests = filteredRequests.slice(startIndex, endIndex);
    
    container.innerHTML = paginatedRequests.map(request => {
        const contentTitle = request.movie_title || request.tv_show_title;
        const contentType = request.movie ? 'Movie' : 'TV Show';
        const requestDate = new Date(request.created_at).toLocaleDateString();
        const requestTime = new Date(request.created_at).toLocaleTimeString();
        
        return `
            <div class="request-item ${request.status}">
                <input type="checkbox" class="request-checkbox" data-request-id="${request.id}" onchange="updateBulkActions()">
                
                <div class="request-poster">
                    <i class="fas fa-${request.movie ? 'film' : 'tv'}"></i>
                </div>
                
                <div class="request-content">
                    <div class="request-title">${contentTitle}</div>
                    <div class="request-meta">
                        <span><i class="fas fa-user"></i> ${request.profile_name}</span>
                        <span><i class="fas fa-calendar"></i> ${requestDate} ${requestTime}</span>
                        <span><i class="fas fa-tag"></i> ${contentType}</span>
                    </div>
                    
                    ${request.request_message ? `
                        <div class="request-message">
                            "${request.request_message}"
                        </div>
                    ` : ''}
                    
                    ${request.status === 'pending' ? `
                        <div class="request-actions">
                            <button class="request-btn approve-btn" onclick="showApprovalModal(${request.id})">
                                <i class="fas fa-check"></i> Approve
                            </button>
                            <button class="request-btn deny-btn" onclick="showDenialModal(${request.id})">
                                <i class="fas fa-times"></i> Deny
                            </button>
                        </div>
                    ` : ''}
                    
                    ${request.status !== 'pending' && request.parent_response ? `
                        <div class="response-section">
                            <div class="response-title">Parent Response:</div>
                            <div class="response-content">${request.parent_response}</div>
                            ${request.reviewed_at ? `
                                <div class="response-meta">
                                    Reviewed on ${new Date(request.reviewed_at).toLocaleDateString()}
                                </div>
                            ` : ''}
                        </div>
                    ` : ''}
                    
                    ${request.access_expires_at ? `
                        <div class="access-expires">
                            Access expires: ${new Date(request.access_expires_at).toLocaleDateString()}
                        </div>
                    ` : ''}
                </div>
                
                <div class="request-status status-${request.status}">
                    <i class="fas fa-${getStatusIcon(request.status)}"></i>
                    ${request.status}
                </div>
            </div>
        `;
    }).join('');
    
    updatePagination();
}

// Get status icon
function getStatusIcon(status) {
    const icons = {
        'pending': 'clock',
        'approved': 'check-circle',
        'denied': 'times-circle'
    };
    return icons[status] || 'question-circle';
}

// Update pagination
function updatePagination() {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(filteredRequests.length / requestsPerPage);
    
    if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
    }
    
    pagination.style.display = 'flex';
    
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const pageInfo = document.getElementById('pageInfo');
    
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
}

// Pagination functions
function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        renderRequests();
    }
}

function nextPage() {
    const totalPages = Math.ceil(filteredRequests.length / requestsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        renderRequests();
    }
}

// Show approval modal
function showApprovalModal(requestId) {
    currentRequestId = requestId;
    document.getElementById('approvalModal').style.display = 'flex';
    document.getElementById('approvalMessage').focus();
}

// Show denial modal
function showDenialModal(requestId) {
    currentRequestId = requestId;
    document.getElementById('denialModal').style.display = 'flex';
    document.getElementById('denialMessage').focus();
}

// Close modal
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    currentRequestId = null;
}

// Confirm approval
async function confirmApproval() {
    if (!currentRequestId) return;
    
    const message = document.getElementById('approvalMessage').value;
    const temporaryAccess = document.getElementById('temporaryAccess').checked;
    const expirationDate = document.getElementById('expirationDate').value;
    
    const requestData = {
        parent_response: message,
        temporary_access: temporaryAccess,
        access_expires_at: temporaryAccess ? expirationDate : null
    };
    
    try {
        const response = await fetch(`/accounts/api/family/content-requests/${currentRequestId}/approve/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify(requestData)
        });
        
        if (response.ok) {
            showToast('Request approved successfully', 'success');
            closeModal('approvalModal');
            await loadRequests();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to approve request', 'error');
        }
    } catch (error) {
        console.error('Error approving request:', error);
        showToast('Error approving request', 'error');
    }
}

// Confirm denial
async function confirmDenial() {
    if (!currentRequestId) return;
    
    const message = document.getElementById('denialMessage').value;
    
    const requestData = {
        parent_response: message
    };
    
    try {
        const response = await fetch(`/accounts/api/family/content-requests/${currentRequestId}/deny/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify(requestData)
        });
        
        if (response.ok) {
            showToast('Request denied successfully', 'success');
            closeModal('denialModal');
            await loadRequests();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to deny request', 'error');
        }
    } catch (error) {
        console.error('Error denying request:', error);
        showToast('Error denying request', 'error');
    }
}

// Update bulk actions
function updateBulkActions() {
    const checkboxes = document.querySelectorAll('.request-checkbox:checked');
    const bulkActions = document.getElementById('bulkActions');
    
    if (checkboxes.length > 0) {
        bulkActions.classList.add('show');
        selectedRequests = Array.from(checkboxes).map(cb => cb.dataset.requestId);
    } else {
        bulkActions.classList.remove('show');
        selectedRequests = [];
    }
}

// Bulk approve
async function bulkApprove() {
    if (selectedRequests.length === 0) return;
    
    if (!confirm(`Are you sure you want to approve ${selectedRequests.length} request(s)?`)) {
        return;
    }
    
    const promises = selectedRequests.map(requestId => 
        fetch(`/accounts/api/family/content-requests/${requestId}/approve/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify({
                parent_response: 'Bulk approved',
                temporary_access: false
            })
        })
    );
    
    try {
        const results = await Promise.all(promises);
        const successCount = results.filter(r => r.ok).length;
        
        showToast(`${successCount} request(s) approved successfully`, 'success');
        selectedRequests = [];
        updateBulkActions();
        await loadRequests();
    } catch (error) {
        console.error('Error bulk approving requests:', error);
        showToast('Error approving requests', 'error');
    }
}

// Bulk deny
async function bulkDeny() {
    if (selectedRequests.length === 0) return;
    
    if (!confirm(`Are you sure you want to deny ${selectedRequests.length} request(s)?`)) {
        return;
    }
    
    const promises = selectedRequests.map(requestId => 
        fetch(`/accounts/api/family/content-requests/${requestId}/deny/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify({
                parent_response: 'Bulk denied'
            })
        })
    );
    
    try {
        const results = await Promise.all(promises);
        const successCount = results.filter(r => r.ok).length;
        
        showToast(`${successCount} request(s) denied successfully`, 'success');
        selectedRequests = [];
        updateBulkActions();
        await loadRequests();
    } catch (error) {
        console.error('Error bulk denying requests:', error);
        showToast('Error denying requests', 'error');
    }
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