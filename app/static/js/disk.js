/* =============================================================
   DISK SCHEDULING MODULE
   ============================================================= */

(function () {
  // Direction segmented control
  const dirControl = document.getElementById('disk-direction');
  dirControl.querySelectorAll('.seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      dirControl.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
  function getDirection() {
    return dirControl.querySelector('.seg-btn.active').dataset.val;
  }

  function renderDiskTrace(order, diskSize, color) {
    const width = 760;
    const height = 220;
    const padX = 40;
    const padY = 24;
    const plotW = width - padX * 2;
    const plotH = height - padY * 2;

    const xFor = (step) => padX + (order.length <= 1 ? 0 : (step / (order.length - 1)) * plotW);
    const yFor = (cyl) => padY + (1 - cyl / Math.max(diskSize - 1, 1)) * plotH;

    let pathD = '';
    order.forEach((cyl, i) => {
      const x = xFor(i);
      const y = yFor(cyl);
      pathD += (i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`);
    });

    const points = order.map((cyl, i) => {
      const x = xFor(i);
      const y = yFor(cyl);
      const isStart = i === 0;
      return `
        <circle cx="${x}" cy="${y}" r="${isStart ? 5.5 : 4}" fill="${isStart ? '#FFB454' : color}" stroke="#0B0E13" stroke-width="1.5" />
        <text class="disk-point-label" x="${x}" y="${y - 10}" text-anchor="middle">${cyl}</text>
      `;
    }).join('');

    // y-axis gridlines (0, mid, max)
    const gridVals = [0, Math.round((diskSize - 1) / 2), diskSize - 1];
    const grid = gridVals.map(v => {
      const y = yFor(v);
      return `
        <line x1="${padX}" y1="${y}" x2="${width - padX}" y2="${y}" stroke="#1F2733" stroke-width="1" stroke-dasharray="3,4" />
        <text x="${padX - 8}" y="${y + 3}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="9" fill="#66728A">${v}</text>
      `;
    }).join('');

    const svg = `
      <svg class="disk-path-svg" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
        ${grid}
        <path d="${pathD}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" opacity="0.9" />
        ${points}
      </svg>
    `;
    return el('div', { class: 'disk-trace', html: svg });
  }

  function renderResults(results, head, diskSize, direction) {
    const output = document.getElementById('disk-output');
    output.innerHTML = '';
    output.classList.remove('empty-state');

    const keys = Object.keys(results);
    const movementItems = [];

    keys.forEach(key => {
      const r = results[key];
      const color = colorFor(key);
      const block = el('div', { class: 'result-block' });

      block.appendChild(el('div', { class: 'result-head' }, [
        el('span', { class: 'result-name' }, [
          el('span', { class: 'result-swatch', style: `background:${color}` }),
          r.label,
        ]),
        el('div', { class: 'metric-row' }, [
          el('span', { class: 'metric-pill' }, ['Total Head Movement ', el('b', {}, String(r.total_movement))]),
          el('span', { class: 'metric-pill' }, ['Requests Served ', el('b', {}, String(r.order.length - 1))]),
        ]),
      ]));

      block.appendChild(renderDiskTrace(r.order, diskSize, color));

      const orderStrip = el('div', { class: 'disk-order-strip' });
      r.order.forEach((cyl, i) => {
        orderStrip.appendChild(el('span', { class: `disk-order-chip ${i === 0 ? 'start' : ''}` }, String(cyl)));
        if (i < r.order.length - 1) orderStrip.appendChild(el('span', { style: 'color:#3A4757;' }, '→'));
      });
      block.appendChild(orderStrip);

      output.appendChild(block);
      movementItems.push({ label: r.label, value: r.total_movement, color });
    });

    if (keys.length > 1) {
      const compareBlock = el('div', { class: 'result-block' });
      compareBlock.appendChild(el('div', { class: 'result-head' }, [
        el('span', { class: 'result-name' }, 'Comparison'),
      ]));
      compareBlock.appendChild(renderCompareBars('Total Head Movement', movementItems, ' cyl'));
      output.appendChild(compareBlock);
    }
  }

  async function run() {
    setError('disk-error', '');
    const btn = document.getElementById('disk-run');
    const requests = document.getElementById('disk-requests').value;
    const head = document.getElementById('disk-head').value;
    const disk_size = document.getElementById('disk-size').value;
    const direction = getDirection();
    const algorithms = getChecked('disk-algo-chips');

    if (!requests.trim()) { setError('disk-error', 'Enter a request queue.'); return; }
    if (algorithms.length === 0) { setError('disk-error', 'Select at least one algorithm.'); return; }

    btn.disabled = true;
    try {
      const data = await postJSON('/api/disk/run', { requests, head, disk_size, direction, algorithms });
      renderResults(data.results, data.head, data.disk_size, data.direction);
    } catch (e) {
      setError('disk-error', e.message);
    } finally {
      btn.disabled = false;
    }
  }

  document.getElementById('disk-run').addEventListener('click', run);
})();
