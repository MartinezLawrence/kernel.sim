/* =============================================================
   MEMORY MANAGEMENT MODULE
   ============================================================= */

(function () {
  const tbody = document.querySelector('#mem-request-table tbody');
  let rowCount = 0;

  function addRow(type = 'alloc', pid = '', size = 40) {
    rowCount += 1;
    const defaultPid = pid || `P${rowCount}`;
    const select = el('select', { class: 'mem-op' }, [
      el('option', { value: 'alloc' }, 'alloc'),
      el('option', { value: 'free' }, 'free'),
    ]);
    select.value = type;

    const sizeInput = el('input', { type: 'number', value: String(size), min: '1', class: 'mem-size' });
    select.addEventListener('change', () => {
      sizeInput.disabled = select.value === 'free';
      sizeInput.style.opacity = select.value === 'free' ? '0.35' : '1';
    });

    const tr = el('tr', {}, [
      el('td', {}, select),
      el('td', {}, el('input', { type: 'text', value: defaultPid, class: 'mem-pid' })),
      el('td', {}, sizeInput),
      el('td', {}, el('button', {
        class: 'row-remove', type: 'button', title: 'Remove',
        onclick: () => tr.remove(),
      }, '✕')),
    ]);
    tbody.appendChild(tr);
  }

  // Seed with a default example showing alloc + free + alloc (good compaction demo)
  addRow('alloc', '', 40);
  addRow('alloc', '', 25);
  addRow('alloc', '', 30);
  addRow('free', 'P2', 0);
  addRow('alloc', '', 50);

  document.getElementById('mem-add-row').addEventListener('click', () => addRow('alloc', '', 20));

  function collectRequests() {
    return Array.from(tbody.querySelectorAll('tr')).map(tr => {
      const type = tr.querySelector('.mem-op').value;
      const pid = tr.querySelector('.mem-pid').value.trim();
      if (type === 'free') return { type: 'free', pid };
      return { type: 'alloc', pid, size: tr.querySelector('.mem-size').value };
    });
  }

  function renderMemStrip(blocks, totalSize) {
    const strip = el('div', { class: 'mem-strip' });
    blocks.forEach(b => {
      const widthPct = (b.size / totalSize) * 100;
      const isFree = b.pid === null;
      const block = el('div', {
        class: `mem-block ${isFree ? 'free' : ''}`,
        style: `width:${widthPct}%; ${isFree ? '' : `background:${colorFor(b.pid)}; color:#0B0E13;`}`,
      });
      if (widthPct > 5) block.textContent = isFree ? '' : b.pid;
      block.appendChild(el('div', { class: 'seg-tooltip' }, isFree
        ? `Free  ·  ${b.start}–${b.end}  (${b.size})`
        : `${b.pid}  ·  ${b.start}–${b.end}  (${b.size})`));
      strip.appendChild(block);
    });
    return strip;
  }

  function renderResults(results, totalSize, compaction) {
    const output = document.getElementById('mem-output');
    output.innerHTML = '';
    output.classList.remove('empty-state');

    const keys = Object.keys(results);
    const utilItems = [];

    keys.forEach(key => {
      const r = results[key];
      const color = colorFor(key);
      const block = el('div', { class: 'result-block' });

      block.appendChild(el('div', { class: 'result-head' }, [
        el('span', { class: 'result-name' }, [
          el('span', { class: 'result-swatch', style: `background:${color}` }),
          r.label + (compaction ? ' · compaction on' : ' · compaction off'),
        ]),
        el('div', { class: 'metric-row' }, [
          el('span', { class: 'metric-pill' }, ['Utilization ', el('b', {}, `${r.utilization}%`)]),
          el('span', { class: 'metric-pill' }, ['Ext. Fragmentation ', el('b', {}, String(r.fragmentation))]),
        ]),
      ]));

      // Final state strip (prominent)
      block.appendChild(el('div', { class: 'mem-snapshot-label' }, 'Final memory layout'));
      block.appendChild(renderMemStrip(r.final_blocks, totalSize));

      // Step-by-step snapshots
      const stepsWrap = el('div', { style: 'margin-top:18px;' });
      stepsWrap.appendChild(el('p', { class: 'compare-title' }, 'Allocation timeline'));
      r.snapshots.forEach(snap => {
        const snapBlock = el('div', { class: 'mem-snapshot' });
        snapBlock.appendChild(el('div', { class: 'mem-snapshot-label' }, snap.label));
        snapBlock.appendChild(renderMemStrip(snap.blocks, totalSize));
        stepsWrap.appendChild(snapBlock);
      });
      block.appendChild(stepsWrap);

      // Log
      const logWrap = el('div', { class: 'mem-log' });
      r.log.forEach(line => {
        const cls = line.startsWith('FAILED') ? 'fail' : (line.includes('Compaction') ? 'compact' : '');
        logWrap.appendChild(el('div', { class: `mem-log-line ${cls}` }, line));
      });
      block.appendChild(logWrap);

      output.appendChild(block);
      utilItems.push({ label: r.label, value: r.utilization, color });
    });

    if (keys.length > 1) {
      const compareBlock = el('div', { class: 'result-block' });
      compareBlock.appendChild(el('div', { class: 'result-head' }, [
        el('span', { class: 'result-name' }, 'Comparison'),
      ]));
      compareBlock.appendChild(renderCompareBars('Memory Utilization', utilItems, '%'));
      output.appendChild(compareBlock);
    }
  }

  async function run() {
    setError('mem-error', '');
    const btn = document.getElementById('mem-run');
    const total_size = document.getElementById('mem-total-size').value;
    const compaction = document.getElementById('mem-compaction').checked;
    const requests = collectRequests();
    const strategies = getChecked('mem-strategy-chips');

    if (requests.length === 0) { setError('mem-error', 'Add at least one request.'); return; }
    if (strategies.length === 0) { setError('mem-error', 'Select at least one strategy.'); return; }

    btn.disabled = true;
    try {
      const data = await postJSON('/api/memory/run', { total_size, requests, strategies, compaction });
      renderResults(data.results, data.total_size, data.compaction);
    } catch (e) {
      setError('mem-error', e.message);
    } finally {
      btn.disabled = false;
    }
  }

  document.getElementById('mem-run').addEventListener('click', run);
})();
