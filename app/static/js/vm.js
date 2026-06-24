/* =============================================================
   VIRTUAL MEMORY (PAGE REPLACEMENT) MODULE
   ============================================================= */

(function () {
  function renderFrameGrid(history, numFrames) {
    const wrap = el('div', { class: 'frame-grid-wrap' });
    const table = el('table', { class: 'frame-grid' });

    const headRow = el('tr', {}, [
      el('th', {}, 'Frame'),
      ...history.map((h, i) => el('th', { class: h.fault ? 'fault-col' : '' }, String(h.page))),
    ]);
    const thead = el('thead', {}, headRow);

    const rows = [];
    for (let f = 0; f < numFrames; f++) {
      const cells = [el('td', { class: 'frame-label' }, `F${f}`)];
      history.forEach(h => {
        const val = h.frames[f] !== undefined ? h.frames[f] : '';
        const isThisStepsValue = h.frames[f] === h.page;
        let cls = 'occupied';
        if (isThisStepsValue) cls += h.fault ? ' fault-cell' : ' hit-cell';
        cells.push(el('td', { class: val === '' ? '' : cls }, val === '' ? '·' : String(val)));
      });
      rows.push(el('tr', {}, cells));
    }
    const tbody = el('tbody', {}, rows);

    // Fault/Hit marker row
    const markerRow = el('tr', {}, [
      el('td', { class: 'frame-label' }, 'Result'),
      ...history.map(h => el('td', { class: h.fault ? 'fault-cell' : 'hit-cell' }, h.fault ? 'F' : 'H')),
    ]);
    tbody.appendChild(markerRow);

    table.appendChild(thead);
    table.appendChild(tbody);
    wrap.appendChild(table);
    return wrap;
  }

  function renderResults(results, numFrames, reference) {
    const output = document.getElementById('vm-output');
    output.innerHTML = '';
    output.classList.remove('empty-state');

    const keys = Object.keys(results);
    const faultItems = [];

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
          el('span', { class: 'metric-pill' }, ['Page Faults ', el('b', {}, `${r.faults} / ${r.total_refs}`)]),
          el('span', { class: 'metric-pill' }, ['Hit Ratio ', el('b', {}, `${r.hit_ratio}%`)]),
        ]),
      ]));

      block.appendChild(renderFrameGrid(r.history, numFrames));

      output.appendChild(block);
      faultItems.push({ label: r.label, value: r.faults, color });
    });

    if (keys.length > 1) {
      const compareBlock = el('div', { class: 'result-block' });
      compareBlock.appendChild(el('div', { class: 'result-head' }, [
        el('span', { class: 'result-name' }, 'Comparison'),
      ]));
      compareBlock.appendChild(renderCompareBars('Total Page Faults', faultItems));
      output.appendChild(compareBlock);
    }
  }

  async function run() {
    setError('vm-error', '');
    const btn = document.getElementById('vm-run');
    const reference_string = document.getElementById('vm-reference').value;
    const num_frames = document.getElementById('vm-frames').value;
    const algorithms = getChecked('vm-algo-chips');

    if (!reference_string.trim()) { setError('vm-error', 'Enter a reference string.'); return; }
    if (algorithms.length === 0) { setError('vm-error', 'Select at least one algorithm.'); return; }

    btn.disabled = true;
    try {
      const data = await postJSON('/api/vm/run', { reference_string, num_frames, algorithms });
      renderResults(data.results, data.num_frames, data.reference);
    } catch (e) {
      setError('vm-error', e.message);
    } finally {
      btn.disabled = false;
    }
  }

  document.getElementById('vm-run').addEventListener('click', run);
})();
