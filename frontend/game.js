"use strict";
/* Smart Energy Conservation Game: real-time front end.
 *
 * Runs inside a Streamlit custom component. Streamlit (Python) sends the appliance table,
 * levels, tariff and scoring constants from game/engine.py, so the live numbers here use the same
 * inputs. The final score is calculated again by the Python engine and shown when it arrives.
 */
(function () {
  const SVGNS = "http://www.w3.org/2000/svg";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const pad = (n) => String(n).padStart(2, "0");

  /* ---------------- constants ---------------- */
  const SEC_PER_HOUR = 3; // real seconds per game hour at 1x
  const COLORS = {
    fridge: "#5ac8fa", cooktop: "#ff7a45", ac: "#3d6bff", fan: "#6ee7b7", lights: "#ffd166",
    tv: "#c084fc", computer: "#f472b6", washer: "#94a3b8", heater: "#ef4444", iron: "#a3e635",
  };
  const ICONS = {
    fridge: '<rect x="6" y="2" width="12" height="20" rx="2.5"/><path d="M6 10h12M9 5v2M9 13v3"/>',
    cooktop: '<rect x="3" y="14" width="18" height="6" rx="1.5"/><path d="M6 11c0-2 2-2 2-4M12 11c0-2 2-2 2-4M17 11c0-2 2-2 2-4"/>',
    ac: '<rect x="3" y="4" width="18" height="8" rx="2.5"/><path d="M6 16v2M12 16v4M18 16v2"/>',
    fan: '<circle cx="12" cy="12" r="1.6"/><path d="M12 10.4C12 6 14 3.6 16.2 4.6s.8 4-3.6 5.8"/><path d="M13.4 12.6c3.9 2.2 4.4 5 2.2 6.2s-3.9-1.3-3.6-5.8"/><path d="M10.6 12.6C6.7 14.8 3.8 13.8 3.8 11.4s3-2.6 6.8-1"/>',
    lights: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.5.4.8 1 .8 1.6V16h5.4v-.5c0-.6.3-1.2.8-1.6A6 6 0 0 0 12 3z"/>',
    tv: '<rect x="3" y="5" width="18" height="12" rx="2.5"/><path d="M8 21h8M12 17v4"/>',
    computer: '<rect x="3" y="4" width="18" height="12" rx="2.5"/><path d="M8 20h8M12 16v4"/>',
    washer: '<rect x="4" y="3" width="16" height="18" rx="2.5"/><circle cx="12" cy="13.5" r="4"/><path d="M7 6.5h2"/>',
    heater: '<rect x="7" y="2" width="10" height="20" rx="5"/><path d="M12 10c-2 2.4-3 3.7-3 4.8a3 3 0 0 0 6 0c0-1.1-1-2.4-3-4.8z"/>',
    iron: '<path d="M3 17h17a1 1 0 0 0 1-1 8 8 0 0 0-8-8H9L3 17z"/><path d="M3 20.5h18"/>',
  };
  const TAG_POS = {
    ac: [164, 176], computer: [313, 206], heater: [447, 190], iron: [578, 228], washer: [664, 214],
    tv: [172, 338], fan: [320, 340], fridge: [452, 326], cooktop: [606, 332], lights: [245, 196],
  };
  const SKY = [ // hour, top rgb, bottom rgb
    [0, [5, 9, 24], [12, 20, 52]], [5, [8, 14, 36], [30, 36, 84]], [6.5, [44, 58, 120], [244, 140, 98]],
    [8, [46, 118, 204], [140, 200, 245]], [13, [36, 116, 214], [150, 208, 248]], [17, [56, 100, 190], [244, 170, 110]],
    [19, [40, 44, 108], [236, 98, 88]], [20.5, [14, 20, 54], [40, 44, 100]], [24, [5, 9, 24], [12, 20, 52]],
  ];

  /* ---------------- state ---------------- */
  let cfg = null;
  let built = false;
  const S = {
    phase: "boot", level: "Medium", t: 0, speed: 1, playing: false, acc: 0, last: 0,
    on: {}, min: {}, nonce: null, local: null, shown: {}, flags: {}, ymax: 3, smax: 12,
  };

  /* ---------------- Streamlit bridge ---------------- */
  const inStreamlit = window.parent !== window;
  const post = (type, data) => window.parent.postMessage({ isStreamlitMessage: true, type, ...data }, "*");
  function fitHeight() {
    if (inStreamlit) post("streamlit:setFrameHeight", { height: Math.ceil($("#app").offsetHeight) + 4 });
  }
  window.addEventListener("message", (e) => {
    if (!e.data || e.data.type !== "streamlit:render") return;
    const args = e.data.args || {};
    if (args.config && !cfg) { cfg = args.config; init(); }
    if (args.result && S.nonce && args.result.nonce === S.nonce) showResult(args.result, true);
  });
  if (inStreamlit) post("streamlit:componentReady", { apiVersion: 1 });
  window.addEventListener("resize", () => { fitHeight(); });

  /* ---------------- helpers ---------------- */
  const period = (h) => (cfg.peak_hours.includes(h) ? "peak" : cfg.offpeak_hours.includes(h) ? "offpeak" : "standard");
  const app = (key) => cfg.appliances.find((a) => a.key === key);
  const level = () => cfg.levels.find((l) => l.name === S.level);
  const hoursOn = (key) => S.min[key].reduce((a, b) => a + b, 0) / 60;
  const hourKwh = (h) => cfg.appliances.reduce((s, a) => s + (a.watts / 1000) * S.min[a.key][h] / 60, 0);
  const powerKw = () => cfg.appliances.reduce((s, a) => s + (S.on[a.key] ? a.watts / 1000 : 0), 0);
  const money = (v) => cfg.currency + v.toFixed(2);

  function totals() {
    let kwh = 0, cost = 0;
    for (let h = 0; h < 24; h++) { const k = hourKwh(h); kwh += k; cost += k * cfg.tariff[period(h)]; }
    return { kwh, cost, co2: kwh * cfg.co2 };
  }
  function comfortRatio() {
    const opt = cfg.appliances.filter((a) => !a.essential);
    const tot = opt.reduce((s, a) => s + a.weight, 0);
    const met = opt.reduce((s, a) => s + a.weight * Math.min(hoursOn(a.key), a.target_hours) / a.target_hours, 0);
    return tot ? met / tot : 0;
  }
  function essentialsMissing() {
    return cfg.appliances.filter((a) => a.essential && hoursOn(a.key) < a.target_hours - 1e-6);
  }
  // Same formulas as game/engine.py; used for the live view and as a fallback for the final score.
  function evaluateLocal() {
    const sc = cfg.scoring, lv = level(), tt = totals(), comfort = comfortRatio(), miss = essentialsMissing();
    let off = 0, peak = 0;
    for (let h = 0; h < 24; h++) { const k = hourKwh(h); if (cfg.offpeak_hours.includes(h)) off += k; if (cfg.peak_hours.includes(h)) peak += k; }
    if (tt.kwh > 0) { off /= tt.kwh; peak /= tt.kwh; }
    const comfort_pts = sc.comfort_max * comfort;
    const budget_pts = tt.kwh <= lv.budget ? sc.budget_bonus_max * (lv.budget - tt.kwh) / lv.budget : -sc.over_penalty * (tt.kwh - lv.budget) / lv.budget;
    const timing_pts = sc.timing_max * (off - peak);
    const essential_pen = sc.essential_penalty * miss.length;
    const score = Math.max(0, Math.round(sc.base + comfort_pts + budget_pts + timing_pts - essential_pen));
    let rating = "Keep trying";
    for (const [name, f] of Object.entries(sc.rating_fractions)) { if (score >= f * lv.par) { rating = name; break; } }
    return { kwh: tt.kwh, co2: tt.co2, cost: tt.cost, budget_kwh: lv.budget, comfort, missing: miss.map((a) => a.name),
      base_pts: sc.base, comfort_pts, budget_pts, timing_pts, essential_pen, score, rating };
  }

  /* ---------------- build UI ---------------- */
  function el(tag, attrs = {}, html = "") {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    n.innerHTML = html;
    return n;
  }
  function resetSim() {
    S.t = 0; S.acc = 0; S.playing = false; S.flags = {}; S.nonce = null; S.local = null;
    S.ymax = 3; S.smax = Math.max(12, level().budget * 1.3);
    cfg.appliances.forEach((a) => { S.on[a.key] = a.key === "fridge"; S.min[a.key] = new Array(24).fill(0); });
  }

  function init() {
    resetSim();
    // stars
    const stars = $("#stars");
    for (let i = 0; i < 70; i++) {
      const c = document.createElementNS(SVGNS, "circle");
      c.setAttribute("cx", (Math.random() * 800).toFixed(1)); c.setAttribute("cy", (Math.random() * 300).toFixed(1));
      c.setAttribute("r", (Math.random() * 1.2 + 0.4).toFixed(2));
      c.style.animationDelay = (-Math.random() * 3).toFixed(2) + "s";
      c.style.animationDuration = (2 + Math.random() * 3).toFixed(2) + "s";
      stars.appendChild(c);
    }
    // wattage tags on the house
    const tags = $("#tags");
    cfg.appliances.forEach((a) => {
      const [x, y] = TAG_POS[a.key];
      const g = document.createElementNS(SVGNS, "g");
      g.setAttribute("transform", `translate(${x} ${y})`);
      const w = a.watts >= 1000 ? (a.watts / 1000).toFixed(1) + " kW" : a.watts + " W";
      g.innerHTML = `<g class="tag" data-key="${a.key}"><rect x="-27" y="-11" width="54" height="20" rx="10"/><text y="3.5">${w}</text></g>`;
      tags.appendChild(g);
    });
    // tray cards + legend + essentials
    const tray = $("#tray"), legend = $("#legend"), ess = $("#essentials");
    cfg.appliances.forEach((a, i) => {
      const c = COLORS[a.key];
      const card = el("button", { class: "card-dev", "data-key": a.key, style: `--c:${c}`, "aria-pressed": "false" }, `
        <span class="ico"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${ICONS[a.key]}</svg></span>
        <span class="nm">${a.name}<small>${a.watts >= 1000 ? (a.watts / 1000).toFixed(1) + " kW" : a.watts + " W"}${a.essential ? ' · <span class="ess">essential</span>' : ""}</small></span>
        <span class="sw"></span>
        <span class="prog"><span class="bar"><i></i></span><em>0.0 / ${a.target_hours} h</em></span>
        <span class="key">${(i + 1) % 10}</span>`);
      card.addEventListener("click", () => toggle(a.key));
      tray.appendChild(card);
      legend.appendChild(el("span", {}, `<i style="background:${c}"></i>${a.name}`));
      if (a.essential) ess.appendChild(el("div", { class: "chip", "data-key": a.key }, `<i></i><span>${a.name}</span><em style="font-style:normal;opacity:.8"></em>`));
    });
    $$("#house .dev").forEach((d) => d.addEventListener("click", () => toggle(d.dataset.key)));
    $("#costUnit").textContent = cfg.currency;
    // level picker
    const lv = $("#levels");
    cfg.levels.forEach((l) => {
      const b = el("button", { class: "lv" + (l.name === S.level ? " on" : ""), "data-l": l.name },
        `<b>${l.name}</b><div class="bud">${l.budget.toFixed(0)}<small> kWh</small></div><p>${l.description}</p>`);
      b.addEventListener("click", () => { S.level = l.name; $$(".lv").forEach((x) => x.classList.toggle("on", x === b)); });
      lv.appendChild(b);
    });
    $("#startBtn").addEventListener("click", startDay);
    $("#playBtn").addEventListener("click", togglePlay);
    $$("#speedSeg button").forEach((b) => b.addEventListener("click", () => {
      S.speed = +b.dataset.speed; $$("#speedSeg button").forEach((x) => x.classList.toggle("on", x === b));
    }));
    window.addEventListener("keydown", (e) => {
      if (S.phase !== "play") return;
      if (e.code === "Space") { e.preventDefault(); togglePlay(); return; }
      const n = e.key === "0" ? 9 : parseInt(e.key, 10) - 1;
      if (n >= 0 && n < cfg.appliances.length) toggle(cfg.appliances[n].key);
    });
    built = true; S.phase = "menu";
    fitHeight();
    setTimeout(fitHeight, 300);
    requestAnimationFrame(frame);
  }

  /* ---------------- game flow ---------------- */
  function startDay() {
    resetSim();
    S.phase = "play"; S.playing = true;
    $("#menu").classList.add("hidden"); $("#result").classList.add("hidden");
    $("#levelChip").textContent = `${S.level} · ${level().budget.toFixed(0)} kWh`;
    $("#ringOf").textContent = `of ${level().budget.toFixed(1)} kWh`;
    $("#stageHint").classList.remove("gone");
    setTimeout(() => $("#stageHint").classList.add("gone"), 6000);
    updatePlayIcon(); toast("Day started. Keep the fridge running.", "good");
  }
  function togglePlay() {
    if (S.phase !== "play") return;
    S.playing = !S.playing; updatePlayIcon();
  }
  function updatePlayIcon() {
    $("#playIcon").innerHTML = S.playing
      ? '<path d="M7 5h4v14H7zM13 5h4v14h-4z" fill="currentColor"/>'
      : '<path d="M8 5v14l11-7z" fill="currentColor"/>';
  }
  function toggle(key) {
    if (S.phase !== "play") return;
    S.on[key] = !S.on[key];
  }
  function toast(msg, kind = "") {
    const box = $("#toasts");
    const t = el("div", { class: "toast " + kind }, `<i></i><span>${msg}</span>`);
    box.appendChild(t);
    while (box.children.length > 3) box.removeChild(box.firstChild);
    setTimeout(() => t.remove(), 4100);
  }
  function stepMinute() {
    const h = Math.floor(S.t / 60);
    for (const a of cfg.appliances) if (S.on[a.key]) S.min[a.key][h] += 1;
    S.t += 1;
    if (S.t % 60 === 0 && S.t < 1440) {
      const nh = S.t / 60, p = period(nh), prev = period(nh - 1);
      if (p !== prev) {
        if (p === "peak") toast(`Peak pricing from ${pad(nh)}:00. Power costs ${money(cfg.tariff.peak)}/kWh`, "bad");
        else if (p === "offpeak") toast(`Off-peak from ${pad(nh)}:00. Cheapest power of the day`, "good");
        else toast(`Standard pricing from ${pad(nh)}:00`, "warn");
      }
    }
  }
  function finishDay() {
    S.playing = false; S.phase = "done"; updatePlayIcon();
    S.nonce = Date.now();
    S.local = evaluateLocal();
    showResult(S.local, false);
    if (inStreamlit) {
      const schedule = {};
      cfg.appliances.forEach((a) => (schedule[a.key] = S.min[a.key].map((m) => m / 60)));
      post("streamlit:setComponentValue", { value: { nonce: S.nonce, level: S.level, schedule }, dataType: "json" });
    }
  }

  /* ---------------- main loop ---------------- */
  function frame(ts) {
    // Game time follows the wall clock, so a slow machine drops frames instead of slowing the day.
    // A long gap (tab in the background) is capped so the game doesn't jump ahead.
    const elapsed = Math.min(1000, ts - (S.last || ts)); S.last = ts;
    const dt = Math.min(100, elapsed); // for visual smoothing only
    if (S.phase === "play" && S.playing) {
      S.acc += elapsed * (60 / (SEC_PER_HOUR * 1000)) * S.speed;
      while (S.acc >= 1 && S.t < 1440) { stepMinute(); S.acc -= 1; }
      if (S.t >= 1440) finishDay();
    }
    render(dt);
    requestAnimationFrame(frame);
  }

  function mix(a, b, f) { return a.map((v, i) => Math.round(lerp(v, b[i], f))); }
  function skyAt(h) {
    for (let i = 0; i < SKY.length - 1; i++) {
      const [h0, t0, b0] = SKY[i], [h1, t1, b1] = SKY[i + 1];
      if (h >= h0 && h <= h1) { const f = (h - h0) / (h1 - h0); return [mix(t0, t1, f), mix(b0, b1, f)]; }
    }
    return [SKY[0][1], SKY[0][2]];
  }
  const rgb = (c) => `rgb(${c[0]},${c[1]},${c[2]})`;
  function nightAmount(h) {
    if (h < 5 || h >= 21) return 1;
    if (h < 7) return 1 - (h - 5) / 2;
    if (h < 18) return 0;
    return (h - 18) / 3;
  }

  const setText = (sel, v) => { const n = $(sel); if (n.textContent !== v) n.textContent = v; };

  function render(dt) {
    if (!built) return;
    const hour = S.t / 60;
    const smooth = clamp(dt * 0.012, 0.02, 1);

    // clock, day bar
    setText("#clock", `${pad(Math.floor(hour) % 24)}:${pad(Math.floor(S.t % 60))}`);
    $("#dayBar").style.width = (S.t / 1440) * 100 + "%";

    // sky, sun, moon
    const [top, bot] = skyAt(hour);
    $("#skyTop").setAttribute("stop-color", rgb(top)); $("#skyBot").setAttribute("stop-color", rgb(bot));
    const night = nightAmount(hour);
    $("#stars").style.opacity = clamp(night * 1.1 - 0.1, 0, 1);
    const sunP = (hour - 6) / 12, sunVis = clamp(Math.min(hour - 5.5, 18.5 - hour) * 2, 0, 1);
    const ang = clamp(sunP, 0, 1) * Math.PI;
    $("#sun").setAttribute("transform", `translate(${400 - Math.cos(ang) * 360} ${430 - Math.sin(ang) * 400})`);
    $("#sun").style.opacity = sunVis;
    const mh = hour >= 18 ? hour - 18 : hour + 6, mAng = clamp(mh / 12, 0, 1) * Math.PI;
    const moonVis = clamp(Math.min(hour < 12 ? 6.5 - hour : hour - 17.5, 1) * 2, 0, 1);
    $("#moon").setAttribute("transform", `translate(${400 - Math.cos(mAng) * 360} ${430 - Math.sin(mAng) * 400})`);
    $("#moon").style.opacity = moonVis;
    $("#clouds").style.opacity = 1 - night * 0.7;

    // appliances in the house + tray
    const house = $("#house");
    house.classList.toggle("lights-on", !!S.on.lights);
    const dimOp = night * (S.on.lights ? 0.08 : 0.62);
    $$("#dim rect").forEach((r) => (r.style.opacity = dimOp.toFixed(3)));
    cfg.appliances.forEach((a) => {
      const on = !!S.on[a.key];
      $(`#house .dev[data-key="${a.key}"]`).classList.toggle("on", on);
      $(`#tags .tag[data-key="${a.key}"]`).classList.toggle("on", on);
      const card = $(`.card-dev[data-key="${a.key}"]`);
      card.classList.toggle("on", on);
      card.setAttribute("aria-pressed", on);
      const h = hoursOn(a.key);
      card.querySelector(".bar i").style.width = clamp(h / a.target_hours, 0, 1) * 100 + "%";
      setText(`.card-dev[data-key="${a.key}"] .prog em`, `${h.toFixed(1)} / ${a.target_hours} h`);
    });

    // HUD numbers
    const tt = totals(), lv = level(), ratio = tt.kwh / lv.budget, pw = powerKw();
    const sh = S.shown;
    ["kwh", "co2", "cost", "pw"].forEach((k) => (sh[k] = sh[k] === undefined ? 0 : sh[k]));
    sh.kwh = lerp(sh.kwh, tt.kwh, smooth); sh.co2 = lerp(sh.co2, tt.co2, smooth);
    sh.cost = lerp(sh.cost, tt.cost, smooth); sh.pw = lerp(sh.pw, pw, smooth * 1.6);
    setText("#ringKwh", sh.kwh.toFixed(2)); setText("#co2", sh.co2.toFixed(2));
    setText("#cost", sh.cost.toFixed(2)); setText("#powerNow", sh.pw.toFixed(2));
    $("#powerBar").style.width = clamp(sh.pw / 6, 0, 1) * 100 + "%";
    const ring = $("#ringFg"), circ = 490.1;
    ring.style.strokeDashoffset = circ * (1 - clamp(ratio, 0, 1));
    const col = ratio >= 1 ? "var(--red)" : ratio >= 0.75 ? "var(--amber)" : "var(--green)";
    ring.style.stroke = col; ring.style.color = col;
    $(".ring").classList.toggle("over", ratio >= 1);

    // pace
    const pace = $("#pace");
    if (S.t < 90) { pace.className = "pace"; setText("#pace", S.phase === "menu" ? "Start the day to see your pace" : "Measuring your pace…"); }
    else {
      const proj = (tt.kwh / S.t) * 1440, over = proj > lv.budget;
      // projection from average use so far; the fridge alone keeps it non-zero
      pace.className = "pace " + (proj > lv.budget * 1.1 ? "bad" : over ? "warn" : "good");
      setText("#pace", `On pace for ${proj.toFixed(1)} kWh · ${over ? "over" : "under"} budget by ${Math.abs(proj - lv.budget).toFixed(1)}`);
    }

    // tariff badge
    const p = period(Math.min(23, Math.floor(hour))), badge = $("#tariffBadge");
    badge.className = "badge " + p;
    setText("#tariffBadge", `${p === "offpeak" ? "Off-peak" : p === "peak" ? "Peak" : "Standard"} · ${money(cfg.tariff[p])}`);

    // comfort + essentials
    const cf = comfortRatio();
    setText("#comfortPct", Math.round(cf * 100) + "%");
    $("#comfortBar").style.width = cf * 100 + "%";
    $$("#essentials .chip").forEach((c) => {
      const a = app(c.dataset.key), h = hoursOn(a.key);
      const met = h >= a.target_hours - 1e-6;
      c.classList.toggle("ok", met);
      c.querySelector("em").textContent = a.target_hours >= 24 ? `${Math.floor(h)}h` : `${h.toFixed(1)}/${a.target_hours}h`;
    });

    // budget toasts
    if (S.phase === "play") {
      if (ratio >= 0.8 && !S.flags.w80) { S.flags.w80 = 1; toast("80% of your budget is gone", "warn"); }
      if (ratio >= 1 && !S.flags.w100) { S.flags.w100 = 1; toast("Over budget. Switch something off!", "bad"); }
    }
    drawChart(hour, dt);
  }

  /* ---------------- chart ---------------- */
  function drawChart(hour, dt) {
    const c = $("#chart"), dpr = window.devicePixelRatio || 1;
    const w = c.clientWidth, h = c.clientHeight;
    if (!w || !h) return;
    if (c.width !== Math.round(w * dpr) || c.height !== Math.round(h * dpr)) { c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); }
    const g = c.getContext("2d");
    g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, w, h);
    const L = 40, R = 50, T = 10, B = 24, pw = w - L - R, ph = h - T - B, bw = pw / 24;
    const lv = level();
    const per = []; let peakBar = 0, cum = 0; const cumPts = [];
    for (let i = 0; i < 24; i++) { const k = hourKwh(i); per.push(k); peakBar = Math.max(peakBar, k); }
    const total = per.reduce((a, b) => a + b, 0);
    S.ymax = lerp(S.ymax, Math.max(3, peakBar * 1.2), clamp(dt * 0.006, 0, 1));
    S.smax = lerp(S.smax, Math.max(lv.budget * 1.3, total * 1.1), clamp(dt * 0.006, 0, 1));
    const yB = (v) => T + ph - (v / S.ymax) * ph, yC = (v) => T + ph - (v / S.smax) * ph;

    // tariff bands
    for (let i = 0; i < 24; i++) {
      const p = period(i);
      g.fillStyle = p === "peak" ? "rgba(255,93,108,0.08)" : p === "offpeak" ? "rgba(61,220,151,0.06)" : "rgba(255,255,255,0.0)";
      g.fillRect(L + i * bw, T, bw, ph);
    }
    // grid + labels
    g.font = "11px 'Segoe UI', system-ui, sans-serif"; g.textBaseline = "middle";
    g.strokeStyle = "rgba(255,255,255,0.06)"; g.lineWidth = 1; g.fillStyle = "#7c88a6";
    for (let i = 0; i <= 3; i++) {
      const y = T + ph - (i / 3) * ph;
      g.beginPath(); g.moveTo(L, y); g.lineTo(L + pw, y); g.stroke();
      g.textAlign = "right"; g.fillText(((S.ymax * i) / 3).toFixed(1), L - 8, y);
    }
    g.textAlign = "center"; g.textBaseline = "top";
    for (let i = 0; i < 24; i += 3) g.fillText(pad(i), L + i * bw + bw / 2, T + ph + 8);
    g.textAlign = "left"; g.textBaseline = "alphabetic"; g.fillStyle = "#566286"; g.fillText("kWh/h", 2, T + 4);

    // stacked bars
    for (let i = 0; i < 24; i++) {
      let base = 0;
      const x = L + i * bw + bw * 0.16, w2 = bw * 0.68;
      cfg.appliances.forEach((a) => {
        const k = (a.watts / 1000) * S.min[a.key][i] / 60;
        if (k <= 0) return;
        const y1 = yB(base + k), y0 = yB(base);
        g.fillStyle = COLORS[a.key]; g.globalAlpha = 0.92;
        g.fillRect(x, y1, w2, Math.max(0.5, y0 - y1));
        base += k;
      });
      g.globalAlpha = 1;
    }
    // budget line (cumulative axis)
    g.setLineDash([5, 5]); g.strokeStyle = "rgba(255,184,77,0.85)"; g.lineWidth = 1.4;
    g.beginPath(); g.moveTo(L, yC(lv.budget)); g.lineTo(L + pw, yC(lv.budget)); g.stroke(); g.setLineDash([]);
    g.textAlign = "left"; g.textBaseline = "middle"; g.fillStyle = "#ffb84d";
    g.fillText(`${lv.budget.toFixed(0)} kWh`, L + pw + 6, yC(lv.budget));
    g.fillStyle = "#7c88a6"; g.fillText("0", L + pw + 6, yC(0));
    // cumulative line
    const nowH = Math.min(hour, 24);
    cumPts.push([L, yC(0)]);
    for (let i = 0; i < Math.floor(nowH); i++) { cum += per[i]; cumPts.push([L + (i + 1) * bw, yC(cum)]); }
    const cur = cum + (Math.floor(nowH) < 24 ? per[Math.floor(nowH)] : 0);
    cumPts.push([L + nowH * bw, yC(cur)]);
    const over = cur > lv.budget;
    const grad = g.createLinearGradient(0, T, 0, T + ph);
    grad.addColorStop(0, over ? "rgba(255,93,108,0.28)" : "rgba(76,201,240,0.26)"); grad.addColorStop(1, "rgba(76,201,240,0)");
    g.beginPath(); cumPts.forEach((p, i) => (i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])));
    g.lineTo(cumPts[cumPts.length - 1][0], T + ph); g.lineTo(L, T + ph); g.closePath(); g.fillStyle = grad; g.fill();
    g.beginPath(); cumPts.forEach((p, i) => (i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])));
    g.strokeStyle = over ? "#ff5d6c" : "#4cc9f0"; g.lineWidth = 2.4; g.lineJoin = "round"; g.stroke();
    const last = cumPts[cumPts.length - 1];
    g.beginPath(); g.arc(last[0], last[1], 4, 0, Math.PI * 2); g.fillStyle = over ? "#ff5d6c" : "#4cc9f0"; g.fill();
    // time cursor
    if (S.phase === "play" || S.phase === "done") {
      const x = L + nowH * bw;
      g.strokeStyle = "rgba(255,255,255,0.35)"; g.lineWidth = 1; g.beginPath(); g.moveTo(x, T); g.lineTo(x, T + ph); g.stroke();
    }
  }

  /* ---------------- results ---------------- */
  const MEDAL = { Gold: "#f5c542", Silver: "#c3cbd9", Bronze: "#d08a5b", "Keep trying": "#6f7b98" };

  function tipsFor(r) {
    const tips = [], lv = level(), tt = totals();
    const per = cfg.appliances.map((a) => ({ a, kwh: (a.watts / 1000) * hoursOn(a.key) })).sort((x, y) => y.kwh - x.kwh);
    if (tt.kwh > 0) tips.push(`<b>${per[0].a.name}</b> used ${Math.round((per[0].kwh / tt.kwh) * 100)}% of your energy (${per[0].kwh.toFixed(1)} kWh). It is the biggest lever you have.`);
    let peakKwh = 0;
    cfg.peak_hours.forEach((h) => (peakKwh += hourKwh(h)));
    if (peakKwh > 0.3) {
      const saved = peakKwh * (cfg.tariff.peak - cfg.tariff.offpeak);
      tips.push(`${peakKwh.toFixed(1)} kWh ran in the 17:00–22:00 peak. Moving flexible jobs like laundry, water heating and ironing to night would save about ${money(saved)}.`);
    }
    if (r.kwh > lv.budget) tips.push(`You went over budget by ${(r.kwh - lv.budget).toFixed(1)} kWh. Cutting the air conditioner by an hour saves ${(app("ac").watts / 1000).toFixed(1)} kWh.`);
    if (r.missing.length) tips.push(`Essentials fell short: ${r.missing.join(", ")}. Food safety and cooking come first.`);
    const unmet = cfg.appliances.filter((a) => !a.essential).map((a) => ({ a, gap: (1 - Math.min(hoursOn(a.key) / a.target_hours, 1)) * a.weight })).sort((x, y) => y.gap - x.gap)[0];
    if (unmet && unmet.gap > 0.5) tips.push(`The household wanted more time with the <b>${unmet.a.name.toLowerCase()}</b>. Look for a cheaper hour instead of skipping it.`);
    if (r.kwh <= lv.budget && !r.missing.length && r.comfort > 0.6) tips.push(`Well balanced: you stayed under budget and kept most comforts. That is what real energy saving looks like.`);
    return tips.slice(0, 4);
  }

  function showResult(r, verified) {
    const lv = level();
    const rows = [
      ["Base", r.base_pts, ""], ["Comfort", r.comfort_pts, ""], ["Budget", r.budget_pts, ""],
      ["Off-peak timing", r.timing_pts, ""], ["Missing essentials", -r.essential_pen, ""],
    ];
    const maxAbs = 500;
    const rowHtml = rows.map(([n, v]) => {
      const pct = clamp(Math.abs(v) / maxAbs, 0, 1) * 50;
      const style = v >= 0 ? `left:50%;width:${pct}%;background:var(--green)` : `right:50%;width:${pct}%;background:var(--red)`;
      return `<div class="br"><span>${n}</span><b class="${v >= 0 ? "pos" : "neg"}">${v >= 0 ? "+" : "−"}${Math.abs(Math.round(v))}</b><div class="track"><i style="${style}"></i></div></div>`;
    }).join("");
    const headline = { Gold: "Outstanding day.", Silver: "Strong day.", Bronze: "Solid effort.", "Keep trying": "Not quite there yet." }[r.rating];
    const sub = r.kwh <= lv.budget
      ? `You finished ${(lv.budget - r.kwh).toFixed(2)} kWh under the ${lv.budget.toFixed(0)} kWh budget.`
      : `You finished ${(r.kwh - lv.budget).toFixed(2)} kWh over the ${lv.budget.toFixed(0)} kWh budget.`;
    $("#resultPanel").innerHTML = `
      <div class="res-top">
        <div class="medal" style="--mc:${MEDAL[r.rating]}"><div><b id="scoreNum">${r.score}</b><span>${r.rating}</span></div></div>
        <div class="res-title"><div class="eyebrow">${S.level} · Day complete</div><h2>${headline}</h2><p>${sub}</p>
          <span class="verify ${verified ? "ok" : ""}">${verified ? "Scored by the Python game engine" : "Checking with the game engine…"}</span></div>
      </div>
      <div class="res-tiles">
        <div class="tile"><span>Energy consumed</span><b>${r.kwh.toFixed(2)}</b><em>kWh</em></div>
        <div class="tile"><span>CO₂ equivalent</span><b>${r.co2.toFixed(2)}</b><em>kg</em></div>
        <div class="tile"><span>Cost</span><b>${money(r.cost)}</b><em>time-of-use tariff</em></div>
        <div class="tile"><span>Comfort</span><b>${Math.round(r.comfort * 100)}%</b><em>of wanted hours</em></div>
      </div>
      <div class="res-cols">
        <div class="box"><div class="card-title">Score breakdown</div>${rowHtml}</div>
        <div class="box"><div class="card-title">What to try next</div><div class="tips">${tipsFor(r).map((t) => `<div class="tip">${t}</div>`).join("")}</div></div>
      </div>
      <div class="res-actions"><button class="btn primary big" id="againBtn">Play again</button></div>`;
    $("#againBtn").addEventListener("click", () => {
      resetSim(); S.phase = "menu"; $("#result").classList.add("hidden"); $("#menu").classList.remove("hidden");
      S.shown = {}; fitHeight();
    });
    $("#result").classList.remove("hidden");
    fitHeight();
  }

  window.__game = { S, evaluateLocal, get cfg() { return cfg; }, toggle, startDay };
})();
