"""
Lightweight web dashboard for the trading signal platform.

Serves a single-page dashboard with real-time signal data,
performance charts, and system status.  Uses inline HTML/JS
(Chart.js via CDN) so no separate template files are needed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from sqlalchemy import func

from signal_platform.models import (
    SignalOutcome,
    SignalRecord,
    SignalType,
    User,
    get_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _quick_stats() -> dict:
    """Gather lightweight statistics for the dashboard."""
    db = get_session()
    try:
        total_signals = db.query(func.count(SignalRecord.id)).scalar() or 0
        crypto_signals = (
            db.query(func.count(SignalRecord.id))
            .filter(SignalRecord.signal_type == SignalType.CRYPTO)
            .scalar()
            or 0
        )
        binary_signals = (
            db.query(func.count(SignalRecord.id))
            .filter(SignalRecord.signal_type == SignalType.BINARY)
            .scalar()
            or 0
        )

        won = (
            db.query(func.count(SignalRecord.id))
            .filter(
                SignalRecord.outcome.in_([
                    SignalOutcome.TP1_HIT,
                    SignalOutcome.TP2_HIT,
                    SignalOutcome.TP3_HIT,
                ])
            )
            .scalar()
            or 0
        )
        lost = (
            db.query(func.count(SignalRecord.id))
            .filter(SignalRecord.outcome == SignalOutcome.SL_HIT)
            .scalar()
            or 0
        )
        resolved = won + lost
        win_rate = (won / resolved * 100) if resolved else 0.0

        total_users = db.query(func.count(User.id)).scalar() or 0

        # Recent signals
        recent = (
            db.query(SignalRecord)
            .order_by(SignalRecord.timestamp.desc())
            .limit(20)
            .all()
        )

        recent_list = []
        for sig in recent:
            recent_list.append({
                "id": sig.id,
                "pair": sig.pair,
                "type": sig.signal_type.value if sig.signal_type else "crypto",
                "direction": sig.direction.value if sig.direction else "",
                "entry": sig.entry_price,
                "confidence": sig.confidence,
                "grade": sig.grade.value if sig.grade else "-",
                "outcome": sig.outcome.value if sig.outcome else "pending",
                "time": sig.timestamp.strftime("%Y-%m-%d %H:%M") if sig.timestamp else "",
            })

        return {
            "total_signals": total_signals,
            "crypto_signals": crypto_signals,
            "binary_signals": binary_signals,
            "win_rate": round(win_rate, 1),
            "won": won,
            "lost": lost,
            "total_users": total_users,
            "recent": recent_list,
            "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
    finally:
        db.close()


@router.get("/", response_class=HTMLResponse)
def dashboard_page():
    """Serve the main dashboard page."""
    stats = _quick_stats()
    recent_rows = ""
    for s in stats["recent"]:
        outcome_cls = "win" if "tp" in s["outcome"] else ("loss" if s["outcome"] == "sl_hit" else "pending")
        direction_emoji = "🟢" if s["direction"] in ("BUY", "CALL") else "🔴" if s["direction"] in ("SELL", "PUT") else "⚪"
        recent_rows += f"""
        <tr class="{outcome_cls}">
            <td>{s['time']}</td>
            <td><span class="badge badge-{'crypto' if s['type'] == 'crypto' else 'binary'}">{s['type'].upper()}</span></td>
            <td><strong>{s['pair']}</strong></td>
            <td>{direction_emoji} {s['direction']}</td>
            <td>${s['entry']:,.2f}</td>
            <td>{s['confidence'] * 100:.0f}%</td>
            <td><span class="grade">{s['grade']}</span></td>
            <td><span class="outcome outcome-{outcome_cls}">{s['outcome'].replace('_', ' ').upper()}</span></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trading Signal Dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #0d1117; color: #c9d1d9; padding: 20px; }}
  .header {{ display: flex; justify-content: space-between; align-items: center;
             margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #21262d; }}
  .header h1 {{ font-size: 24px; color: #58a6ff; }}
  .header .updated {{ font-size: 12px; color: #8b949e; }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px; margin-bottom: 24px; }}
  .stat-card {{ background: #161b22; border: 1px solid #21262d; border-radius: 8px;
                padding: 20px; text-align: center; }}
  .stat-card .value {{ font-size: 32px; font-weight: 700; color: #58a6ff; }}
  .stat-card .label {{ font-size: 13px; color: #8b949e; margin-top: 4px; }}
  .stat-card.win-rate .value {{ color: #3fb950; }}
  table {{ width: 100%; border-collapse: collapse; background: #161b22;
           border: 1px solid #21262d; border-radius: 8px; overflow: hidden; }}
  th {{ background: #21262d; padding: 12px; text-align: left; font-size: 13px;
       color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }}
  td {{ padding: 10px 12px; border-top: 1px solid #21262d; font-size: 14px; }}
  tr.win {{ background: rgba(63,185,80,0.05); }}
  tr.loss {{ background: rgba(248,81,73,0.05); }}
  .badge {{ padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
  .badge-crypto {{ background: #1f6feb33; color: #58a6ff; }}
  .badge-binary {{ background: #a371f733; color: #bc8cff; }}
  .grade {{ font-weight: 700; color: #f0883e; }}
  .outcome {{ padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
  .outcome-win {{ background: #238636; color: #fff; }}
  .outcome-loss {{ background: #da3633; color: #fff; }}
  .outcome-pending {{ background: #30363d; color: #8b949e; }}
  h2 {{ font-size: 18px; margin-bottom: 12px; color: #e6edf3; }}
  .section {{ margin-bottom: 24px; }}
  .chart-wrap {{ background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 16px; }}
  canvas {{ max-height: 280px; }}
  @media (max-width: 600px) {{
    .stats {{ grid-template-columns: 1fr 1fr; }}
    .header {{ flex-direction: column; gap: 8px; }}
  }}
</style>
</head>
<body>
<div class="header">
  <h1>📊 Trading Signal Dashboard</h1>
  <span class="updated">Last updated: {stats['updated']}</span>
</div>

<div class="stats">
  <div class="stat-card">
    <div class="value">{stats['total_signals']}</div>
    <div class="label">Total Signals</div>
  </div>
  <div class="stat-card">
    <div class="value">{stats['crypto_signals']}</div>
    <div class="label">Crypto Signals</div>
  </div>
  <div class="stat-card">
    <div class="value">{stats['binary_signals']}</div>
    <div class="label">Binary Signals</div>
  </div>
  <div class="stat-card win-rate">
    <div class="value">{stats['win_rate']}%</div>
    <div class="label">Win Rate ({stats['won']}W / {stats['lost']}L)</div>
  </div>
  <div class="stat-card">
    <div class="value">{stats['total_users']}</div>
    <div class="label">Active Users</div>
  </div>
</div>

<div class="section">
  <h2>Performance Snapshot</h2>
  <div class="chart-wrap">
    <canvas id="outcomesChart"></canvas>
  </div>
</div>

<div class="section">
  <h2>Recent Signals</h2>
  <table>
    <thead>
      <tr>
        <th>Time</th><th>Type</th><th>Pair</th><th>Direction</th>
        <th>Entry</th><th>Confidence</th><th>Grade</th><th>Outcome</th>
      </tr>
    </thead>
    <tbody>
      {recent_rows if recent_rows else '<tr><td colspan="8" style="text-align:center;color:#8b949e;">No signals yet</td></tr>'}
    </tbody>
  </table>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<script>
const ctx = document.getElementById('outcomesChart');
if (window.Chart) {{
  new Chart(ctx, {{
    type: 'doughnut',
    data: {{
      labels: ['Wins', 'Losses'],
      datasets: [{{
        data: [{stats['won']}, {stats['lost']}],
        backgroundColor: ['#3fb950', '#f85149'],
        borderWidth: 0
      }}]
    }},
    options: {{
      responsive: true,
      plugins: {{
        legend: {{
          labels: {{
            color: '#c9d1d9'
          }}
        }}
      }}
    }}
  }});
}}

// Auto-refresh every 60 seconds
setTimeout(function(){{ location.reload(); }}, 60000);
</script>
</body>
</html>"""
    return HTMLResponse(content=html)
