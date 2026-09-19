/**
 * Historical Backtesting Validation Module
 * Benchmarks predictions against verified historical flood incidents and displays
 * standard meteorological validation metrics (CSI, POD, FAR, Accuracy).
 */

function setupBacktest() {
  const eventSelect = document.getElementById('backtestEventSelect');
  const runBtn = document.getElementById('runBacktestBtn');

  const csiMetric = document.getElementById('csiMetric');
  const podMetric = document.getElementById('podMetric');
  const farMetric = document.getElementById('farMetric');
  const accMetric = document.getElementById('accMetric');
  const tableBody = document.getElementById('backtestTableBody');

  runBtn.addEventListener('click', async () => {
    const eventId = eventSelect.value;

    runBtn.disabled = true;
    runBtn.innerHTML = `<i data-lucide="loader" class="spin"></i> Running Evaluation...`;

    try {
      const resp = await fetch(`/api/backtest?event_id=${eventId}`);
      if (!resp.ok) throw new Error('Failed to run backtest evaluation');

      const data = await resp.json();
      const eventData = data.selected_event;

      // Update metrics
      csiMetric.innerText = eventData.metrics.critical_success_index.toFixed(3);
      podMetric.innerText = eventData.metrics.probability_of_detection.toFixed(3);
      farMetric.innerText = eventData.metrics.false_alarm_ratio.toFixed(3);
      accMetric.innerText = `${eventData.metrics.overall_accuracy_pct}%`;

      // Populate points table
      tableBody.innerHTML = '';
      eventData.points.forEach(pt => {
        const tr = document.createElement('tr');
        const isHit = pt.outcome.includes('HIT') || pt.outcome.includes('CORRECT');
        const badgeClass = isHit ? 'badge-hit' : 'badge-miss';

        tr.innerHTML = `
          <td>
            <strong>${pt.name}</strong><br>
            <small style="color: #64748b;">${pt.source}</small>
          </td>
          <td><b style="color: #f87171;">${pt.observed_depth_cm} cm</b></td>
          <td><b style="color: #38bdf8;">${pt.predicted_depth_cm} cm</b></td>
          <td><span class="${badgeClass}">${pt.outcome}</span></td>
        `;
        tableBody.appendChild(tr);
      });

      alert(`Backtest Complete! Critical Success Index (CSI): ${eventData.metrics.critical_success_index} across ${eventData.points.length} ground-truth checkpoints.`);

    } catch (err) {
      console.error(err);
      alert('Error running backtest: ' + err.message);
    } finally {
      runBtn.disabled = false;
      runBtn.innerHTML = `<i data-lucide="play-circle"></i> Run Backtest Evaluation`;
      lucide.createIcons();
    }
  });

  // Run initial backtest evaluation on load
  runBtn.click();
}

window.BacktestEngine = {
  setupBacktest
};
