async function loadSignals() {
  const container = document.getElementById('signals');
  if (!container) return;
  try {
    const res = await fetch('/api/signals');
    const data = await res.json();
    const rows = Array.isArray(data) ? data : (data.signals || []);
    container.textContent = '';
    if (!rows.length) {
      const item = document.createElement('li');
      item.textContent = 'No signals';
      container.appendChild(item);
      return;
    }
    rows.slice(0, 20).forEach((s) => {
      const item = document.createElement('li');
      item.textContent = `${s?.pair || '-'} ${s?.direction || ''}`.trim();
      container.appendChild(item);
    });
  } catch {
    container.textContent = '';
    const item = document.createElement('li');
    item.textContent = 'Unable to load signals';
    container.appendChild(item);
  }
}
loadSignals();
setInterval(loadSignals, 5000);
