// StudyMate AI - Theme Controller (Dark Mode / Light Mode)

function applyTheme(theme) {
    const isLight = (theme === 'light');
    if (isLight) {
        document.body.classList.add('light-mode');
        document.body.classList.remove('dark-mode');
    } else {
        document.body.classList.remove('light-mode');
        document.body.classList.add('dark-mode');
    }

    // Update all toggle buttons on page
    const toggleBtns = document.querySelectorAll('.theme-toggle-btn, #themeToggleBtn');
    toggleBtns.forEach(btn => {
        if (isLight) {
            btn.innerHTML = '🌙 Dark Mode';
            btn.classList.remove('btn-dark');
            btn.classList.add('btn-outline-dark');
        } else {
            btn.innerHTML = '☀️ Light Mode';
            btn.classList.add('btn-dark');
            btn.classList.remove('btn-outline-dark');
        }
    });
}

function toggleDarkMode() {
    const currentlyLight = document.body.classList.contains('light-mode');
    const newTheme = currentlyLight ? 'dark' : 'light';
    localStorage.setItem('studymate_theme', newTheme);
    applyTheme(newTheme);
}

// Immediate theme execution on script load
(function() {
    const savedTheme = localStorage.getItem('studymate_theme') || 'dark';
    applyTheme(savedTheme);
})();

// Re-apply once DOM is loaded to ensure all buttons are updated and mobile sidebar is initialized
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('studymate_theme') || 'dark';
    applyTheme(savedTheme);

    // Auto-initialize mobile menu toggle for all templates
    const sidebar = document.querySelector('.sidebar');
    const logo = document.querySelector('.sidebar .logo');
    const menu = document.querySelector('.sidebar .sidebar-menu');
    
    if (logo && menu && !document.getElementById('mobileMenuToggleBtn')) {
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'mobileMenuToggleBtn';
        toggleBtn.className = 'btn btn-sm btn-outline-light d-md-none';
        toggleBtn.type = 'button';
        toggleBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
        toggleBtn.style.padding = '4px 10px';
        toggleBtn.style.fontSize = '14px';
        toggleBtn.style.borderRadius = '8px';
        
        toggleBtn.onclick = function(e) {
            e.stopPropagation();
            menu.classList.toggle('show');
            toggleBtn.innerHTML = menu.classList.contains('show') ? '<i class="fa-solid fa-xmark"></i>' : '<i class="fa-solid fa-bars"></i>';
        };
        
        logo.style.display = 'flex';
        logo.style.justifyContent = 'space-between';
        logo.style.alignItems = 'center';
        logo.appendChild(toggleBtn);
        
        logo.onclick = function() {
            if (window.innerWidth <= 768) {
                menu.classList.toggle('show');
                toggleBtn.innerHTML = menu.classList.contains('show') ? '<i class="fa-solid fa-xmark"></i>' : '<i class="fa-solid fa-bars"></i>';
            }
        };
    }
});
