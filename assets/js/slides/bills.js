/* bills.js — shows only $-tagged bill events */
(function(){
  const R = (window.DASH && window.DASH.register) || function(){};
  const U = (window.DASH && window.DASH.util) || {};

  function row(ev){
    const dateStr = U.formatDateLong(ev.start);
    const timeStr = U.formatTimeRange(ev.start, ev.end);
    const EH = U.escapeHtml || (s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])));
    return `
      <div class="cal-row">
        <div class="cal-title">${EH(ev.title || "Bill")}</div>
        <div class="cal-date">${EH(dateStr)}</div>
        <div class="cal-loc"></div>
        <div class="cal-time">${EH(timeStr)}</div>
      </div>`;
  }

  R("slide-bills", function renderBills(data){
    const el = document.getElementById("bills-content");
    if (!el) return;

    try{
      const evs = Array.isArray(data?.events) ? data.events : [];
      if (evs.length === 0) {
        el.innerHTML = '<p class="small">Bills data unavailable.</p>'; return;
      }

      const now = Date.now();
      const items = evs
        .filter(ev => U.isBillTitle(ev.title))
        .sort((a,b)=> new Date(a.start) - new Date(b.start))
        .filter(ev => new Date(ev.end || ev.start).getTime() >= now)
        .slice(0, 10)
        .map(row).join("");

      el.innerHTML = items || '<p class="small">No upcoming bills.</p>';
    } catch(e){
      el.innerHTML = `<p class="small mono">${(e.message||e)}</p>`;
      console.error("[bills]", e);
    }
  });
})();
