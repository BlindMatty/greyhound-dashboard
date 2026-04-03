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

  // Auto-select first state by earliest race time
  const first = summaryData.states
    .filter(s => s.hasData)
    .sort((a, b) => parseTime(a.earliestRaceTime) - parseTime(b.earliestRaceTime))[0];
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
  // Sort by race start time (all times are AEST)
  allHC.sort((a, b) => {
    const ta = parseTime(a.raceStartTime);
    const tb = parseTime(b.raceStartTime);
    if (ta !== tb) return ta - tb;
    return (a.track || '').localeCompare(b.track || '') || (a.raceNumber || 0) - (b.raceNumber || 0);
  });
  renderHighConfidence(allHC);
}

/** Parse "11:17AM" / "8:53PM" into minutes since midnight for sorting. */
function parseTime(s) {
  if (!s) return 9999;
  const m = s.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if (!m) return 9999;
  let h = parseInt(m[1], 10);
  const min = parseInt(m[2], 10);
  const pm = m[3].toUpperCase() === 'PM';
  if (pm && h !== 12) h += 12;
  if (!pm && h === 12) h = 0;
  return h * 60 + min;
}

function renderHighConfidence(picks) {
  const el = document.getElementById('hcPicks');
  if (!picks.length) { hide('hcSection'); return; }

  el.innerHTML = picks.map(p => {
    const ensOdds = p.ensemble_odds || p.implied_odds || 0;
    const ensProb = p.ensemble_prob || p.probability || 0;
    const mcPct = p.mc_win_pct != null ? p.mc_win_pct : '';
    const safeDog = p.dog ? String(p.dog).toLowerCase().replace(/[^a-z0-9\s]/g, '').trim().replace(/\s+/g, '-') : 'unknown';
      const slug = `${p.state}_${String(p.track).toLowerCase()}_r${p.raceNumber}_${safeDog}.json`;
      return `
    
    <div class="hc-card" onclick="openHCModal('${slug}')" style="cursor:pointer" title="Click for Full 50-step Assessment">
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
    .sort((a, b) => parseTime(a.earliestRaceTime) - parseTime(b.earliestRaceTime))
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

  container.innerHTML = data.races
    .slice()
    .sort((a, b) => {
      const ta = parseTime(a.start_time);
      const tb = parseTime(b.start_time);
      if (ta !== tb) return ta - tb;
      return (a.track || '').localeCompare(b.track || '') || (a.raceNumber || 0) - (b.raceNumber || 0);
    })
    .map((race, i) => {
    const dogs = (race.dogs || [])
      .filter(d => !d.scratched)
      .sort((a, b) => (b.ensemble_prob || b.probability || 0) - (a.ensemble_prob || a.probability || 0));

    // Determine each model's top pick
    const mlTop = dogs.reduce((best, d) => (!best || (d.probability || 0) > (best.probability || 0)) ? d : best, null);
    const ensTop = dogs.reduce((best, d) => (!best || (d.ensemble_prob || 0) > (best.ensemble_prob || 0)) ? d : best, null);
    const mcTop = dogs.reduce((best, d) => {
      const mc = d.mc_win_pct != null && d.mc_win_pct > 0 ? d.mc_win_pct : 0;
      const bestMc = best && best.mc_win_pct != null && best.mc_win_pct > 0 ? best.mc_win_pct : 0;
      return mc > bestMc ? d : best;
    }, null);
    const topDog = ensTop || mlTop;

    // Tag each dog with which models pick it as #1
    const topNames = { ml: mlTop?.dog, ens: ensTop?.dog, mc: mcTop?.dog };

    return `
      <div class="race-card">
        <div class="race-header" onclick="toggleRace(this)">
          <div>
            <span class="race-title">${esc(race.track)} R${race.raceNumber}</span>
            <span class="race-meta">${esc(race.start_time || '')}${race.grade ? ' · ' + esc(race.grade) : ''}</span>
          </div>
          <div style="display:flex;align-items:center;gap:12px">
            ${topDog ? `<span class="race-meta">Pick: <strong>${esc(topDog.dog)}</strong> (Box ${topDog.box}) ${((topDog.ensemble_prob || topDog.probability) * 100).toFixed(1)}%</span>` : ''}
            <span class="race-toggle">▼</span>
          </div>
        </div>
        <div class="race-body${i === 0 ? ' open' : ''}">
          <table class="dog-table">
            <thead>
              <tr>
                <th>Box</th>
                <th>Rug</th>
                <th>Dog</th>
                <th>ENS %</th>
                <th>ML %</th>
                <th>MC %</th>
                <th>ENS Odds</th>
              </tr>
            </thead>
            <tbody>
              ${dogs.map((d, di) => dogRow(d, di === 0, topNames)).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }).join('');
}

function dogRow(d, isTop, topNames) {
  const prob = d.probability || 0;
  const eProb = d.ensemble_prob || 0;
  const eOdds = d.ensemble_odds || 0;
  const mc = d.mc_win_pct != null ? d.mc_win_pct : '';
  const tierClass = d.isHighConf ? 'tier-green' : isTop ? 'tier-yellow' : '';
  const barW = Math.min(eProb * 200, 80);
  const rug = d.rug || d.box;

  // Model top-pick badges
  const badges = [];
  if (topNames.ens && d.dog === topNames.ens) badges.push('<span class="badge badge-ens">ENS</span>');
  if (topNames.ml && d.dog === topNames.ml) badges.push('<span class="badge badge-ml">ML</span>');
  if (topNames.mc && d.dog === topNames.mc) badges.push('<span class="badge badge-mc">MC</span>');
  const badgeHtml = badges.length ? ' ' + badges.join('') : '';

  return `
    <tr class="${d.scratched ? 'scratched' : ''} ${isTop ? 'top-pick' : ''}">
      <td><span class="box-num box-${d.box}">${d.box}</span></td>
      <td><span class="box-num box-${rug}">${rug}</span></td>
      <td class="${tierClass}">${esc(d.dog)}${d.isHighConf ? ' ⭐' : ''}${badgeHtml}</td>
      <td>${eProb ? (eProb * 100).toFixed(1) + '%' : '—'}<span class="prob-bar" style="width:${barW}px"></span></td>
      <td>${(prob * 100).toFixed(1)}%</td>
      <td>${mc !== '' ? (typeof mc === 'number' ? mc.toFixed(1) : mc) + '%' : '—'}</td>
      <td>${eOdds ? '$' + eOdds.toFixed(2) : '—'}</td>
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


// HC Modal System
window.openHCModal = function(slug) {
  const modal = document.getElementById('hcModal');
  const details = document.getElementById('hcModalDetails');
  if(!modal || !details) {
      console.error("Modal elements not found in DOM");
      return;
  }
  
  details.innerHTML = '<div style="padding: 20px; text-align: center;">Loading AI Analysis...</div>';
  modal.style.display = 'block';

  fetch('data/hc_profiles/' + slug)
    .then(r => function(res) {
        if(!res.ok) throw new Error("Not found");
        return res.json();
    }(r))
    .then(data => {
        if(!data || !data.steps || !data.steps['50_Final_Probability']) {
            details.innerHTML = '<span style="color:red; padding: 20px;">Invalid profile data structure.</span>';
            return;
        }
        
      let redHtml = data.steps['50_Final_Probability'].red_flags.map(f => `<li style="color:#e74c3c; margin-bottom:5px;">${f}</li>`).join('') || '<li>None</li>';
      let greenHtml = data.steps['50_Final_Probability'].green_flags.map(f => `<li style="color:#2ecc71; margin-bottom:5px;">${f}</li>`).join('') || '<li>None</li>';
      
      let finalScore = data.steps['50_Final_Probability'].final_score;
      let decColor = finalScore >= 3 ? '#2ecc71' : (finalScore <= -2 ? '#e74c3c' : '#f39c12');

      let scoreHtml = `<strong style="color:${decColor}; font-size:1.2em;">${data.steps['50_Final_Probability'].decision} (Score: ${finalScore})</strong>`;

      details.innerHTML = `
        <h4 style="margin:0 0 10px 0; color:#2c3e50;">${data.dog || 'Unknown Dog'} (R${data.race || '?'} ${data.track || '?'})</h4>
        <div style="margin-bottom: 20px; padding: 10px; background: #f8f9fa; border-radius: 4px; border-left: 4px solid ${decColor}">${scoreHtml}</div>
        <div style="display:flex; gap:20px; font-size:0.95em;">
          <div style="flex:1; background: #fafafa; padding: 10px; border-radius: 4px;"><strong><span style="color:#2ecc71">&#10003;</span> Green Flags</strong><ul style="margin:10px 0; padding-left:20px; color:#2c3e50;">${greenHtml}</ul></div>
          <div style="flex:1; background: #fafafa; padding: 10px; border-radius: 4px;"><strong><span style="color:#e74c3c">&#10007;</span> Red Flags</strong><ul style="margin:10px 0; padding-left:20px; color:#2c3e50;">${redHtml}</ul></div>
        </div>
      `;
    })
    .catch(err => {
      details.innerHTML = `<div style="color:#e74c3c; padding: 20px;">Failed to load profile for ${slug}. The JSON file may not exist yet.</div>`;
      console.error(err);
    });
};

window.closeHCModal = function() {
  const modal = document.getElementById('hcModal');
  if(modal) modal.style.display = 'none';
};

// Close when clicking outside of the modal content
window.onclick = function(event) {
  const modal = document.getElementById('hcModal');
  if (event.target == modal) {
    modal.style.display = 'none';
  }
};
