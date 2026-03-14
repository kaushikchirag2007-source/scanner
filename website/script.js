/**
 * script.js — Body Outline Scanner Website
 * Handles: cursor glow, navbar scroll, reveal on scroll,
 *          animated stat counters, style card interaction, copy buttons.
 */

/* ── Custom cursor ────────────────────────────────────── */
const cursorGlow = document.getElementById('cursorGlow');

document.addEventListener('mousemove', e => {
  cursorGlow.style.left = e.clientX + 'px';
  cursorGlow.style.top  = e.clientY + 'px';
});

document.addEventListener('mousedown', () => {
  cursorGlow.style.width  = '48px';
  cursorGlow.style.height = '48px';
});
document.addEventListener('mouseup', () => {
  cursorGlow.style.width  = '28px';
  cursorGlow.style.height = '28px';
});

/* ── Navbar scroll effect ─────────────────────────────── */
const navbar = document.getElementById('navbar');

window.addEventListener('scroll', () => {
  if (window.scrollY > 40) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
}, { passive: true });

/* ── Scroll-reveal ────────────────────────────────────── */
const revealEls = document.querySelectorAll('.reveal');

const revealObserver = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
);

revealEls.forEach(el => revealObserver.observe(el));

/* ── Animated stat counters ───────────────────────────── */
function animateCounter(el) {
  const target = parseInt(el.dataset.target, 10);
  const duration = 1400;
  const start = performance.now();

  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    // Ease-out quad
    const eased = 1 - (1 - progress) * (1 - progress);
    el.textContent = Math.round(eased * target);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

const statVals = document.querySelectorAll('.stat-val');
const statsObserver = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        statsObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.5 }
);
statVals.forEach(el => statsObserver.observe(el));

/* ── Style cards — click to activate ─────────────────── */
const styleCards = document.querySelectorAll('.style-card');

styleCards.forEach(card => {
  card.addEventListener('click', () => {
    styleCards.forEach(c => {
      c.classList.remove('active');
      c.querySelector('.preview-label') && 
        c.querySelector('.preview-label').remove();
    });
    card.classList.add('active');
    const preview = card.querySelector('.style-preview');
    const lbl = document.createElement('div');
    lbl.className = 'preview-label';
    lbl.textContent = 'Active';
    preview.appendChild(lbl);
  });
});

/* ── Copy-to-clipboard buttons ────────────────────────── */
document.querySelectorAll('.copy-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const text = btn.dataset.copy;
    try {
      await navigator.clipboard.writeText(text);
      const orig = btn.textContent;
      btn.textContent = '✓';
      btn.style.borderColor = 'var(--neon)';
      btn.style.color = 'var(--neon)';
      setTimeout(() => {
        btn.textContent = orig;
        btn.style.borderColor = '';
        btn.style.color = '';
      }, 1800);
    } catch {
      btn.textContent = '✗';
      setTimeout(() => { btn.textContent = '⧉'; }, 1500);
    }
  });
});

/* ── Active nav link highlighting ─────────────────────── */
const sections = document.querySelectorAll('section[id], .section[id]');
const navLinks = document.querySelectorAll('.nav-links a');

const sectionObserver = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        navLinks.forEach(a => {
          a.style.color = a.getAttribute('href') === `#${id}`
            ? 'var(--neon)'
            : '';
        });
      }
    });
  },
  { threshold: 0.45 }
);
sections.forEach(s => sectionObserver.observe(s));

/* ── Smooth nav cursor reset (links and buttons) ───────── */
document.querySelectorAll('a, button').forEach(el => {
  el.style.cursor = 'none';
  el.addEventListener('mouseenter', () => {
    cursorGlow.style.width  = '42px';
    cursorGlow.style.height = '42px';
    cursorGlow.style.background =
      'radial-gradient(circle, rgba(0,245,255,0.7) 0%, transparent 70%)';
  });
  el.addEventListener('mouseleave', () => {
    cursorGlow.style.width  = '28px';
    cursorGlow.style.height = '28px';
    cursorGlow.style.background =
      'radial-gradient(circle, rgba(0,255,65,0.65) 0%, transparent 70%)';
  });
});
