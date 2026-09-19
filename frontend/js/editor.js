/**
 * ULB Drainage Network Calibration Module
 * Enables municipal engineers to inspect and modify pipe parameters (diameters, inverts)
 * and trigger live hydraulic re-computations to test flood mitigation interventions.
 */

function setupDrainEditor(onNowcastUpdated) {
  const pipeSelect = document.getElementById('selectedPipeSelect');
  const diamSlider = document.getElementById('newPipeDiameter');
  const diamDisplay = document.getElementById('diameterValDisplay');
  const applyBtn = document.getElementById('applyCalibrationBtn');

  const pipeFrom = document.getElementById('pipeFrom');
  const pipeTo = document.getElementById('pipeTo');
  const pipeCap = document.getElementById('pipeCap');
  const pipeUtil = document.getElementById('pipeUtil');

  let currentConduits = {};

  // Slider change listener
  diamSlider.addEventListener('input', (e) => {
    diamDisplay.innerText = `${e.target.value} mm`;
  });

  // Select change listener
  pipeSelect.addEventListener('change', () => {
    const cid = pipeSelect.value;
    updateSelectedPipeUI(cid);
  });

  // Apply calibration button
  applyBtn.addEventListener('click', async () => {
    const cid = pipeSelect.value;
    const newDiam = parseInt(diamSlider.value, 10);

    applyBtn.disabled = true;
    applyBtn.innerHTML = `<i data-lucide="loader" class="spin"></i> Recalculating Hydraulics...`;

    try {
      const resp = await fetch('/api/network/calibrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conduit_id: cid,
          new_diam_mm: newDiam
        })
      });

      if (!resp.ok) {
        throw new Error('Calibration failed');
      }

      const resData = await resp.json();
      alert(`Success: ${resData.message}`);

      // Notify main app to update cached nowcast data
      if (onNowcastUpdated) {
        onNowcastUpdated(resData.new_nowcast);
      }

      // Re-populate network state
      await loadNetwork();

    } catch (err) {
      console.error(err);
      alert('Error applying calibration: ' + err.message);
    } finally {
      applyBtn.disabled = false;
      applyBtn.innerHTML = `<i data-lucide="check"></i> Apply Calibration & Recalculate`;
      lucide.createIcons();
    }
  });

  async function loadNetwork() {
    try {
      const resp = await fetch('/api/network');
      const data = await resp.json();

      pipeSelect.innerHTML = '';
      currentConduits = {};

      data.conduits.forEach(pipe => {
        currentConduits[pipe.id] = pipe;
        const opt = document.createElement('option');
        opt.value = pipe.id;
        opt.innerText = `${pipe.id} (Ø${pipe.diam_mm}mm: ${pipe.from} → ${pipe.to}) ${pipe.inferred ? '[Inferred]' : ''}`;
        pipeSelect.appendChild(opt);
      });

      // Default select bottleneck P8 or P4 if present
      const defaultPipe = currentConduits['P8'] ? 'P8' : (currentConduits['P4'] ? 'P4' : data.conduits[0].id);
      pipeSelect.value = defaultPipe;
      updateSelectedPipeUI(defaultPipe);

    } catch (err) {
      console.error('Failed to load network data:', err);
    }
  }

  function updateSelectedPipeUI(cid) {
    const pipe = currentConduits[cid];
    if (!pipe) return;

    pipeFrom.innerText = pipe.from;
    pipeTo.innerText = pipe.to;
    pipeCap.innerText = `${pipe.q_capacity_m3s || '--'} m³/s`;
    
    // Set slider value
    diamSlider.value = pipe.diam_mm;
    diamDisplay.innerText = `${pipe.diam_mm} mm`;

    // Estimate status
    if (pipe.diam_mm <= 600) {
      pipeUtil.className = 'text-red';
      pipeUtil.innerText = 'High Surcharge Risk (Bottleneck)';
    } else {
      pipeUtil.className = 'text-green';
      pipeUtil.innerText = 'Sufficient Flow Capacity';
    }
  }

  function selectPipeFromMap(pipeData) {
    if (!pipeData || !pipeData.id) return;
    pipeSelect.value = pipeData.id;
    updateSelectedPipeUI(pipeData.id);

    // Switch to editor tab
    const editorTabBtn = document.querySelector('.tab-btn[data-tab="editor"]');
    if (editorTabBtn) editorTabBtn.click();
  }

  // Initial load
  loadNetwork();

  return {
    selectPipeFromMap,
    reloadNetwork: loadNetwork
  };
}

window.DrainEditor = {
  setupDrainEditor
};
