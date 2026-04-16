async function loadJson(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    return { error: String(error) };
  }
}

async function render() {
  const root = document.getElementById('app');
  if (!root) return;

  const page = document.body.dataset.page || 'index';

  if (page === 'index') {
    const stats = await loadJson('/dashboard/backend/analytics');
    root.innerHTML = `<div class="card"><h2>Dashboard Overview</h2><pre>${JSON.stringify(stats, null, 2)}</pre></div>`;
    return;
  }

  if (page === 'users') {
    root.innerHTML = `<div class="card"><h2>Users</h2><pre>${JSON.stringify(await loadJson('/dashboard/backend/users'), null, 2)}</pre></div>`;
    return;
  }

  if (page === 'subscriptions') {
    root.innerHTML = `<div class="card"><h2>Subscriptions</h2><pre>${JSON.stringify(await loadJson('/dashboard/backend/subscriptions'), null, 2)}</pre></div>`;
    return;
  }

  if (page === 'signals') {
    root.innerHTML = `<div class="card"><h2>Signals</h2><pre>${JSON.stringify(await loadJson('/dashboard/backend/signals'), null, 2)}</pre></div>`;
    return;
  }

  if (page === 'market') {
    root.innerHTML = `<div class="card"><h2>Market</h2><pre>${JSON.stringify(await loadJson('/dashboard/backend/market'), null, 2)}</pre></div>`;
    return;
  }

  root.innerHTML = '<div class="card"><h2>Section ready</h2><p class="small">This section is connected via the dashboard backend API.</p></div>';
}

render();
