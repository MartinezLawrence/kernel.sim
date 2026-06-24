/* =============================================================
   kernel.sim — app.js
   Core utilities, navigation, and editable-table helpers.
   ============================================================= */

const PALETTE = ['#FFB454', '#5FD4D4', '#6FCF97', '#B9A3FF', '#FF8FA3', '#7FA8FF', '#E8C468', '#8FE0B0'];
function colorFor(key) {
  // stable hash -> palette index, so the same pid/algo always gets the same color within a render
  let h = 0;
  for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') node.className = v;
    else if (k === 'html') node.innerHTML = v;
    else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const c of [].concat(children)) {
    if (c == null) continue;
    node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  }
  return node;
}

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({ ok: false, error: 'Server returned an invalid response.' }));
  if (!res.ok || !data.ok) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

function setError(elId, msg) {
  const node = document.getElementById(elId);
  node.textContent = msg || '';
}

function getChecked(containerId) {
  return Array.from(document.querySelectorAll(`#${containerId} input[type=checkbox]:checked`)).map(i => i.value);
}

/* =============================================================
   NAVIGATION
   ============================================================= */

document.querySelectorAll('.rail-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.rail-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.module').forEach(m => m.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`module-${btn.dataset.module}`).classList.add('active');
  });
});

/* =============================================================
   GENERIC "TRACE" (GANTT-STYLE) RENDERER
   Used by CPU scheduling and as the base visual language.
   segments: [{ key, label, start, end, tooltip }]
   ============================================================= */

function renderTrace(segments, totalEnd) {
  const track = el('div', { class: 'trace-track' });
  track.appendChild(el('div', { class: 'trace-baseline' }));

  const span = totalEnd || 1;
  segments.forEach(seg => {
    const leftPct = (seg.start / span) * 100;
    const widthPct = Math.max(((seg.end - seg.start) / span) * 100, 0.4);
    const segNode = el('div', {
      class: 'trace-seg',
      style: `left:${leftPct}%; width:${widthPct}%; background:${seg.color};`,
    });
    if (widthPct > 3) segNode.textContent = seg.label;
    segNode.appendChild(el('div', { class: 'seg-tooltip' }, seg.tooltip || seg.label));
    track.appendChild(segNode);
  });

  // Ruler with adaptive tick density
  const ruler = el('div', { class: 'trace-ruler' });
  const ticks = computeTicks(span);
  ticks.forEach(t => {
    ruler.appendChild(el('div', { class: 'trace-tick', style: `left:${(t / span) * 100}%` }, String(t)));
  });

  const wrap = el('div', { class: 'trace-wrap' }, [track, ruler]);
  return wrap;
}

function computeTicks(span) {
  if (span <= 0) return [0];
  const targetCount = 10;
  const rawStep = span / targetCount;
  const niceSteps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000];
  let step = niceSteps.find(s => s >= rawStep) || niceSteps[niceSteps.length - 1];
  const ticks = [];
  for (let t = 0; t <= span; t += step) ticks.push(t);
  if (ticks[ticks.length - 1] !== span) ticks.push(span);
  return ticks;
}

/* =============================================================
   GENERIC COMPARISON BAR CHART
   items: [{ label, value, color }]
   ============================================================= */

function renderCompareBars(title, items, unit = '') {
  const max = Math.max(...items.map(i => i.value), 0.0001);
  const wrap = el('div', { class: 'compare-wrap' });
  wrap.appendChild(el('p', { class: 'compare-title' }, title));
  items.forEach(item => {
    const pct = (item.value / max) * 100;
    const row = el('div', { class: 'bar-row' }, [
      el('span', { class: 'bar-label' }, item.label),
      el('div', { class: 'bar-track' }, [
        el('div', { class: 'bar-fill', style: `width:${pct}%; background:${item.color};` }),
      ]),
      el('span', { class: 'bar-value' }, `${item.value}${unit}`),
    ]);
    wrap.appendChild(row);
  });
  return wrap;
}

/* =============================================================
   DATA TABLE RENDERER
   columns: [{ key, label }]   rows: [{...}]
   ============================================================= */

function renderDataTable(columns, rows, hiKeys = []) {
  const wrap = el('div', { class: 'data-table-wrap' });
  const table = el('table', { class: 'data-table' });
  const thead = el('thead', {}, [
    el('tr', {}, columns.map(c => el('th', {}, c.label))),
  ]);
  const tbody = el('tbody', {}, rows.map(row =>
    el('tr', {}, columns.map(c =>
      el('td', { class: hiKeys.includes(c.key) ? 'hi' : '' }, String(row[c.key]))
    ))
  ));
  table.appendChild(thead);
  table.appendChild(tbody);
  wrap.appendChild(table);
  return wrap;
}
