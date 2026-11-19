/**
 * EEB ANTONIO ANTE - JavaScript Principal
 */

document.addEventListener('DOMContentLoaded', () => {
  // Sombra dinámica en la barra de navegación al hacer scroll
  const navbar = document.querySelector('.navbar-institucional');
  
  if (navbar) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 30) {
        navbar.classList.add('shadow');
      } else {
        navbar.classList.remove('shadow');
      }
    });
  }

  // Inicializar tooltips de Bootstrap si están presentes
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  console.log('EEB Antonio Ante - Sistema web institucional cargado correctamente.');
});
