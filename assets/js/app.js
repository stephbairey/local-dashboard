"use strict";

/* ================= CLOCK ================= */
(() => {
  const $time  = document.getElementById("clock-time");
  const $dowln = document.getElementById("clock-dowline");
  const $date  = document.getElementById("clock-date");

  function periodOfDay(h) {
    if (h < 5)  return "Night";
    if (h < 12) return "Morning";
    if (h < 17) return "Afternoon";
    if (h < 21) return "Evening";
    return "Night";
  }

  function updateClock() {
    const now = new Date();
    const h = now.getHours();
    const m = now.getMinutes();
    const h12 = ((h + 11) % 12) + 1;
    const ampm = h >= 12 ? "pm" : "am";
    const weekday = now.toLocaleDateString(undefined, { weekday: "long" });
    const dateStr = now.toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" });
    if ($time)  $time.textContent  = `${h12}:${String(m).padStart(2, "0")} ${ampm}`;
    if ($dowln) $dowln.textContent = `${weekday} ${periodOfDay(h)}`;
    if ($date)  $date.textContent  = dateStr;
  }
  updateClock();
  setInterval(updateClock, 1000);
})();

/* ================= SLIDE ROTATION ================= */
const ROTATE_MS = 10000;
const slides = Array.from(document.querySelectorAll(".slide"));
let currentIndex = 0;

function setError(id, msg) {
  console.error(`[dashboard] ${id}: ${msg}`);
  const map = { "slide-weather":"weather-content","slide-calendar":"calendar-content","slide-bills":"bills-content","slide-tides":"tides-content" };
  const elId = map[id]; if (!elId) return;
  const el = document.getElementById(elId);
  if (el) el.innerHTML = `<p class="small mono">${escapeHtml(String(msg))}</p>`;
}

