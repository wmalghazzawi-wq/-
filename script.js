/**
 * NanoWorld — Main JavaScript
 * Particle system, animations, interactivity
 */

// ============================================================
// PARTICLE SYSTEM
// ============================================================
const canvas = document.getElementById('particles-canvas');
const ctx = canvas.getContext('2d');

let particles = [];
const PARTICLE_COUNT = 80;
const CONNECT_DIST = 140;

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

class Particle {
  constructor() { this.reset(true); }

  reset(init = false) {
    this.x = Math.random() * canvas.width;
    this.y = init ? Math.random() * canvas.height : canvas.height + 10;
    this.vx = (Math.random() - 0.5) * 0.4;
    this.vy = -(Math.random() * 0.5 + 0.1);
    this.radius = Math.random() * 2 + 0.5;
    this.alpha = Math.random() * 0.5 + 0.1;
    const colors = ['0, 247, 255', '59, 130, 246', '168, 85, 247', '255, 107, 53'];
    this.color = colors[Math.floor(Math.random() * colors.length)];
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;
    if (this.y < -10) this.reset();
  }

  draw() {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${this.color}, ${this.alpha})`;
    ctx.fill();
  }
}

function initParticles() {
  particles = Array.from({ length: PARTICLE_COUNT }, () => new Particle());
}

function drawConnections() {
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x;
      const dy = particles[i].y - particles[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < CONNECT_DIST) {
        const opacity = (1 - dist / CONNECT_DIST) * 0.15;
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(particles[j].x, particles[j].y);
        ctx.strokeStyle = `rgba(0, 247, 255, ${opacity})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }
    }
  }
}

function animateParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawConnections();
  particles.forEach(p => { p.update(); p.draw(); });
  requestAnimationFrame(animateParticles);
}

initParticles();
animateParticles();

// ============================================================
// NAVBAR SCROLL EFFECT
// ============================================================
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 60) navbar.classList.add('scrolled');
  else navbar.classList.remove('scrolled');
}, { passive: true });

// ============================================================
// HAMBURGER MENU
// ============================================================
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');
if (hamburger && navLinks) {
  hamburger.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    // Animate hamburger
    const spans = hamburger.querySelectorAll('span');
    if (navLinks.classList.contains('open')) {
      spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
      spans[1].style.opacity = '0';
      spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
    } else {
      spans.forEach(s => { s.style.transform = ''; s.style.opacity = ''; });
    }
  });

  // Close menu on link click
  navLinks.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      const spans = hamburger.querySelectorAll('span');
      spans.forEach(s => { s.style.transform = ''; s.style.opacity = ''; });
    });
  });
}

// ============================================================
// ANIMATE-IN ON LOAD (Hero section)
// ============================================================
window.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    document.querySelectorAll('.animate-in').forEach(el => {
      el.classList.add('visible');
    });
  }, 100);
});

// ============================================================
// SCROLL REVEAL
// ============================================================
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12, rootMargin: '0px 0px -50px 0px' });

document.addEventListener('DOMContentLoaded', () => {
  // Add reveal class to elements we want to animate on scroll
  const revealTargets = document.querySelectorAll(
    '.info-card, .material-card, .app-item, .material-detail, .mox-card, .prop-card, .footer-col, .about-text, .feature-row, .app-domain-card, .xrd-intro, .xrd-card'
  );
  revealTargets.forEach((el, i) => {
    el.classList.add('reveal');
    el.style.transitionDelay = `${(i % 4) * 0.1}s`;
    revealObserver.observe(el);
  });
});

// ============================================================
// COUNTER ANIMATION
// ============================================================
function animateCounter(el) {
  const target = parseInt(el.dataset.target);
  const duration = 1800;
  const step = target / (duration / 16);
  let current = 0;

  const timer = setInterval(() => {
    current += step;
    if (current >= target) {
      current = target;
      clearInterval(timer);
    }
    el.textContent = Math.floor(current);
  }, 16);
}

const statsObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.querySelectorAll('.stat-num[data-target]').forEach(animateCounter);
      statsObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

const heroStats = document.querySelector('.hero-stats');
if (heroStats) statsObserver.observe(heroStats);

// ============================================================
// DID YOU KNOW SLIDER
// ============================================================
const dykSlider = document.getElementById('dykSlider');
const dykDots = document.getElementById('dykDots');

if (dykSlider && dykDots) {
  const facts = dykSlider.querySelectorAll('.dyk-fact');
  let currentFact = 0;

  // Build dots
  facts.forEach((_, i) => {
    const btn = document.createElement('button');
    btn.classList.add('dyk-dot-btn');
    if (i === 0) btn.classList.add('active');
    btn.setAttribute('aria-label', `Fact ${i + 1}`);
    btn.addEventListener('click', () => goToFact(i));
    dykDots.appendChild(btn);
  });

  function goToFact(n) {
    facts[currentFact].classList.remove('active');
    dykDots.children[currentFact].classList.remove('active');
    currentFact = n;
    facts[currentFact].classList.add('active');
    dykDots.children[currentFact].classList.add('active');
  }

  // Auto-advance
  setInterval(() => {
    goToFact((currentFact + 1) % facts.length);
  }, 4500);
}

// ============================================================
// MATERIAL FILTER (nanomaterials.html)
// ============================================================
const filterBtns = document.querySelectorAll('.filter-btn');
const materialCards = document.querySelectorAll('.material-detail');

if (filterBtns.length && materialCards.length) {
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      // Update active button
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.dataset.filter;

      materialCards.forEach(card => {
        const dims = (card.dataset.dims || '').split(' ');
        if (filter === 'all' || dims.includes(filter)) {
          card.removeAttribute('data-hidden');
          card.style.display = '';
          // Trigger reveal animation
          setTimeout(() => card.classList.add('visible'), 50);
        } else {
          card.setAttribute('data-hidden', '');
          card.style.display = 'none';
        }
      });
    });
  });
}

// ============================================================
// SMOOTH ANCHOR SCROLL (for hash links like #carbon-nanotubes)
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  if (window.location.hash) {
    setTimeout(() => {
      const target = document.querySelector(window.location.hash);
      if (target) {
        const navH = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-h')) || 72;
        const top = target.getBoundingClientRect().top + window.scrollY - navH - 20;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    }, 300);
  }
});

// ============================================================
// MATERIAL CARD GLOW EFFECT (follows mouse)
// ============================================================
document.querySelectorAll('.material-card, .mox-card, .glass-card').forEach(card => {
  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    card.style.background = `radial-gradient(circle at ${x}% ${y}%, rgba(0,247,255,0.04) 0%, rgba(10, 20, 45, 0.7) 60%)`;
  });
  card.addEventListener('mouseleave', () => {
    card.style.background = '';
  });
});

// ============================================================
// ACTIVE NAV LINK HIGHLIGHT ON SCROLL
// ============================================================
const sections = document.querySelectorAll('section[id]');
const navLinkEls = document.querySelectorAll('.nav-link');

const sectionObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinkEls.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').includes(entry.target.id)) {
          link.classList.add('active');
        }
      });
    }
  });
}, { threshold: 0.4 });

sections.forEach(s => sectionObserver.observe(s));

// ============================================================
// PAGE LOAD FADE IN
// ============================================================
document.body.style.opacity = '0';
document.body.style.transition = 'opacity 0.5s ease';
window.addEventListener('load', () => {
  document.body.style.opacity = '1';
});

