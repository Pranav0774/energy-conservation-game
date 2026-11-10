"use strict";
/* Turns the runs saved in the browser into a CSV (the "raw play log" dataset).
 * Pure functions so the column layout can be tested in Node against the Python cleaning script
 * (tests/test_data_pipeline.py). Anonymous: a random player id, no names or emails.
 */
(function (root) {
  const pad2 = (n) => String(n).padStart(2, "0");

  function columns(appliances) {
    return [
      "source", "player_id", "run_id", "timestamp_utc", "level", "event", "budget_kwh", "par", "score", "rating",
      "energy_kwh", "co2_kg", "cost", "comfort", "offpeak_share", "peak_share", "missing_essentials",
      ...appliances.map((a) => "hrs_" + a.key),
      ...Array.from({ length: 24 }, (_, h) => "kwh_h" + pad2(h)),
    ];
  }

  function esc(v) {
    if (v === null || v === undefined) return "";
    const s = String(v);
    return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  /** `store` is the object kept in localStorage: { _pid, Easy: {runs:[...]}, Medium: ..., Hard: ... }. */
  function toCsv(store, appliances) {
    const cols = columns(appliances);
    const lines = [cols.join(",")];
    let n = 0;
    for (const level of Object.keys(store || {})) {
      if (level.startsWith("_")) continue;
      for (const r of (store[level] || {}).runs || []) {
        const row = {
          source: "browser_player", player_id: store._pid || "", run_id: r.id || "",
          timestamp_utc: r.ts ? new Date(r.ts).toISOString() : "", level, event: r.event || "none",
          budget_kwh: r.budget, par: r.par, score: r.score, rating: r.rating, energy_kwh: r.kwh, co2_kg: r.co2,
          cost: r.cost, comfort: r.comfort, offpeak_share: r.off, peak_share: r.peak, missing_essentials: r.missing,
        };
        for (const a of appliances) row["hrs_" + a.key] = r.hrs ? r.hrs[a.key] : "";
        for (let h = 0; h < 24; h++) row["kwh_h" + pad2(h)] = r.kwh_h ? r.kwh_h[h] : "";
        lines.push(cols.map((c) => esc(row[c])).join(","));
        n++;
      }
    }
    return { csv: lines.join("\n") + "\n", runs: n };
  }

  const api = { columns, toCsv };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Exporter = api;
})(typeof window !== "undefined" ? window : globalThis);
