// PROTOTYPE — Stage Switcher UI Variations
// Throwaway component. Switch between variants via ?variant=A/B/C.
// Floating bottom bar. Keyboard arrows cycle. Shareable URLs.

(function() {
  const variants = [
    { key: 'A', name: 'Popover Dropdown' },
    { key: 'B', name: 'Sidebar Context' },
    { key: 'C', name: 'Stage Cards Overview' },
  ];

  const url = new URL(window.location.href);
  const currentKey = url.searchParams.get('variant') || 'A';
  const currentIdx = variants.findIndex(v => v.key === currentKey);
  const current = variants[currentIdx === -1 ? 0 : currentIdx];

  function switchVariant(delta) {
    const nextIdx = (currentIdx + delta + variants.length) % variants.length;
    const next = variants[nextIdx];
    const url = new URL(window.location.href);
    url.searchParams.set('variant', next.key);
    window.location.href = url.toString();
  }

  // Inject switcher bar
  const bar = document.createElement('div');
  bar.className = 'prototype-switcher-bar';
  bar.innerHTML = `
    <button class="proto-switcher-btn" id="proto-prev" aria-label="Vorige variant">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 12L6 8L10 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>
    <span class="proto-switcher-label">
      <strong>${current.key}</strong> — ${current.name}
    </span>
    <button class="proto-switcher-btn" id="proto-next" aria-label="Volgende variant">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 4L10 8L6 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>
  `;
  document.body.appendChild(bar);

  document.getElementById('proto-prev').addEventListener('click', () => switchVariant(-1));
  document.getElementById('proto-next').addEventListener('click', () => switchVariant(1));

  // Keyboard arrows
  document.addEventListener('keydown', (e) => {
    const tag = document.activeElement?.tagName;
    const editable = document.activeElement?.isContentEditable;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || editable) return;
    if (e.key === 'ArrowLeft') { e.preventDefault(); switchVariant(-1); }
    if (e.key === 'ArrowRight') { e.preventDefault(); switchVariant(1); }
  });

  window.__prototypeCurrentVariant = current.key;
})();
