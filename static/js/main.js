// ==========================================
//  IGREJA — Main JS
// ==========================================

document.addEventListener('DOMContentLoaded', () => {

  // --- Navbar scroll effect ---
  const navbar = document.getElementById('navbar');
  const onScroll = () => {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // --- Mobile nav toggle ---
  const toggle  = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');
  const overlay = document.getElementById('navOverlay');
  const navClose = document.getElementById('navClose');

  function openMenu() {
    navLinks.classList.add('open');
    if (overlay) overlay.classList.add('open');
    if (navClose) navClose.style.display = 'flex';
    toggle.style.opacity = '0';
    toggle.style.pointerEvents = 'none';
    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    navLinks.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
    if (navClose) navClose.style.display = '';
    toggle.style.opacity = '';
    toggle.style.pointerEvents = '';
    document.body.style.overflow = '';
    document.querySelectorAll('.has-submenu.open').forEach(el => el.classList.remove('open'));
  }

  if (toggle && navLinks) {
    toggle.addEventListener('click', openMenu);
    navClose?.addEventListener('click', closeMenu);
    overlay?.addEventListener('click', closeMenu);
    window.addEventListener('resize', () => {
      if (window.innerWidth > 768) closeMenu();
    });
  }

  // --- Scroll reveal for elements ---
  const revealEls = document.querySelectorAll('.section-header, .value-item, .contact-item, .testimony-card');
  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    revealEls.forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
      revealObserver.observe(el);
    });
  }

  // --- Submenus mobile (desktop usa CSS :hover) ---
  document.querySelectorAll('.has-submenu > .nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
      if (window.innerWidth > 768) return;
      e.preventDefault();
      const li = this.closest('.has-submenu');
      const isOpen = li.classList.contains('open');
      document.querySelectorAll('.has-submenu.open').forEach(el => el.classList.remove('open'));
      if (!isOpen) li.classList.add('open');
    });
  });

  // --- Active nav link highlight ---
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

});


document.querySelectorAll('.btn-delete').forEach(btn => {
    btn.addEventListener('click', function () {
        const id = this.dataset.id;
        const name = this.dataset.name;

        document.getElementById('deleteText').innerText =
            `Deseja realmente excluir ${name}?`;

        document.getElementById('deleteForm').action =
            `/gerenciar-membros/${id}/excluir/`;

        document.getElementById('deleteModal').style.display = 'flex';
    });
});

function closeModal() {
    document.getElementById('deleteModal').style.display = 'none';
}


// ==========================================
//  Service Worker Registration
// ==========================================
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => {
        console.log('✓ SW registrado:', reg);
        // Verificar atualizações a cada 1 hora
        setInterval(() => reg.update(), 3600000);
      })
      .catch(err => console.log('✗ Erro ao registrar SW:', err));
  });
}

// Notificar usuário quando nova versão do app está disponível
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (confirm('Nova versão disponível! Deseja atualizar agora?')) {
      window.location.reload();
    }
  });
}


