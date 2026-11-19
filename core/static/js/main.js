/**
 * EEB ANTONIO ANTE - JavaScript Principal y Navegación
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Sombra suave en la barra de navegación al hacer scroll
    const navbar = document.getElementById('mainNavbar');
    
    if (navbar) {
        const handleScroll = () => {
            if (window.scrollY > 30) {
                navbar.classList.add('shadow-sm');
            } else {
                navbar.classList.remove('shadow-sm');
            }
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll();
    }

    // 2. Cerrar menú móvil al hacer clic en un enlace
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link:not(.dropdown-toggle)');
    const navbarCollapse = document.getElementById('navbarInstitutionalContent');

    if (navbarCollapse) {
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (navbarCollapse.classList.contains('show')) {
                    const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                    if (bsCollapse) {
                        bsCollapse.hide();
                    }
                }
            });
        });
    }

    console.log('✅ EEB Antonio Ante - Sistema web institucional cargado.');
});
