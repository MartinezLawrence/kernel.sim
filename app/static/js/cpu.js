/* =============================================================
   CPU SCHEDULING MODULE
   ============================================================= */

(function () {
  const tbody = document.querySelector('#cpu-process-table tbody');
  let rowCount = 0;

  function addRow(at = 0, bt = 5, pr = 1) {
    rowCount += 1;
    const pid = `P${rowCount}`;
    const tr = el('tr', {}, [
      el('td', {}, el('input', { type: 'text', value: pid, class: 'cpu-pid' })),
      el('td', {}, el('input', { type: 'number', value: String(at), min: '0', class: 'cpu-at' })),
      el('td', {}, el('input', { type: 'number', value: String(bt), min: '1', class: 'cpu-bt' })),
      el('td', {}, el('input', { type: 'number', value: String(pr), min: '0', class: 'cpu-pr' })),
      el('td', {}, el('button', {
        class: 'row-remove', type: 'button', title: 'Remove',
        onclick: () => tr.remove(),
      }, '✕')),
    ]);
    tbody.appendChild(tr);
  }

  // Seed with a friendly default example
  addRow(0, 5, 2);
  addRow(1, 3, 1);
  addRow(2, 8, 3);
  addRow(3, 6, 2);

  document.getElementById('cpu-add-row').addEventListener('click', () => addRow(0, 4, 1));

  function collectProcesses() {
    return Array.from(tbody.querySelectorAll('tr')).map(tr => ({
      pid: tr.querySelector('.cpu-pid').value.trim(),
      arrival_time: tr.querySelector('.cpu-at').value,
      burst_time: tr.querySelector('.cpu-bt').value,
      priority: tr.querySelector('.cpu-pr').value,
    }));
  }

  function renderResults(results) {
    const output = document.getElementById('cpu-output');
    output.innerHTML = '';
    output.classList.remove('empty-state');

    const keys = Object.keys(results);
    const compareItems = { wt: [], tat: [], rt: [] };

    keys.forEach(key => {
      const r = results[key];
      const color = colorFor(key);
      const block = el('div', { class: 'result-block' });

      const totalEnd = Math.max(...r.schedule.map(s => s.end), 1);
      const segments = r.schedule.map(s => ({
        key: s.pid,
        label: s.pid,
        start: s.start,
        end: s.end,
        color: colorFor(s.pid),
        tooltip: `${s.pid}  ·  ${s.start}–${s.end}`,
      }));

      block.appendChild(el('div', { class: 'result-head' }, [
        el('span', { class: 'result-name' }, [
          el('span', { class: 'result-swatch', style: `background:${color}` }),
          r.label,
        ]),
        el('div', { class: 'metric-row' }, [
          el('span', { class: 'metric-pill' }, ['Avg WT ', el('b', {}, String(r.averages.avg_wt))]),
          el('span', { class: 'metric-pill' }, ['Avg TAT ', el('b', {}, String(r.averages.avg_tat))]),
          el('span', { class: 'metric-pill' }, ['Avg RT ', el('b', {}, String(r.averages.avg_rt))]),
        ]),
      ]));

      block.appendChild(renderTrace(segments, totalEnd));

      block.appendChild(renderDataTable(
        [
          { key: 'pid', label: 'PID' },
          { key: 'arrival_time', label: 'AT' },
          { key: 'burst_time', label: 'BT' },
          { key: 'completion_time', label: 'CT' },
          { key: 'turnaround_time', label: 'TAT' },
          { key: 'waiting_time', label: 'WT' },
          { key: 'response_time', label: 'RT' },
        ],
        r.rows,
        ['pid']
      ));

      output.appendChild(block);

      compareItems.wt.push({ label: r.label, value: r.averages.avg_wt, color });
      compareItems.tat.push({ label: r.label, value: r.averages.avg_tat, color });
      compareItems.rt.push({ label: r.label, value: r.averages.avg_rt, color });
    });

    if (keys.length > 1) {
      const compareBlock = el('div', { class: 'result-block' });
      compareBlock.appendChild(el('div', { class: 'result-head' }, [
        el('span', { class: 'result-name' }, 'Comparison'),
      ]));
      compareBlock.appendChild(renderCompareBars('Average Waiting Time', compareItems.wt));
      compareBlock.appendChild(renderCompareBars('Average Turnaround Time', compareItems.tat));
      compareBlock.appendChild(renderCompareBars('Average Response Time', compareItems.rt));
      output.appendChild(compareBlock);
    }
  }

  async function run() {
    setError('cpu-error', '');
    const btn = document.getElementById('cpu-run');
    const processes = collectProcesses();
    const algorithms = getChecked('cpu-algo-chips');
    const quantum = document.getElementById('cpu-quantum').value;

    if (processes.length === 0) { setError('cpu-error', 'Add at least one process.'); return; }
    if (algorithms.length === 0) { setError('cpu-error', 'Select at least one algorithm.'); return; }

    btn.disabled = true;
    try {
      const data = await postJSON('/api/cpu/run', { processes, algorithms, quantum });
      renderResults(data.results);
    } catch (e) {
      setError('cpu-error', e.message);
    } finally {
      btn.disabled = false;
    }
  }

  document.getElementById('cpu-run').addEventListener('click', run);
})();
