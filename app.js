/* Greyhound Dashboard — vanilla JS, no build step */

const DATA_DIR = './data';
const STATES = ['vic','nsw','qld','wa','sa','tas','nz','nt'];
const STATE_NAMES = {
  vic:'Victoria', nsw:'New South Wales', qld:'Queensland', wa:'Western Australia',
  sa:'South Australia', tas:'Tasmania', nz:'New Zealand', nt:'Northern Territory'
};

// ── State ───────────────────────────────────────────
let currentDate = '';
let summaryData = null;
let stateDataCache = {};   // { state: data }
let activeState = null;

// ── Init ────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);

async function init() {
  const picker = document.getElementById('datePicker');
  document.getElementById('prevDay').addEventListener('click', () => shiftDay(-1));
  document.getElementById('nextDay').addEventListener('click', () => shiftDay(1));
  picker.addEventListener('change', () => loadDate(picker.value));

  // Load latest.json to find default date
  try {
    const latest = await fetchJSON(`${DATA_DIR}/latest.json`);
    loadDate(latest.date);
  } catch {
    // Fallback: today in AEST (UTC+11)
    const now = new Date();
    const aest = new Date(now.getTime() + (11 * 60 * 60 * 1000));
    loadDate(aest.toISOString().slice(0, 10));
  }
}

// ── Date navigation ─────────────────────────────────
function shiftDay(delta) {
  if (!currentDate) return;
  const d = new Date(currentDate + 'T00:00:00');
  d.setDate(d.getDate() + delta);
  loadDate(d.toISOString().slice(0, 10));
}

// ── Main load ───────────────────────────────────────
async function loadDate(dateStr) {
  currentDate = dateStr;
  document.getElementById('datePicker').value = dateStr;
  stateDataCache = {};
  activeState = null;

  show('loading'); hide('error'); hide('summaryBar'); hide('hcSection'); hide('statesSection');

  try {
    summaryData = await fetchJSON(`${DATA_DIR}/summary_${dateStr}.json`);
  } catch {
    showError(`No data available for ${formatDate(dateStr)}. Predictions may not have been generated yet.`);
    return;
  }

  renderSummary(summaryData);

  // High confidence picks are loaded from state prediction JSONs
  // (consensus: ML + ENS + MC all agree on #1 pick)
  // We load them after the first state is selected
  renderStateTabs(summaryData.states);
  loadHighConfidencePicks(summaryData.states);

  // Auto-select first state with data
  const first = summaryData.states.find(s => s.hasData);
  if (first) selectState(first.code);
}

// ── Render summary bar ──────────────────────────────
function renderSummary(data) {
  const statesWithData = data.states.filter(s => s.hasData).length;
  const totalRaces = data.states.reduce((n, s) => n + Math.ceil((s.totalPredictions || 0) / 7), 0);
  document.getElementById('statDate').textContent = formatDate(data.date);
  document.getElementById('statStates').textContent = statesWithData;
  document.getElementById('statRaces').textContent = totalRaces;
  document.getElementById('statDogs').textContent = data.totalPredictions || 0;
  document.getElementById('statHC').textContent = data.totalHighConfidence || 0;
  show('summaryBar');
}

// ── High confidence picks (consensus: ML + ENS + MC agree) ──
async function loadHighConfidencePicks(states) {
  const allHC = [];
  const fetches = states.filter(s => s.hasData).map(async (s) => {
    try {
      const data = await fetchJSON(`${DATA_DIR}/${s.code}_predictions_${currentDate}.json`);
      stateDataCache[s.code] = data;
      for (const p of (data.highConfidencePicks || [])) {
        allHC.push({ ...p, state: s.code, stateName: s.name });
      }
    } catch { /* skip */ }
  });
  await Promise.all(fetches);
  renderHighConfidence(allHC);
}

function renderHighConfidence(picks) {
  const el = document.getElementById('hcPicks');
  if (!picks.length) { hide('hcSection'); return; }

  el.innerHTML = picks.map(p => {
    const ensOdds = p.ensemble_odds || p.implied_odds || 0;
    const ensProb = p.ensemble_prob || p.probability || 0;
    const mcPct = p.mc_win_pct != null ? p.mc_win_pct : '';
    return `
    <div class="hc-card">
      <div class="hc-left">
        <span class="hc-dog">${esc(p.dog)}</span>
        <span class="hc-meta">
          Box ${p.box} · ${esc(p.track)} R${p.raceNumber} · ${esc(p.raceStartTime || '')}
          · ${esc(p.stateName)}
        </span>
        <span class="hc-meta">
          ML ${(p.probability * 100).toFixed(1)}%
          · ENS ${(ensProb * 100).toFixed(1)}%
          ${mcPct !== '' ? '· MC ' + (typeof mcPct === 'number' ? mcPct.toFixed(1) : mcPct) + '%' : ''}
        </span>
      </div>
      <div>
        <div class="hc-odds">$${ensOdds.toFixed(2)}</div>
        <div style="font-size:0.7rem;color:var(--text-dim);text-align:right">ENS implied</div>
      </div>
    </div>
  `}).join('');
  show('hcSection');
}

