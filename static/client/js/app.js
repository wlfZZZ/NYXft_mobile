/* GLOBAL UTILITIES & LOGIC */

// 🛡️ SECURITY: Global Fetch Wrapper for CSRF Protection
const originalFetch = window.fetch;
window.fetch = async (...args) => {
    let [resource, config] = args;
    if (!config) config = {};
    if (!config.headers) config.headers = {};
    
    const method = (config.method || 'GET').toUpperCase();
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (token) {
            config.headers['X-CSRFToken'] = token;
        }
    }
    return originalFetch(resource, config);
};


/**
 * Premium Toast System
 * @param {string} message - Message to display
 * @param {string} type - 'success' | 'error' | 'warning' | 'info'
 */
const showToast = (message, type = 'success') => {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'ph-info';
    if (type === 'success') icon = 'ph-check-circle';
    if (type === 'error') icon = 'ph-warning-octagon';
    if (type === 'warning') icon = 'ph-warning';

    toast.innerHTML = `
        <i class="ph-bold ${icon} toast-icon"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Auto-remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
};

// Map legacy alert to toast
window.showAlert = showToast;
window.showToast = showToast;

document.addEventListener('DOMContentLoaded', () => {
    // Global Logout Handler (for navbar and hero)
    const logoutBtns = document.querySelectorAll('.logout-action');
    logoutBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const res = await fetch('/api/logout', { method: 'POST' });
                if (res.ok) {
                    window.location.href = '/auth?mode=login';
                }
            } catch (err) {
                // Silent fail or handle gracefully
            }
        });
    });

    // Global glass button hover effects (optional polish)
    const glassBtns = document.querySelectorAll('.btn-glass');
    glassBtns.forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            btn.style.transform = 'translateY(-2px)';
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = 'translateY(0)';
        });
    });

    // Mobile Menu Toggle
    const menuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    
    if (menuBtn && navLinks) {
        menuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            const icon = menuBtn.querySelector('i');
            if (navLinks.classList.contains('active')) {
                icon.className = 'ph-bold ph-x';
            } else {
                icon.className = 'ph-bold ph-list';
            }
        });

        // Close when a link is clicked
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
                menuBtn.querySelector('i').className = 'ph-bold ph-list';
            });
        });
    }

    // ════ NYX NATIVE SHEET GLOBAL DISMISSAL ════
    const sheetOverlay = document.querySelector('.nyx-sheet-overlay');
    if (sheetOverlay) {
        sheetOverlay.addEventListener('click', () => NYXSheet.close());
    }
});

/**
 * NYX Native Sheet Controller
 */
const NYXSheet = {
    open: (id) => {
        const sheet = document.getElementById(id);
        const overlay = document.querySelector('.nyx-sheet-overlay');
        if (!sheet || !overlay) return;
        
        overlay.classList.add('active');
        sheet.classList.add('active');
        document.body.style.overflow = 'hidden'; // Lock background scroll
        if (navigator.vibrate) navigator.vibrate(10); // Subtle tactile feedback
    },
    close: () => {
        const activeSheet = document.querySelector('.nyx-sheet.active');
        const overlay = document.querySelector('.nyx-sheet-overlay');
        if (activeSheet) activeSheet.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        document.body.style.overflow = ''; // Restore background scroll
    }
};
window.NYXSheet = NYXSheet;

/**
 * Animate Number Counter
 * @param {HTMLElement} obj - The element to animate
 * @param {number} start - Starting value
 * @param {number} end - Ending value
 * @param {number} duration - Animation duration in ms
 */
function animateValue(obj, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start).toLocaleString();
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Export for use in templates
window.animateValue = animateValue;
