"use strict";
/* Personalised end-of-day tips. Pure functions (no DOM) so they can be unit-tested in Node.
 * Every "what if" number is computed by re-scoring a modified copy of the player's day with Scoring.evaluate.
 */
(function (root) {
  const Scoring = typeof require !== "undefined" && typeof module !== "undefined" ? require("./scoring.js") : root.Scoring;

  // Verified facts for the learning panel (sources in docs/research.md).
  const FACTS = [
    { text: "LED bulbs use at least 75% less energy than incandescent bulbs and can last up to 25 times longer.", src: "U.S. Department of Energy" },
    { text: "Devices left on standby can account for roughly 5–10% of a home's electricity use.", src: "U.S. Department of Energy" },
    { text: "A typical passenger car emits about 400 g of CO₂ per mile driven, about 250 g per km.", src: "U.S. EPA" },
    { text: "Electricity is cleanest and cheapest when demand is low. Shifting flexible jobs like laundry to off-peak hours helps the grid as well as your bill.", src: "Time-of-use tariffs" },
  ];
  const KG_PER_KM_CAR = 0.4 / 1.609; // EPA: ~400 g CO2 per mile

  const clone = (m) => Object.fromEntries(Object.entries(m).map(([k, v]) => [k, v.slice()]));
  const money = (cfg, v) => cfg.currency + v.toFixed(2);
  const kwhOf = (a, minutes) => (a.watts / 1000) * minutes.reduce((s, x) => s + x, 0) / 60;

  /** Remove up to `mins` minutes of an appliance, taking from its busiest hours first. */
  function trimMinutes(minutes, key, mins) {
    const m = clone(minutes), row = m[key];
    let left = mins;
    const order = row.map((v, h) => [v, h]).sort((a, b) => b[0] - a[0]);
    for (const [, h] of order) {
      const cut = Math.min(row[h], left);
      row[h] -= cut; left -= cut;
      if (left <= 0) break;
    }
    return m;
  }

  /** Move all of an appliance's peak-hour minutes to hour 02:00-03:00 (off-peak) without exceeding 60 min. */
  function shiftPeakToNight(cfg, minutes, key) {
    const m = clone(minutes), row = m[key];
    let moved = 0;
    for (const h of cfg.peak_hours) { moved += row[h]; row[h] = 0; }
    for (const h of [2, 3, 4, 1, 0, 23, 22, 5]) {
      const room = 60 - row[h], add = Math.min(room, moved);
      row[h] += add; moved -= add;
      if (moved <= 0) break;
    }
    return m;
  }

  function build(cfg, level, minutes, r) {
    const tips = [];
    const sc = (m) => Scoring.evaluate(cfg, level, m).score;
    const apps = cfg.appliances;
    const per = apps.map((a) => ({ a, kwh: kwhOf(a, minutes[a.key]) })).sort((x, y) => y.kwh - x.kwh);
    const optional = per.filter((p) => !p.a.essential && p.kwh > 0);

    if (r.missing.length) {
      tips.push(`Essentials fell short: <b>${r.missing.join(", ")}</b>. Food safety and cooking come first, and each one costs you ${cfg.scoring.essential_penalty} points.`);
    }

    if (r.kwh > level.budget && optional.length) {
      const big = optional[0];
      const cut = trimMinutes(minutes, big.a.key, 60);
      const saved = big.kwh - kwhOf(big.a, cut[big.a.key]);
      tips.push(`You went over budget by <b>${(r.kwh - level.budget).toFixed(1)} kWh</b>. Running the ${big.a.name.toLowerCase()} one hour less would have saved ${saved.toFixed(1)} kWh and gained about ${Math.max(0, sc(cut) - r.score)} points.`);
    }

    // Biggest peak-hour user: what if its peak use moved to the night?
    const peakUse = apps.map((a) => ({ a, kwh: (a.watts / 1000) * cfg.peak_hours.reduce((s, h) => s + minutes[a.key][h], 0) / 60 }))
      .filter((p) => !p.a.essential).sort((x, y) => y.kwh - x.kwh)[0];
    if (peakUse && peakUse.kwh >= 0.3) {
      const moved = shiftPeakToNight(cfg, minutes, peakUse.a.key);
      const before = Scoring.totals(cfg, minutes).cost, after = Scoring.totals(cfg, moved).cost;
      tips.push(`The <b>${peakUse.a.name.toLowerCase()}</b> ran ${peakUse.kwh.toFixed(1)} kWh in the 17:00–22:00 peak. Moving that to the night would have saved ${money(cfg, before - after)} and gained ${Math.max(0, sc(moved) - r.score)} points.`);
    }

    // Lights on in daylight
    const dayLightMins = [9, 10, 11, 12, 13, 14, 15].reduce((s, h) => s + (minutes.lights ? minutes.lights[h] : 0), 0);
    if (dayLightMins >= 30) {
      tips.push(`The lights were on for <b>${(dayLightMins / 60).toFixed(1)} h</b> in full daylight (09:00–16:00). Open the curtains instead.`);
    }

    // Comfort left on the table while budget remained
    if (r.kwh < level.budget) {
      const room = level.budget - r.kwh;
      const unmet = apps.filter((a) => !a.essential).map((a) => {
        const h = minutes[a.key].reduce((s, x) => s + x, 0) / 60;
        return { a, gap: (a.target_hours - Math.min(h, a.target_hours)) * a.weight, hours: a.target_hours - h };
      }).filter((u) => u.hours >= 1).sort((x, y) => y.gap - x.gap)[0];
      if (unmet && (unmet.a.watts / 1000) <= room) {
        tips.push(`You finished ${room.toFixed(1)} kWh under budget but left the <b>${unmet.a.name.toLowerCase()}</b> ${unmet.hours.toFixed(0)} h short of what the household wanted. One more hour costs only ${(unmet.a.watts / 1000).toFixed(2)} kWh.`);
      }
    }

    if (per[0] && per[0].kwh > 0 && r.kwh > 0) {
      tips.push(`<b>${per[0].a.name}</b> used ${Math.round((per[0].kwh / r.kwh) * 100)}% of your energy (${per[0].kwh.toFixed(1)} kWh). The biggest appliance is usually the biggest lever.`);
    }

    if (r.kwh <= level.budget && !r.missing.length && r.comfort > 0.6) {
      tips.unshift("Well balanced: you stayed under budget and kept most comforts. That is what real energy saving looks like.");
    }
    return tips.slice(0, 4);
  }

  /** CO2 shown as distance driven plus a yearly view, for the "Why it matters" panel. */
  function impact(co2kg) {
    return { km: co2kg / KG_PER_KM_CAR, yearKg: co2kg * 365 };
  }

  const api = { FACTS, build, impact, trimMinutes, shiftPeakToNight };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Tips = api;
})(typeof window !== "undefined" ? window : globalThis);
