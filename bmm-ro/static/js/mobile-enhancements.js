// File: bmm-ro/static/js/mobile-enhancements.js
// Revision: 1.0 - Mobile interaction improvements

document.addEventListener('DOMContentLoaded', function() {
    // Improve table scrolling feedback on mobile
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
        let isScrolling = false;
        table.addEventListener('scroll', function() {
            if (!isScrolling) {
                table.style.boxShadow = '0 4px 15px rgba(0,0,0,0.15)';
                isScrolling = true;
                setTimeout(() => {
                    table.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                    isScrolling = false;
                }, 150);
            }
        });
    });

    // Auto-collapse navbar on mobile after link selection
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992 && navbarCollapse.classList.contains('show')) {
                bootstrap.Collapse.getInstance(navbarCollapse).hide();
            }
        });
    });

    // Optimize for device orientation changes
    window.addEventListener('orientationchange', function() {
        setTimeout(() => {
            window.scrollTo(0, 0);
        }, 100);
    });

    // Add touch feedback for buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.98)';
        });
        
        button.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
    });
});