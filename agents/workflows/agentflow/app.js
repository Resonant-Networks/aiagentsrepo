'use strict';

/* =============================================================================
   AgentFlow Landing — app.js
   Modern vanilla JS (ES2022+), no dependencies.
   Features:
     1. Sticky navbar shadow + background on scroll
     2. Mobile hamburger menu toggle
     3. Scroll-reveal animations via IntersectionObserver (.reveal -> .visible)
     4. Smooth scroll for anchor links
     5. Contact form handler (prevent default, inline success message, no backend)
     6. Subtle hero parallax via requestAnimationFrame
   ========================================================================== */

/* ------------------------------------------------------------------ helpers */
const qs = (selector, scope = document) => scope.querySelector(selector);
const qsa = (selector, scope = document) => [...scope.querySelectorAll(selector)];

/* --------------------------------------------------------------- 1. navbar */
function initStickyNavbar() {
  const navbar = qs('[data-navbar], .navbar');
  if (!navbar) return;

  const addShadowClass = () => {
    if (window.scrollY > 10 || document.documentElement.scrollTop > 10) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  };

  // Run once on load, then on every scroll (throttled via rAF in parallax).
  addShadowClass();
  window.addEventListener('scroll', addShadowClass, { passive: true });
}

/* ---------------------------------------------------------- 2. hamburger */
function initMobileMenu() {
  const toggle = qs('[data-menu-toggle], #hamburger, .menu-toggle');
  const menu = qs('[data-menu], .nav-links, .mobile-menu');
  if (!toggle || !menu) return;

  toggle.addEventListener('click', (event) => {
    event.preventDefault();
    const isOpen = menu.classList.toggle('open');
    toggle.classList.toggle('is-active', isOpen);
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });

  // Close the menu when a link inside it is clicked.
  qsa('a', menu).forEach((link) => {
    link.addEventListener('click', () => {
      menu.classList.remove('open');
      toggle.classList.remove('is-active');
      toggle.setAttribute('aria-expanded', 'false');
    });
  });
}

/* ------------------------------------------------- 3. scroll-reveal */
function initScrollReveal() {
  const revealEls = qsa('.reveal');

  if (!('IntersectionObserver' in window)) {
    // Degrade gracefully: show everything immediately.
    revealEls.forEach((el) => el.classList.add('visible'));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
  );

  revealEls.forEach((el) => observer.observe(el));
}

/* ------------------------------------------------------ 4. smooth scroll */
function initSmoothScroll() {
  qsa('a[href^="#"]').forEach((link) => {
    link.addEventListener('click', (event) => {
      const href = link.getAttribute('href');
      if (href === '#') return; // `href="#"` is a placeholder, not an anchor.

      const target = qs(href);
      if (!target) return;

      event.preventDefault();

      const navOffset = qs('[data-navbar], .navbar')?.offsetHeight ?? 0;
      const top = target.getBoundingClientRect().top + window.scrollY - navOffset;

      window.scrollTo({ top, behavior: 'smooth' });

      // Keep focus on the section for a11y.
      history.replaceState(null, '', href);
    });
  });
}

/* ----------------------------------------------------- 5. contact form */
function initContactForm() {
  const form = qs('[data-contact-form], .contact-form, #contact-form');
  if (!form) return;

  form.addEventListener('submit', (event) => {
    event.preventDefault();

    const success = qs('[data-form-success], .form-success, #form-success', form) ?? makeSuccessDiv(form);
    success.classList.add('visible');
    success.setAttribute('role', 'status');

    const submitBtn = qs('button[type="submit"]', form);
    if (submitBtn) submitBtn.setAttribute('disabled', 'true');

    form.reset();
  });
}

/* Build + insert a success div if the page didn't ship one. */
function makeSuccessDiv(form) {
  const div = document.createElement('div');
  div.className = 'form-success';
  div.id = 'form-success';
  div.textContent = 'Thanks! Your message has been received — we’ll be in touch shortly.';
  form.after(div);
  return div;
}

/* ------------------------------------------------------ 6. hero parallax */
function initHeroParallax() {
  const hero = qs('[data-parallax], .hero');
  if (!hero) return;

  const bg = hero.querySelector('[data-parallax-bg], .hero-bg, .hero__bg') ?? hero;

  let ticking = false;
  let heroTop = hero.getBoundingClientRect().top;

  // Cache hero geometry; it doesn't move horizontally and only shifts on resize.
  const updateGeometry = () => {
    heroTop = hero.getBoundingClientRect().top;
  };

  const applyParallax = () => {
    // Distance scrolled relative to the hero's position (never leaves where it started).
    const distance = Math.max(-window.scrollY - heroTop, 0);
    bg.style.transform = `translate3d(0, ${distance * 0.35}px, 0)`;
    ticking = false;
  };

  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(applyParallax);
  };

  const onResize = () => {
    updateGeometry();
    applyParallax();
  };

  updateGeometry();
  applyParallax();
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onResize, { passive: true });
}

/* ---------------------------------------------------------------- boot */
const init = () => {
  initStickyNavbar();
  initMobileMenu();
  initScrollReveal();
  initSmoothScroll();
  initContactForm();
  initHeroParallax();
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}