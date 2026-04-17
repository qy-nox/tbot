const tokenInput = document.getElementById("tokenInput");
const refreshBtn = document.getElementById("refreshBtn");

async function fetchJSON(url, token) {
  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    throw new Error(`${url} -> ${response.status}`);
  }
  return response.json();
}

async function refreshAdmin() {
  const token = tokenInput.value.trim();
  try {
    const [dashboard, users] = await Promise.all([
      fetchJSON("/api/admin/dashboard", token),
      fetchJSON("/api/admin/users?limit=25", token),
    ]);

    document.getElementById("totalUsers").textContent = dashboard.total_users;
    document.getElementById("paidUsers").textContent = `${dashboard.premium_users + dashboard.vip_users}`;
    document.getElementById("signalsToday").textContent = dashboard.total_signals_today;
    document.getElementById("revenue").textContent = `$${Number(dashboard.total_revenue || 0).toFixed(2)}`;
    document.getElementById("usersBox").textContent = JSON.stringify(users, null, 2);
    document.getElementById("paymentsBox").textContent = JSON.stringify(dashboard, null, 2);
  } catch (error) {
    document.getElementById("usersBox").textContent = `Failed loading admin data.\n${error}`;
  }
}

refreshBtn?.addEventListener("click", refreshAdmin);