// ── State tabs ──────────────────────────────────────
function renderStateTabs(states) {
  const container = document.getElementById('stateTabs');
  container.innerHTML = states
    .filter(s => s.hasData)
    .map(s => `
      <div class="state-tab" data-state="${s.code}" onclick="selectState('${s.code}')">
        ${s.name} <span class="tab-count">(${s.totalPredictions})</span>
      </div>
    `)
    .join('');
  show('statesSection');
}

async function selectState(stateCode) {
  activeState = stateCode;

  // Highlight tab
  document.querySelectorAll('.state-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.state === stateCode);
  });

  const container = document.getElementById('stateContent');
  container.innerHTML = '<div class="loading">Loading races…</div>';

  // Fetch state data if not cached
  if (!stateDataCache[stateCode]) {
    try {
      stateDataCache[stateCode] = await fetchJSON(`${DATA_DIR}/${stateCode}_predictions_${currentDate}.json`);
    } catch {
      container.innerHTML = `<div class="error">Could not load ${STATE_NAMES[stateCode]} data.</div>`;
      return;
    }
  }

  renderRaces(stateDataCache[stateCode]);
}

// ── Render races ────────────────────────────────────
function renderRaces(data) {
  const container = document.getElementById('stateContent');
  if (!data.races || !data.races.length) {
    container.innerHTML = '<div class="error">No races found.</div>';
    return;
  }

  container.innerHTML = data.races.map((race, i) => {
    const dogs = (race.dogs || [])
      .filter(d => !d.scratched)
      .sort((a, b) => (b.probability || 0) - (a.probability || 0));
    const topDog = dogs[0];

    return `
      <div class="race-card">
        <div class="race-header" onclick="toggleRace(this)">
          <div>
            <span class="race-title">${esc(race.track)} R${race.raceNumber}</span>
            <span class="race-meta">${esc(race.start_time || '')}${race.grade ? ' · ' + esc(race.grade) : ''}</span>
          </div>
          <div style="display:flex;align-items:center;gap:12px">
            ${topDog ? `<span class="race-meta">Pick: <strong>${esc(topDog.dog)}</strong> (Box ${topDog.box}) ${(topDog.probability * 100).toFixed(1)}%</span>` : ''}
            <span class="race-toggle">▼</span>
          </div>
        </div>
        <div class="race-body${i === 0 ? ' open' : ''}">
          <table class="dog-table">
            <thead>
              <tr>
                <th>Box</th>
                <th>Dog</th>
                <th>ML Prob</th>
                <th>ML Odds</th>
                <th>Ens Prob</th>
                <th>Ens Odds</th>
                <th>MC Win%</th>
              </tr>
            </thead>
            <tbody>
              ${dogs.map((d, di) => dogRow(d, di === 0)).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }).join('');
}

function dogRow(d, isTop) {
  const prob = d.probability_norm || d.probability || 0;
  const odds = d.implied_odds_norm || d.implied_odds || 0;
  const eProb = d.ensemble_prob || 0;
  const eOdds = d.ensemble_odds || 0;
  const mc = d.mc_win_pct != null ? d.mc_win_pct : '';
  const tierClass = d.isHighConf ? 'tier-green' : isTop ? 'tier-yellow' : '';
  const barW = Math.min(prob * 200, 80);

  return `
    <tr class="${d.scratched ? 'scratched' : ''} ${isTop ? 'top-pick' : ''}">
      <td><span class="box-num box-${d.box}">${d.box}</span></td>
      <td class="${tierClass}">${esc(d.dog)}${d.isHighConf ? ' ⭐' : ''}</td>
      <td>${(prob * 100).toFixed(1)}%<span class="prob-bar" style="width:${barW}px"></span></td>
      <td>$${odds.toFixed(2)}</td>
      <td>${eProb ? (eProb * 100).toFixed(1) + '%' : '—'}</td>
      <td>${eOdds ? '$' + eOdds.toFixed(2) : '—'}</td>
      <td>${mc !== '' ? mc.toFixed ? mc.toFixed(1) + '%' : mc + '%' : '—'}</td>
    </tr>
  `;
}

// ── Toggle race expand/collapse ─────────────────────
function toggleRace(headerEl) {
  const body = headerEl.nextElementSibling;
  body.classList.toggle('open');
  const arrow = headerEl.querySelector('.race-toggle');
  arrow.textContent = body.classList.contains('open') ? '▲' : '▼';
}

// ── Helpers ─────────────────────────────────────────
async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-AU', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
}

function esc(s) {
  if (s == null) return '';
  const el = document.createElement('span');
  el.textContent = String(s);
  return el.innerHTML;
}

function show(id) { document.getElementById(id).hidden = false; }
function hide(id) { document.getElementById(id).hidden = true; }
function showError(msg) {
  hide('loading');
  const el = document.getElementById('error');
  el.textContent = msg;
  el.hidden = false;
}
