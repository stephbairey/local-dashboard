/* weather.js: renders the Weather slide and registers with DASH */
(function(){
  const util       = (window.DASH && window.DASH.util) || {};
  const escapeHtml = util.escapeHtml || (s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])));
  function numOrDash(v){ return (v==null || Number.isNaN(Number(v))) ? "—" : String(v); }
  function weatherEmoji(desc){
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

  window.DASH.register("slide-weather", function renderWeather(data){
    const el = document.getElementById("weather-content");
    if (!el) return;

    try{
      if (!data || !data.current) {
        el.innerHTML = '<p class="small">Weather data unavailable.</p>';
        return;
      }

      const cur   = data.current;
      const temp  = Math.round(Number(cur.temp ?? cur.temperature ?? 0));
      const desc  = String(cur.description || "Weather");
      const wind  = cur.wind_mph != null ? Math.round(Number(cur.wind_mph)) : null;
      const gust  = cur.wind_gust_mph != null ? Math.round(Number(cur.wind_gust_mph)) : null;
      const hum   = cur.humidity != null ? Math.round(Number(cur.humidity)) : null;
      const press = cur.pressure_inHg != null ? Number(cur.pressure_inHg) : null;
      const station = cur.station || "";
      const emoji = weatherEmoji(desc);

      const dailies = Array.isArray(data.daily) ? data.daily.slice(0,5) : [];
      const today   = dailies[0] || {};
      const hiToday = today?.temp?.max ?? null;
      const loToday = today?.temp?.min ?? null;

      const highs = dailies.map(d => Number(d?.temp?.max ?? NaN)).filter(n => Number.isFinite(n));
      let trendWord = "Steady", trendClass = "trend-steady", trendArrow = "→";
      if (highs.length >= 2) {
        if (highs.at(-1) > highs[0]) { trendWord = "Warming"; trendClass = "trend-up"; trendArrow = "▲"; }
        else if (highs.at(-1) < highs[0]) { trendWord = "Cooling"; trendClass = "trend-down"; trendArrow = "▼"; }
      }

      const next3 = dailies.slice(1,4).map(d => {
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
    } catch(e){
      el.innerHTML = `<p class="small mono">${escapeHtml(e.message || String(e))}</p>`;
      console.error("[weather]", e);
    }
  });
})();
