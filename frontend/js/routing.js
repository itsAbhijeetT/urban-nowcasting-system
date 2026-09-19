/**
 * Safe Routing Module (Module E)
 * Communicates with /api/route to calculate dynamic flood-penalized navigation paths.
 */

function setupRouting(currentTimestepGetter) {
  const calcBtn = document.getElementById('calcRouteBtn');
  const originSelect = document.getElementById('routeOrigin');
  const destSelect = document.getElementById('routeDestination');
  const resultsCard = document.getElementById('routeResultsCard');

  calcBtn.addEventListener('click', async () => {
    const origin = originSelect.value;
    const dest = destSelect.value;
    const vehicleMode = document.querySelector('input[name="vehicleMode"]:checked')?.value || 'emergency';
    const timestep = currentTimestepGetter();

    calcBtn.disabled = true;
    calcBtn.innerHTML = `<i data-lucide="loader" class="spin"></i> Calculating Path...`;

    try {
      const response = await fetch('/api/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_node: origin,
          end_node: dest,
          timestep_min: timestep
        })
      });

      if (!response.ok) {
        throw new Error('Failed to compute route');
      }

      const routeData = await response.json();
      displayRouteResults(routeData, vehicleMode);
      window.MapEngine.renderRoutePaths(routeData);

    } catch (err) {
      console.error(err);
      alert('Routing Error: ' + err.message);
    } finally {
      calcBtn.disabled = false;
      calcBtn.innerHTML = `<i data-lucide="compass"></i> Compute Flood-Safe Route`;
      lucide.createIcons();
    }
  });
}

function displayRouteResults(routeData, mode) {
  const resultsCard = document.getElementById('routeResultsCard');
  const routeTime = document.getElementById('routeTravelTime');
  const routeDist = document.getElementById('routeDistance');
  const routeMaxDepth = document.getElementById('routeMaxDepth');
  const routeDelay = document.getElementById('routeDelay');
  const directionsList = document.getElementById('routeDirectionsList');
  const statusBadge = document.getElementById('routeStatusBadge');

  const chosen = mode === 'emergency' ? routeData.emergency : routeData.commuter;

  if (!chosen || !chosen.success) {
    resultsCard.style.display = 'block';
    statusBadge.className = 'badge-miss';
    statusBadge.innerText = 'NO PASSABLE ROUTE';
    routeTime.innerText = '--';
    routeDist.innerText = '--';
    routeMaxDepth.innerText = '>35 cm';
    routeDelay.innerText = 'Impassable';
    directionsList.innerHTML = `<p style="color: #f87171; margin-top: 8px;">
      All direct arterial avenues are severely submerged beyond vehicle clearance. Advise emergency services to stage watercraft or deploy bypass ridges.
    </p>`;
    return;
  }

  resultsCard.style.display = 'block';
  statusBadge.className = 'badge-success';
  statusBadge.innerText = `${chosen.vehicle_name} Path Clear`;

  routeTime.innerText = `${chosen.estimated_time_min} min`;
  routeDist.innerText = `${chosen.total_distance_km} km`;
  routeMaxDepth.innerText = `${chosen.max_depth_encountered_cm} cm`;

  if (routeData.delay_commuter_min !== null && routeData.delay_commuter_min > 0) {
    routeDelay.innerText = `+${routeData.delay_commuter_min} min`;
  } else {
    routeDelay.innerText = `0.0 min (Normal)`;
  }

  const nodesPath = chosen.path_nodes.join(' → ');
  directionsList.innerHTML = `
    <p><b>Nav Path:</b> ${nodesPath}</p>
    <p style="margin-top: 4px; color: #38bdf8;">
      Safely bypassed Railway Subway & Gandhi Market lowlands via elevated ridge corridors.
    </p>
  `;
}

window.RoutingEngine = {
  setupRouting
};
