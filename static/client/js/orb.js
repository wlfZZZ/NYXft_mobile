// ════ NYX PERFORMANCE OS: DYNAMIC ORB NAVIGATION (ASSISTIVETOUCH ARCHITECTURE) ════
document.addEventListener('DOMContentLoaded', () => {
    let navItems = [];

    // 1. FETCH SYSTEM NAVIGATION REGISTRY
    async function initOrb() {
        try {
            const res = await fetch('/api/nav');
            navItems = await res.json();
            renderOrb();
        } catch (err) {
            console.error('System Uplink Failed: Navigation Registry Unreachable');
        }
    }

    function renderOrb() {
        if (document.getElementById('nyxOrbContainer')) return;

        const currentPath = window.location.pathname;
        
        const orbOverlayHTML = `
            <div id="nyxOrbOverlay" class="nyx-orb-overlay">
                <div class="nyx-orb-menu">
                    ${navItems.map(item => `
                        <a href="${item.url}" 
                           class="nyx-orb-item ${item.class || ''} ${item.id === 'lock' ? 'lock-trigger' : ''} ${currentPath === item.url ? 'active-route' : ''}"
                           data-id="${item.id}">
                            <i class="ph-bold ${item.icon}"></i>
                            <span class="nyx-orb-label">${item.label}</span>
                        </a>
                    `).join('')}
                </div>
            </div>
            <div id="nyxOrbContainer" class="nyx-orb-container">
                <div id="nyxOrbBtn" class="nyx-orb-btn"></div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', orbOverlayHTML);
        setupOrbInteractions();
    }

    function setupOrbInteractions() {
        const orb = document.getElementById('nyxOrbContainer');
        const overlay = document.getElementById('nyxOrbOverlay');
        
        let isDragging = false;
        let dragStarted = false;
        let startX, startY, orbX, orbY;
        let idleTimer;

        // Load saved position
        const savedPos = JSON.parse(localStorage.getItem('nyx_orb_pos')) || {
            x: window.innerWidth - 65,
            y: window.innerHeight - 150
        };
        
        orb.style.left = savedPos.x + 'px';
        orb.style.top = savedPos.y + 'px';

        // 2. IDLE & BREATHING LOGIC
        function resetIdleTimer() {
            orb.classList.remove('idle');
            clearTimeout(idleTimer);
            idleTimer = setTimeout(() => {
                if (!overlay.classList.contains('open')) {
                    orb.classList.add('idle');
                }
            }, 4000);
        }

        // 3. PHYSICS-BASED DRAGGING
        function onTouchStart(e) {
            dragStarted = true;
            isDragging = false;
            const touch = e.touches[0];
            startX = touch.clientX;
            startY = touch.clientY;
            const rect = orb.getBoundingClientRect();
            orbX = rect.left;
            orbY = rect.top;
            
            orb.style.transition = 'none';
            orb.classList.remove('idle', 'stealth');
        }

        function onTouchMove(e) {
            if (!dragStarted) return;
            
            const touch = e.touches[0];
            const dx = touch.clientX - startX;
            const dy = touch.clientY - startY;

            if (Math.abs(dx) > 10 || Math.abs(dy) > 10) {
                isDragging = true;
                let newX = orbX + dx;
                let newY = orbY + dy;

                newX = Math.max(10, Math.min(newX, window.innerWidth - 60));
                newY = Math.max(10, Math.min(newY, window.innerHeight - 60));

                orb.style.left = newX + 'px';
                orb.style.top = newY + 'px';
                
                if (e.cancelable) e.preventDefault();
            }
        }

        function onTouchEnd() {
            if (!dragStarted) return;
            dragStarted = false;

            if (isDragging) {
                snapToEdges();
            } else {
                toggleMenu();
            }
            resetIdleTimer();
        }

        function snapToEdges() {
            const rect = orb.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const targetX = centerX < window.innerWidth / 2 ? 15 : window.innerWidth - 65;
            
            orb.style.transition = 'all 0.6s cubic-bezier(0.19, 1, 0.22, 1)';
            orb.style.left = targetX + 'px';
            
            setTimeout(() => {
                const finalRect = orb.getBoundingClientRect();
                localStorage.setItem('nyx_orb_pos', JSON.stringify({
                    x: finalRect.left,
                    y: finalRect.top
                }));
                isDragging = false;
            }, 600);
        }

        // 5. MENU CONTROLLER (RELATIVE EXPANSION)
        function toggleMenu() {
            const isOpen = overlay.classList.toggle('open');
            if (isOpen) {
                const rect = orb.getBoundingClientRect();
                const menu = overlay.querySelector('.nyx-orb-menu');
                const isLeft = rect.left < window.innerWidth / 2;
                const isTop = rect.top < window.innerHeight / 2;
                
                menu.style.transformOrigin = `${isLeft ? 'left' : 'right'} ${isTop ? 'top' : 'bottom'}`;
                menu.style.position = 'absolute';
                menu.style.left = isLeft ? '20px' : 'auto';
                menu.style.right = isLeft ? 'auto' : '20px';
                menu.style.top = isTop ? '20px' : 'auto';
                menu.style.bottom = isTop ? 'auto' : '20px';
                
                orb.classList.remove('idle');
                if (navigator.vibrate) navigator.vibrate(10);
            } else {
                resetIdleTimer();
            }
        }

        // 6. LOCK PROTOCOL HANDLER (SUBTLE APERTURE)
        document.addEventListener('click', (e) => {
            const lockBtn = e.target.closest('.lock-trigger');
            if (lockBtn) {
                e.preventDefault();
                // Subtle Visual Lock
                document.body.classList.add('nyx-locking');
                if (navigator.vibrate) navigator.vibrate(20); 
                toggleMenu();
                
                setTimeout(() => {
                    window.location.href = '/auth';
                }, 400);
            }
        });

        // SCROLL STEALTH
        let scrollStopTimer;
        window.addEventListener('scroll', () => {
            if (overlay.classList.contains('open')) return;
            orb.classList.add('stealth');
            clearTimeout(scrollStopTimer);
            scrollStopTimer = setTimeout(() => orb.classList.remove('stealth'), 500);
        }, { passive: true });

        // EVENT LISTENERS
        orb.addEventListener('touchstart', onTouchStart, { passive: false });
        document.addEventListener('touchmove', onTouchMove, { passive: false });
        document.addEventListener('touchend', onTouchEnd);
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) toggleMenu();
        });

        window.addEventListener('resize', () => {
            const rect = orb.getBoundingClientRect();
            const newX = rect.left > window.innerWidth / 2 ? window.innerWidth - 65 : 15;
            const newY = Math.min(rect.top, window.innerHeight - 65);
            orb.style.left = newX + 'px';
            orb.style.top = newY + 'px';
        });

        resetIdleTimer();
    }

    // Initialize the Orb system
    initOrb();
});
