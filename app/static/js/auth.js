/**
 * Functions for authentication management
 */

// Set the Authorization header for all fetch requests
(function() {
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        const token = localStorage.getItem('token');
        if (token) {
            options.headers = options.headers || {};
            if (!options.headers['Authorization']) {
                options.headers['Authorization'] = `Bearer ${token}`;
            }
            // Also add a custom header for our middleware
            if (!options.headers['X-Auth-Token']) {
                options.headers['X-Auth-Token'] = token;
            }
        }
        return originalFetch(url, options);
    };
})();

// Add authentication check on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check for user in localStorage
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    const token = localStorage.getItem('token');
    
    // Update nav based on authentication status
    updateNavigation(user);
    
    // Add event handler for logging out
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Redirect to login if trying to access protected pages without auth
    const currentPath = window.location.pathname;
    if (currentPath === '/admin' && !user) {
        window.location.href = '/login';
    }
    
    // Handle admin link visibility
    const adminLink = document.querySelector('a[href="/admin"]');
    if (adminLink && user) {
        adminLink.style.display = user.role === 'admin' ? '' : 'none';
    }
});

// Function to update navigation menu based on authentication state
function updateNavigation(user) {
    const loginMenuItem = document.querySelector('.nav-item a[href="/login"]')?.parentNode;
    const registerMenuItem = document.querySelector('.nav-item a[href="/register"]')?.parentNode;
    const userDropdown = document.querySelector('.nav-item .dropdown-toggle')?.parentNode;
    const adminLink = document.querySelector('a[href="/admin"]');
    
    if (user) {
        // Hide login/register links
        if (loginMenuItem) loginMenuItem.style.display = 'none';
        if (registerMenuItem) registerMenuItem.style.display = 'none';
        
        // Show user dropdown
        if (userDropdown) {
            userDropdown.style.display = '';
            const userNameElement = userDropdown.querySelector('.dropdown-toggle');
            if (userNameElement) {
                userNameElement.textContent = user.full_name || user.username;
            }
        }
        
        // Show/hide admin link based on role
        if (adminLink) {
            adminLink.style.display = user.role === 'admin' ? '' : 'none';
        }
    } else {
        // Show login/register links
        if (loginMenuItem) loginMenuItem.style.display = '';
        if (registerMenuItem) registerMenuItem.style.display = '';
        
        // Hide user dropdown
        if (userDropdown) userDropdown.style.display = 'none';
        
        // Hide admin link
        if (adminLink) adminLink.style.display = 'none';
    }
}

// Function to handle logout
async function handleLogout(e) {
    e.preventDefault();
    
    try {
        await fetch('/logout', { method: 'POST' });
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/';
    } catch (error) {
        console.error('Logout error:', error);
        alert('Error logging out');
    }
} 