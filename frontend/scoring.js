"use strict";
/* Pure scoring functions shared by the game UI and by the Node parity test (tests/test_frontend_parity.py).
 * They mirror game/engine.py. `minutes` maps an appliance key to 24 numbers: minutes it ran in each hour.
 */
(function (root) {
  const EPS = 1e-6;
  const periodOf = (cfg, h) => (cfg.peak_hours.includes(h) ? "peak" : cfg.offpeak_hours.includes(h) ? "offpeak" : "standard");
  const hoursOn = (minutes, key) => minutes[key].reduce((a, b) => a + b, 0) / 60;
  const hourKwh = (cfg, minutes, h) => cfg.appliances.reduce((s, a) => s + (a.watts / 1000) * minutes[a.key][h] / 60, 0);

  function totals(cfg, minutes) {
    let kwh = 0, cost = 0;
    for (let h = 0; h < 24; h++) {
      const k = hourKwh(cfg, minutes, h);
      kwh += k;
      cost += k * cfg.tariff[periodOf(cfg, h)];
    }
    return { kwh, cost, co2: kwh * cfg.co2 };
  }

  function comfort(cfg, minutes) {
    const optional = cfg.appliances.filter((a) => !a.essential);
    const total = optional.reduce((s, a) => s + a.weight, 0);
    const met = optional.reduce((s, a) => s + a.weight * Math.min(hoursOn(minutes, a.key), a.target_hours) / a.target_hours, 0);
    return total ? met / total : 0;
  }

  function missingEssentials(cfg, minutes) {
    return cfg.appliances.filter((a) => a.essential && hoursOn(minutes, a.key) < a.target_hours - EPS);
  }

  function evaluate(cfg, level, minutes) {
    const sc = cfg.scoring, tt = totals(cfg, minutes), cf = comfort(cfg, minutes), miss = missingEssentials(cfg, minutes);
    let off = 0, peak = 0;
    for (let h = 0; h < 24; h++) {
      const k = hourKwh(cfg, minutes, h);
      if (cfg.offpeak_hours.includes(h)) off += k;
      if (cfg.peak_hours.includes(h)) peak += k;
    }
    if (tt.kwh > 0) { off /= tt.kwh; peak /= tt.kwh; }
    const comfort_pts = sc.comfort_max * cf;
    const budget_pts = tt.kwh <= level.budget
      ? (sc.budget_bonus_max * (level.budget - tt.kwh)) / level.budget
      : (-sc.over_penalty * (tt.kwh - level.budget)) / level.budget;
    const timing_pts = sc.timing_max * (off - peak);
    const essential_pen = sc.essential_penalty * miss.length;
    const score = Math.max(0, Math.round(sc.base + comfort_pts + budget_pts + timing_pts - essential_pen));
    let rating = "Keep trying";
    for (const [name, f] of Object.entries(sc.rating_fractions)) {
      if (score >= f * level.par) { rating = name; break; }
    }
    return {
      kwh: tt.kwh, co2: tt.co2, cost: tt.cost, budget_kwh: level.budget, comfort: cf, missing: miss.map((a) => a.name),
      base_pts: sc.base, comfort_pts, budget_pts, timing_pts, essential_pen, score, rating,
    };
  }

  const api = { periodOf, hoursOn, hourKwh, totals, comfort, missingEssentials, evaluate };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Scoring = api;
})(typeof window !== "undefined" ? window : globalThis);