async function fetchJSON(url) {
  const cacheBust = url.includes("?") ? "&" : "?";
  const full = url + cacheBust + "t=" + Date.now();
  const res = await fetch(full, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load ${url} (${res.status})`);
  return res.json();
}

function showSlide(idx) {
  slides.forEach((s, i) => s.classList.toggle("active", i === idx));
  const active = slides[idx];
  if (active && !active.dataset.static) {
    const url = active.dataset.endpoint;
    if (url) {
      fetchJSON(url)
        .then(data => { try { renderSlide(active.id, data); } catch (e) { setError(active.id, `Render error: ${e.message || e}`); } })
        .catch(err => setError(active.id, err.message || err));
    }
  }
}
function nextSlide() { currentIndex = (currentIndex + 1) % slides.length; showSlide(currentIndex); }
setInterval(nextSlide, ROTATE_MS);
showSlide(currentIndex);

/* ================= RENDERERS ================= */
function renderSlide(id, data) {
  if (id === "slide-weather")  return renderWeather(data);
  if (id === "slide-calendar") return renderCalendar(data);
  if (id === "slide-tides")    return renderTides(data);
  if (id === "slide-bills")    return renderBills(data);
}

/* ---- Weather (hero temp+icon; details; 2x2 trend + next 3) ---- */
function renderWeather(data) {
  const el = document.getElementById("weather-content");
  if (!el) return;
  if (!data || !data.current) {
    el.innerHTML = '<p class="small">Weather data unavailable.</p>';
    return;
  }

  const cur = data.current;
  const temp = Math.round(Number(cur.temp ?? cur.temperature ?? 0));
  const desc = String(cur.description || "Weather");
  const wind = cur.wind_mph != null ? Math.round(Number(cur.wind_mph)) : null;
  const gust = cur.wind_gust_mph != null ? Math.round(Number(cur.wind_gust_mph)) : null;
  const hum  = cur.humidity != null ? Math.round(Number(cur.humidity)) : null;
  const press= cur.pressure_inHg != null ? Number(cur.pressure_inHg) : null;
  const station = cur.station || "";
  const emoji = weatherEmoji(desc);

  const dailies = Array.isArray(data.daily) ? data.daily.slice(0,5) : [];
  const today   = dailies[0] || {};
  const hiToday = today?.temp?.max ?? null;
  const loToday = today?.temp?.min ?? null;

  const highs = dailies.map(d => Number(d?.temp?.max ?? NaN)).filter(n => Number.isFinite(n));
  let trendWord = "Steady", trendClass = "trend-steady", trendArrow = "→";
  if (highs.length >= 2) {
    if (highs[highs.length-1] > highs[0]) { trendWord = "Warming"; trendClass = "trend-up"; trendArrow = "▲"; }
    else if (highs[highs.length-1] < highs[0]) { trendWord = "Cooling"; trendClass = "trend-down"; trendArrow = "▼"; }
  }

  const next3 = (dailies.slice(1,4)).map(d => {
    const dt = new Date((d.dt || 0) * 1000);
    const name = dt.toLocaleDateString([], { weekday: "short" });
    const hi = Math.round(Number(d?.temp?.max ?? 0));
    const lo = Math.round(Number(d?.temp?.min ?? 0));
    return `
      <div class="card quad-card">
        <div class="quad-day">${name}</div>
        <div class="quad-temps">Hi ${hi}° · Lo ${lo}°</div>
      </div>`;
  }).join("");

  el.innerHTML = `
    <div class="card weather-hero only-hero">
      <div class="wx-temp">${temp}°</div>
      <div class="wx-emoji" aria-label="${escapeHtml(desc)}">${emoji}</div>
    </div>

    <div class="card weather-details">
      <div class="wx-desc">${escapeHtml(desc)}</div>
      <div class="wx-chips">
        ${numOrDash(hiToday) !== "—" && numOrDash(loToday) !== "—" ? `<span class="chip">H ${Math.round(hiToday)}° · L ${Math.round(loToday)}°</span>` : ""}
        ${wind != null ? `<span class="chip">Wind ${wind} mph${gust!=null?`, G ${gust}`:""}</span>` : ""}
        ${hum  != null ? `<span class="chip">Humidity ${hum}%</span>` : ""}
        ${press!= null ? `<span class="chip">Pressure ${press.toFixed(2)} inHg</span>` : ""}
        ${station ? `<span class="chip">Station ${escapeHtml(station)}</span>` : ""}
      </div>
    </div>

    <div class="weather-quad">
      <div class="card quad-card trend ${trendClass}">
        <div class="trend-main"><span class="arrow ${trendClass.replace("trend-","")}">${trendArrow}</span> ${trendWord}</div>
      </div>
      ${next3}
    </div>
  `;
}

/* ---- Calendar (hide bills) ---- */
function renderCalendar(data) {
  const el = document.getElementById("calendar-content");
  if (!el) return;
  if (!data || !Array.isArray(data.events)) {
    el.innerHTML = '<p class="small">Calendar data unavailable.</p>';
    return;
  }
  const items = data.events
    .filter(ev => !isBillTitle(ev.title || ""))
    .slice(0, 10)
    .map(ev => renderCalRow(ev))
    .join("");
  el.innerHTML = items || '<p class="small">No upcoming events.</p>';
}

/* ---- Bills (only bills) ---- */
function renderBills(data) {
  const el = document.getElementById("bills-content");
  if (!el) return;
  if (!data || !Array.isArray(data.events)) {
    el.innerHTML = '<p class="small">Bills data unavailable.</p>';
    return;
  }
  const items = data.events
    .filter(ev => isBillTitle(ev.title || ""))
    .slice(0, 10)
    .map(ev => renderCalRow(ev))
    .join("");
  el.innerHTML = items || '<p class="small">No upcoming bills.</p>';
}

/* ================= SHARED HELPERS ================= */
function renderCalRow(ev) {
  const dateStr = formatDateLong(ev);
  const timeStr = formatTimeRange(ev);
  const locStr  = (ev.location && ev.location.trim()) ? linkifyLocation(ev.location.trim()) : "";
  return `
    <div class="cal-row">
      <div class="cal-title">${escapeHtml(ev.title || "Untitled")}</div>
      <div class="cal-date">${escapeHtml(dateStr)}</div>
      <div class="cal-loc">${locStr}</div>
      <div class="cal-time">${escapeHtml(timeStr)}</div>
    </div>`;
}
function formatDateLong(ev) {
  const d = new Date(ev.start);
  return d.toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" });
}
function isAllDayEvent(ev) {
  const s = ev.start || ""; const e = ev.end || "";
  const hasOffset = /(?:Z|[+-]\d{2}:\d{2})$/.test(s);
  if (s.includes("T00:00:00") && !hasOffset) return true;
  if (e) { const sd = new Date(s), ed = new Date(e); const durH = (ed - sd) / 3600000;
    if (sd.getHours() === 0 && sd.getMinutes() === 0 && durH >= 20) return true; }
  return false;
}
function formatTimeRange(ev) {
  if (isAllDayEvent(ev)) return "";
  const start = new Date(ev.start);
  const end   = ev.end ? new Date(ev.end) : null;
  const opts  = { hour: "numeric", minute: "2-digit" };
  const s = start.toLocaleTimeString([], opts);
  if (!end) return s;
  const e = end.toLocaleTimeString([], opts);
  return (e === s) ? s : `${s} to ${e}`;
}
function isBillTitle(title) { return /\(\$\d[\d,]*(?:\.\d{2})?\)/.test(title); }

/* domain-only link text; normalize *.zoom.us → 'zoom.us' */
function linkifyLocation(loc) {
  if (!/^https?:\/\//i.test(loc)) return escapeHtml(loc);
  const href = loc.trim();
  const domain = extractDomain(href);
  const safeHref = escapeHtml(href);
  const safeText = escapeHtml(domain);
  return `<a href="${safeHref}" target="_blank" rel="noopener">${safeText}</a>`;
}
function extractDomain(url) {
  try {
    const u = new URL(url);
    const host = u.hostname.toLowerCase();
    const parts = host.split(".");
    let base = parts.length >= 2 ? parts.slice(-2).join(".") : host;
    if (host.endsWith(".zoom.us") || host === "zoom.us") base = "zoom.us";
    if (host.endsWith(".zoom.com") || host === "zoom.com") base = "zoom.com";
    return base;
  } catch { return url; }
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));
}

/* Weather helpers */
function weatherEmoji(desc) {
  const d = String(desc || "").toLowerCase();
  if (d.includes("snow")) return "🌨️";
  if (d.includes("thunder")) return "⛈️";
  if (d.includes("rain") || d.includes("shower") || d.includes("drizzle")) return "🌧️";
  if (d.includes("fog") || d.includes("mist") || d.includes("haze")) return "🌫️";
  if (d.includes("wind")) return "🌬️";
  if (d.includes("cloud")) return "☁️";
  if (d.includes("partly") || d.includes("few")) return "🌤️";
  if (d.includes("clear") || d.includes("sun")) return "☀️";
  return "⛅";
}
function numOrDash(v){ return (v==null || Number.isNaN(Number(v))) ? "—" : String(v); }

/* ================= TIDES + MOON ================= */
function timeShort(d){ return new Date(d).toLocaleTimeString([], { hour:"numeric", minute:"2-digit" }); }
function feet2(v){ const n = Number(v); return Number.isFinite(n) ? n.toFixed(2) : "—"; }

function moonEmoji(phaseName, illumPct){
  const p = String(phaseName||"").toLowerCase();
  if (p.includes("new")) return "🌑";
  if (p.includes("waxing cres")) return "🌒";
  if (p.includes("first")) return "🌓";
  if (p.includes("waxing gibb")) return "🌔";
  if (p.includes("full")) return "🌕";
  if (p.includes("waning gibb")) return "🌖";
  if (p.includes("last") || p.includes("third")) return "🌗";
  if (p.includes("waning cres")) return "🌘";
  // fallback by illumination
  const illum = Number(illumPct||0);
  if (illum >= 95) return "🌕";
  if (illum >= 60) return "🌖";
  if (illum >= 40) return "🌓";
  if (illum >= 10) return "🌒";
  return "🌑";
}

async function renderTides(data) {
  const el = document.getElementById("tides-content");
  if (!el) return;
  if (!data || !Array.isArray(data.predictions)) {
    el.innerHTML = '<p class="small">Tide data unavailable.</p>';
    return;
  }

  // Try to load moon.json in parallel; failures are fine.
  let moon = null;
  try { moon = await fetchJSON("/dashboard/api/read.php?file=moon.json"); } catch {}

  const now = new Date();
  const preds = data.predictions
    .map(p => ({ t: new Date(p.t), v: Number(p.v), type: p.type }))
    .sort((a,b)=>a.t-b.t);

  // Find bracketing events around now
  let last = null, next = null;
  for (const p of preds) {
    if (p.t <= now) last = p;
    if (p.t > now && !next) { next = p; break; }
  }

  const nextHigh = preds.find(p => p.t > now && p.type === "H");
  const nextLow  = preds.find(p => p.t > now && p.type === "L");

  // Determine trend: coming in (rising) if between L -> H, going out (falling) if H -> L
  let trend = "Steady", arrow = "→", trendClass = "tide-steady", untilStr = "";
if (last && next) {
  if (last.type === "L" && next.type === "H") { trend = "Coming in";  arrow = "▲"; trendClass = "tide-up";   untilStr = `until ${timeShort(next.t)}`; }
  else if (last.type === "H" && next.type === "L") { trend = "Going out"; arrow = "▼"; trendClass = "tide-down"; untilStr = `until ${timeShort(next.t)}`; }
  const mins = Math.abs(now - next.t) / 60000;
  if (mins <= 8) { trend = "Turning"; arrow = "⟲"; trendClass = "tide-turn"; untilStr = `at ${timeShort(next.t)}`; }
}


  const water = data.water_level || {};
  const levelStr = (water.v != null) ? `${feet2(water.v)} ft` : "—";
  const levelTime = water.t ? timeShort(water.t) : "";

  // Moon block
  let moonBlock = "";
  if (moon && moon.current) {
    const phase = moon.current.phase_name || "Moon";
    const illum = moon.current.illumination_pct;
    const emoji = moonEmoji(phase, illum);
    const nextFull = moon.next && moon.next.full_moon ? new Date(moon.next.full_moon) : null;
    const nextFullStr = nextFull ? nextFull.toLocaleDateString([], { weekday:"short", month:"short", day:"numeric" }) : "";
    moonBlock = `
      <div class="card moon-hero">
        <div class="moon-emoji">${emoji}</div>
        <div class="moon-info">
          <div class="moon-phase">${escapeHtml(phase)}</div>
          ${nextFullStr ? `<div class="moon-next">Next full moon: ${escapeHtml(nextFullStr)}</div>` : ""}
        </div>
      </div>`;
  }

  // Top tide status row (current + trend + next high/low cards)
  const nh = nextHigh ? `
    <div class="card tide-mini">
      <div class="mini-label">Next High</div>
      <div class="mini-value">${timeShort(nextHigh.t)}</div>
      <div class="mini-sub">${feet2(nextHigh.v)} ft</div>
    </div>` : "";

  const nl = nextLow ? `
    <div class="card tide-mini">
      <div class="mini-label">Next Low</div>
      <div class="mini-value">${timeShort(nextLow.t)}</div>
      <div class="mini-sub">${feet2(nextLow.v)} ft</div>
    </div>` : "";

  const statusRow = `
    <div class="tide-top">
      <div class="card tide-status ${trendClass}">
        <div class="tide-level">${levelStr}</div>
        <div class="tide-sub">${levelTime ? `at ${levelTime}` : ""}</div>
        <div class="tide-trend"><span class="tide-arrow">${arrow}</span> ${trend}${untilStr ? ` ${untilStr}` : ""}</div>
      </div>
      ${nh}
      ${nl}
    </div>`;

  // Upcoming prediction grid (next ~9 entries)
  const items = preds.slice(0, 9).map(p => {
    const hhmm = timeShort(p.t);
    const typ  = p.type ? ` (${p.type})` : "";
    return `<div class="card"><div><strong>${hhmm}</strong>${typ}</div><div class="small">${feet2(p.v)} ft</div></div>`;
  }).join("");

  el.innerHTML = `
    ${moonBlock}
    ${statusRow}
    <div class="grid">${items}</div>
  `;
}
/* === Slide registry bootstrap (appends) === */
window.DASH = window.DASH || { slides:{}, util:{} };
window.DASH.register = function(id, fn){ window.DASH.slides[id] = fn; };
window.DASH.util.fetchJSON  = window.DASH.util.fetchJSON  || fetchJSON;
window.DASH.util.escapeHtml = window.DASH.util.escapeHtml || escapeHtml;

/* Prefer registered modules; fall back to built-ins */
function renderSlide(id, data){
  if (window.DASH && window.DASH.slides && typeof window.DASH.slides[id] === "function") {
    return window.DASH.slides[id](data);
  }
  if (id === "slide-weather")  return renderWeather(data);
  if (id === "slide-calendar") return renderCalendar(data);
  if (id === "slide-bills")    return renderBills(data);
  if (id === "slide-tides" && typeof renderTides === "function") return renderTides(data);
}
/* === Shared calendar helpers (util) === */
(function(){
  window.DASH = window.DASH || { util:{}, slides:{} };
  const U = window.DASH.util;

  U.extractDomain = U.extractDomain || function(url){
    try {
      const u = new URL(url);
      const host = u.hostname.toLowerCase();
      if (host.endsWith(".zoom.us") || host === "zoom.us") return "zoom.us";
      if (host.endsWith(".zoom.com") || host === "zoom.com") return "zoom.com";
      const parts = host.split(".");
      return parts.length >= 2 ? parts.slice(-2).join(".") : host;
    } catch { return url; }
  };

  U.linkifyLocation = U.linkifyLocation || function(loc){
    if (!/^https?:\/\//i.test(loc)) return (U.escapeHtml||escapeHtml)(loc);
    const href  = loc.trim();
    const text  = U.extractDomain(href);
    const EH    = U.escapeHtml || escapeHtml;
    return `<a href="${EH(href)}" target="_blank" rel="noopener">${EH(text)}</a>`;
  };

  U.isBillTitle = U.isBillTitle || function(title){
    return /\(\$\d[\d,]*(?:\.\d{2})?\)/.test(title || "");
  };

  U.isAllDayEvent = U.isAllDayEvent || function(start, end){
    const s = start || "", e = end || "";
    const hasOffset = /(?:Z|[+-]\d{2}:\d{2})$/.test(s);
    if (s.includes("T00:00:00") && !hasOffset) return true;
    if (e) {
      const sd = new Date(s), ed = new Date(e);
      const durH = (ed - sd) / 3600000;
      if (sd.getHours() === 0 && sd.getMinutes() === 0 && durH >= 20) return true;
    }
    return false;
  };

  U.formatDateLong = U.formatDateLong || function(dStr){
    const d = new Date(dStr);
    return d.toLocaleDateString([], { weekday:"long", month:"long", day:"numeric" });
  };

  U.formatTimeRange = U.formatTimeRange || function(start, end){
    if (U.isAllDayEvent(start, end)) return "";
    const s = new Date(start).toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
    if (!end) return s;
    const e = new Date(end).toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
    return (e === s) ? s : `${s} to ${e}`;
  };
})();

