/**
 * Global JavaScript functions for the Student Journal application
 */

// Helper function to show custom alerts
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-message`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);
    
    // Remove the alert after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Helper function to get the authenticated user from localStorage
function getCurrentUser() {
    const userJson = localStorage.getItem('user');
    
    if (!userJson) {
        return null;
    }
    
    try {
        return JSON.parse(userJson);
    } catch (error) {
        console.error('Error parsing user JSON:', error);
        return null;
    }
}

// Helper function to handle authentication headers
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    
    if (!token) {
        return {};
    }
    
    return {
        'Authorization': `Bearer ${token}`
    };
}

// Helper function for API calls with error handling
async function apiCall(url, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error completing request');
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error (${method} ${url}):`, error);
        showAlert(error.message, 'danger');
        throw error;
    }
}

// Handle logout functionality
document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.getElementById('logoutBtn');
    
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            
            try {
                await fetch('/logout', { method: 'POST' });
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/';
            } catch (error) {
                console.error('Logout error:', error);
                showAlert('Error logging out', 'danger');
            }
        });
    }
    
    // Update navigation menu based on user
    const updateNavigation = () => {
        const user = getCurrentUser();
        const loginMenuItem = document.querySelector('.nav-item a[href="/login"]')?.parentNode;
        const registerMenuItem = document.querySelector('.nav-item a[href="/register"]')?.parentNode;
        const userDropdown = document.querySelector('.nav-item .dropdown-toggle')?.parentNode;
        
        if (user) {
            // Hide login/register links
            if (loginMenuItem) loginMenuItem.style.display = 'none';
            if (registerMenuItem) registerMenuItem.style.display = 'none';
            
            // Show user dropdown
            if (userDropdown) {
                userDropdown.style.display = '';
                const userNameElement = userDropdown.querySelector('.dropdown-toggle');
                if (userNameElement) {
                    userNameElement.textContent = user.full_name;
                }
            }
        } else {
            // Show login/register links
            if (loginMenuItem) loginMenuItem.style.display = '';
            if (registerMenuItem) registerMenuItem.style.display = '';
            
            // Hide user dropdown
            if (userDropdown) userDropdown.style.display = 'none';
        }
    };
    
    // Call updateNavigation on page load
    updateNavigation();
});