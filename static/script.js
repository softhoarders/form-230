document.addEventListener('DOMContentLoaded', () => {
    const themeBtn = document.getElementById('theme-toggle');
    
    // Check local storage for theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.replace('light-mode', 'dark-mode');
    }

    // Theme Toggle
    themeBtn.addEventListener('click', () => {
        if (document.body.classList.contains('light-mode')) {
            document.body.classList.replace('light-mode', 'dark-mode');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.replace('dark-mode', 'light-mode');
            localStorage.setItem('theme', 'light');
        }
    });

    // Admin Panel Submissions Toggle
    const headers = document.querySelectorAll('.submission-header');
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const body = header.nextElementSibling;
            const isVisible = body.style.display === 'block';
            
            // Close all
            document.querySelectorAll('.submission-body').forEach(b => b.style.display = 'none');
            
            // Toggle current
            if (!isVisible) {
                body.style.display = 'block';
            }
        });
    });
});