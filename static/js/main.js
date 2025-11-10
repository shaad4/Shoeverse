// Mobile Menu Toggle
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const mobileMenu = document.getElementById('mobileMenu');

if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', () => {
        const isExpanded = mobileMenuBtn.getAttribute('aria-expanded') === 'true';
        mobileMenu.classList.toggle('hidden');
        mobileMenuBtn.setAttribute('aria-expanded', !isExpanded);
    });
}

// Sticky Search Bar
const searchWrap = document.getElementById('searchWrap');
const searchBar = document.getElementById('searchBar');
const navbar = document.querySelector('nav');
const container = searchWrap?.closest('.max-w-container');

if (searchWrap && searchBar && navbar && container) {
    const navbarHeight = navbar.offsetHeight;
    let isSticky = false;
    let originalWidth = 0;
    let offsetFromContainer = 0;

    const updateSticky = () => {
        const wrapRect = searchWrap.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        const shouldBeSticky = wrapRect.top <= navbarHeight;

        if (shouldBeSticky && !isSticky) {
            // Store original dimensions and offset from container
            if (originalWidth === 0) {
                const barRect = searchBar.getBoundingClientRect();
                originalWidth = searchBar.offsetWidth;
                // Calculate offset from container's left edge
                offsetFromContainer = barRect.left - containerRect.left;
            }
            
            // Calculate current position relative to container
            const currentContainerLeft = container.getBoundingClientRect().left;
            const stickyLeft = currentContainerLeft + offsetFromContainer;
            
            // Make search bar sticky with exact same width and position
            searchBar.classList.add('search-sticky');
            searchBar.style.top = `${navbarHeight}px`;
            searchBar.style.width = `${originalWidth}px`;
            searchBar.style.left = `${stickyLeft}px`;
            searchBar.style.right = 'auto';
            searchBar.style.transform = 'none';
            isSticky = true;
        } else if (!shouldBeSticky && isSticky) {
            // Remove sticky and restore original styles
            searchBar.classList.remove('search-sticky');
            searchBar.style.top = '';
            searchBar.style.width = '';
            searchBar.style.left = '';
            searchBar.style.right = '';
            searchBar.style.transform = '';
            isSticky = false;
            // Reset dimensions on next scroll up
            originalWidth = 0;
            offsetFromContainer = 0;
        }
    };

    // Use scroll event for more precise control
    window.addEventListener('scroll', updateSticky, { passive: true });
    window.addEventListener('resize', () => {
        // Reset on resize to recalculate
        if (isSticky) {
            originalWidth = 0;
            offsetFromContainer = 0;
            updateSticky();
        }
    });
    
    // Initial check
    updateSticky();
}

// Close mobile menu when clicking outside
document.addEventListener('click', (e) => {
    if (mobileMenu && mobileMenuBtn && !mobileMenu.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
        if (!mobileMenu.classList.contains('hidden')) {
            mobileMenu.classList.add('hidden');
            mobileMenuBtn.setAttribute('aria-expanded', 'false');
        }
    }
});

// Close mobile menu on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && mobileMenu && !mobileMenu.classList.contains('hidden')) {
        mobileMenu.classList.add('hidden');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        mobileMenuBtn.focus();
    }
});