// ============================================================
// AI IMAGE PREDICTION (index.html)
// ============================================================
const predictInput = document.getElementById('predictImage');
const predictBtn = document.getElementById('predictBtn');
const predictStatus = document.getElementById('predictStatus');
const predictResult = document.getElementById('predictResult');
const predictLabel = document.getElementById('predictLabel');
const predictConfidence = document.getElementById('predictConfidence');
const predictConfidenceFill = document.getElementById('predictConfidenceFill');
const predictTopList = document.getElementById('predictTopList');
const predictPreview = document.getElementById('predictPreview');
const predictPreviewWrap = document.getElementById('predictPreviewWrap');
const uploadDropzone = document.getElementById('uploadDropzone');

if (predictInput && predictBtn && predictStatus) {
  let selectedFile = null;
  let isPredicting = false;
  let previewUrl = null;

  function setStatus(message, isError = false) {
    predictStatus.textContent = message;
    predictStatus.classList.toggle('error', isError);
  }

  function setLoading(loading) {
    isPredicting = loading;
    predictBtn.disabled = loading;
    predictBtn.classList.toggle('is-loading', loading);
  }

  function clearResult() {
    if (predictResult) predictResult.hidden = true;
    if (predictTopList) predictTopList.innerHTML = '';
    if (predictConfidenceFill) predictConfidenceFill.style.width = '0%';
  }

  function showPreview(file) {
    if (!predictPreview || !predictPreviewWrap) return;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(file);
    predictPreview.src = previewUrl;
    predictPreviewWrap.classList.add('visible');
  }

  async function runPrediction() {
    if (!selectedFile) {
      setStatus('اختر صورة أولاً ثم أعد المحاولة.', true);
      return;
    }
    if (isPredicting) return;

    try {
      setLoading(true);
      setStatus('جاري تحليل الصورة...');
      clearResult();

      const formData = new FormData();
      formData.append('image', selectedFile);

      const response = await fetch('/predict', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || 'تعذر تنفيذ التنبؤ.');
      }

      const confidence = Number(result.confidence || 0) * 100;

      if (predictLabel) predictLabel.textContent = result.predicted_class;
      if (predictConfidence) predictConfidence.textContent = `${confidence.toFixed(2)}%`;
      if (predictConfidenceFill) {
        predictConfidenceFill.style.width = `${Math.max(0, Math.min(confidence, 100)).toFixed(2)}%`;
      }

      if (predictTopList) {
        predictTopList.innerHTML = '';
        (result.top_predictions || []).forEach((item) => {
          const li = document.createElement('li');
          const conf = Number(item.confidence || 0) * 100;
          li.innerHTML = `<span>${item.class_name}</span><strong>${conf.toFixed(2)}%</strong>`;
          predictTopList.appendChild(li);
        });
      }

      if (predictResult) predictResult.hidden = false;
      setStatus('تم التنبؤ بنجاح.');
    } catch (error) {
      setStatus(error.message || 'حدث خطأ أثناء التنبؤ.', true);
    } finally {
      setLoading(false);
    }
  }

  function onFileSelected(file) {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setStatus('الملف ليس صورة صالحة.', true);
      selectedFile = null;
      clearResult();
      return;
    }

    selectedFile = file;
    clearResult();
    showPreview(file);
    setStatus(`تم اختيار الصورة: ${file.name}. اضغط "ابدأ التنبؤ".`);
  }

  predictInput.addEventListener('change', (event) => {
    const file = event.target.files && event.target.files[0];
    onFileSelected(file);
  });

  if (uploadDropzone) {
    ['dragenter', 'dragover'].forEach((eventName) => {
      uploadDropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        uploadDropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach((eventName) => {
      uploadDropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        uploadDropzone.classList.remove('dragover');
      });
    });

    uploadDropzone.addEventListener('drop', (event) => {
      const file = event.dataTransfer.files && event.dataTransfer.files[0];
      if (predictInput && file) {
        const dt = new DataTransfer();
        dt.items.add(file);
        predictInput.files = dt.files;
      }
      onFileSelected(file);
    });
  }

  predictBtn.addEventListener('click', runPrediction);
}
