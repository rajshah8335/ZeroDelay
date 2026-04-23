/* ═══════════════════════════════════════════════════
   ZERODELAY — main.js (Shared logic for all pages)
   ═══════════════════════════════════════════════════ */

// ─── Intersection Observer for animations ─────────
document.addEventListener('DOMContentLoaded', () => {
  // Animate elements on scroll
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.animate-in, .feature-card, .step, .tech-item, .stat-card').forEach(el => {
    observer.observe(el);
  });

  // Hero stat counter animation
  animateStats();

  // Nav active state
  highlightActiveNav();
});

// ─── Active navigation link ──────────────────────
function highlightActiveNav() {
  const page = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    link.classList.toggle('active', href === page);
  });
}

// ─── Animated counter for hero stats ─────────────
function animateStats() {
  const targets = [
    { id: 'stat-routes', end: 12847, prefix: '', suffix: '' },
    { id: 'stat-cost', end: 2.4, prefix: '$', suffix: 'M' },
    { id: 'stat-time', end: 8420, prefix: '', suffix: 'h' },
    { id: 'stat-co2', end: 156, prefix: '', suffix: 'T' },
  ];

  targets.forEach(t => {
    const el = document.getElementById(t.id);
    if (!el) return;

    let start = 0;
    const duration = 2000;
    const step = (timestamp) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      const current = t.end * eased;

      if (Number.isInteger(t.end)) {
        el.textContent = t.prefix + Math.round(current).toLocaleString() + t.suffix;
      } else {
        el.textContent = t.prefix + current.toFixed(1) + t.suffix;
      }

      if (progress < 1) requestAnimationFrame(step);
    };

    // Delay start based on card position
    const card = el.closest('.stat-card');
    const delay = card ? parseInt(card.dataset.delay || 0) : 0;
    setTimeout(() => requestAnimationFrame(step), 400 + delay);
  });
}

// ─── Toast notification ──────────────────────────
function showToast(msg, color = '#00e5ff') {
  let el = document.getElementById('toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'toast';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.style.color = color;
  el.style.borderColor = color;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 3000);
}

// ─── Geocoding (Nominatim) ───────────────────────
const geoCache = {};
const geoTimers = {};

async function geocode(query) {
  if (geoCache[query]) return geoCache[query];
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`,
      { headers: { 'Accept': 'application/json' } }
    );
    const data = await res.json();
    if (data.length) {
      const result = {
        lat: parseFloat(data[0].lat),
        lng: parseFloat(data[0].lon),
        label: data[0].display_name.split(',').slice(0, 2).join(',').trim()
      };
      geoCache[query] = result;
      return result;
    }
  } catch (e) { /* silent */ }
  return null;
}

function liveGeocode(inputId, displayId) {
  clearTimeout(geoTimers[inputId]);
  geoTimers[inputId] = setTimeout(async () => {
    const val = document.getElementById(inputId).value.trim();
    const el = document.getElementById(displayId);
    if (!el) return;
    if (val.length < 3) {
      el.textContent = 'Enter location above';
      el.classList.remove('found');
      return;
    }
    el.textContent = 'Locating…';
    el.classList.remove('found');
    const res = await geocode(val);
    if (res) {
      el.textContent = `${res.lat.toFixed(4)}°, ${res.lng.toFixed(4)}° · ${res.label}`;
      el.classList.add('found');
      el.dataset.lat = res.lat;
      el.dataset.lng = res.lng;
    } else {
      el.textContent = 'Location not found';
      el.classList.remove('found');
    }
  }, 700);
}

// ─── Haversine Distance ──────────────────────────
function haversine(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ─── Format helpers ──────────────────────────────
function formatTime(hours) {
  if (hours > 48) {
    return Math.floor(hours / 24) + 'd ' + Math.round(hours % 24) + 'h';
  }
  return Math.round(hours) + 'h';
}

function formatCurrency(val) {
  return '$' + val.toLocaleString();
}
