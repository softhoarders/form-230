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

    // GDPR consent handling
    const gdprCheckbox = document.getElementById('gdpr-consent');
    const donateBtn = document.getElementById('donate-btn');
    
    if (gdprCheckbox && donateBtn) {
        gdprCheckbox.addEventListener('change', function() {
            donateBtn.disabled = !this.checked;
            if (this.checked) {
                donateBtn.classList.add('active');
            } else {
                donateBtn.classList.remove('active');
            }
        });
    }
});


// Signature Pad Logic
function initSignaturePad(canvasId, hiddenInputId, clearBtnId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const hiddenInput = document.getElementById(hiddenInputId);
    const clearBtn = document.getElementById(clearBtnId);

    function resizeCanvas() {
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
    }
    window.addEventListener('resize', resizeCanvas);
    setTimeout(resizeCanvas, 100);

    let isDrawing = false;
    let hasDrawn = false;

    function getCoordinates(e) {
        const rect = canvas.getBoundingClientRect();
        const clientX = e.clientX || (e.touches && e.touches[0].clientX);
        const clientY = e.clientY || (e.touches && e.touches[0].clientY);
        return {
            x: clientX - rect.left,
            y: clientY - rect.top
        };
    }

    function startDraw(e) {
        isDrawing = true;
        hasDrawn = true;
        const coords = getCoordinates(e);
        ctx.beginPath();
        ctx.moveTo(coords.x, coords.y);
        e.preventDefault();
    }

    function draw(e) {
        if (!isDrawing) return;
        const coords = getCoordinates(e);
        ctx.lineTo(coords.x, coords.y);
        ctx.stroke();
        e.preventDefault();
    }

    function stopDraw() {
        if (isDrawing) {
            isDrawing = false;
            updateHiddenInput();
        }
    }

    canvas.addEventListener('mousedown', startDraw);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDraw);
    canvas.addEventListener('mouseleave', stopDraw);

    canvas.addEventListener('touchstart', startDraw, {passive: false});
    canvas.addEventListener('touchmove', draw, {passive: false});
    canvas.addEventListener('touchend', stopDraw);

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            hiddenInput.value = '';
            hasDrawn = false;
        });
    }

    function updateHiddenInput() {
        if (hasDrawn) {
            hiddenInput.value = canvas.toDataURL('image/png');
        }
    }

    const form = canvas.closest('form');
    if (form) {
        form.addEventListener('submit', (e) => {
            if (!hasDrawn && window.location.pathname === '/') {
                e.preventDefault();
                alert('Vă rugăm să semnați înainte de a trimite. / Please provide a signature before submitting.');
            } else {
                updateHiddenInput();
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initSignaturePad('user-signature-pad', 'user_signature_base64', 'clear-signature');
    initSignaturePad('admin-signature-pad', 'signature_base64', 'clear-admin-signature');
});
