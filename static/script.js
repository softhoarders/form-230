document.addEventListener('DOMContentLoaded', () => {
    const themeBtn = document.getElementById('theme-toggle');
    
    // Check local storage for theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-mode');
    }

    // Theme Toggle with cover effect
    themeBtn.addEventListener('click', () => {
        document.body.classList.add('theme-transitioning');
        
        setTimeout(() => {
            if (document.body.classList.contains('light-mode')) {
                document.body.classList.remove('light-mode');
                localStorage.setItem('theme', 'dark');
            } else {
                document.body.classList.add('light-mode');
                localStorage.setItem('theme', 'light');
            }
            
            setTimeout(() => {
                document.body.classList.remove('theme-transitioning');
            }, 50);
        }, 500); // Wait for cover config
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