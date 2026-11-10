// Builds submission/5_presentation.pptx from data/clean/summary_stats.json and docs/images.
// Needs: cd tools && npm install     Run: node tools/build_deck.js   (from the project root)
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const S = JSON.parse(fs.readFileSync(path.join(ROOT, "data/clean/summary_stats.json"), "utf8"));
const REPO = "github.com/Pranav0774/energy-conservation-game";
let team = [];
try {
  team = (JSON.parse(fs.readFileSync(path.join(ROOT, "docs/team.json"), "utf8")).team || []).filter((m) => (m.name || "").trim());
} catch (e) { /* no team file */ }

// ---- palette and type ----
const INK = "12201C", DEEP = "0B2A21", GREEN = "0B6E4F", MINT = "E8F1ED", AMBER = "F2A900", RED = "D55E00",
  TEAL = "009E73", MUTED = "5B6770", PAPER = "F6F9F7", WHITE = "FFFFFF", SOFT = "BFD8CC";
const HEAD = "Cambria", BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };
pres.title = "Smart Energy Conservation Game";
pres.author = team.map((m) => m.name).join(", ") || "Project team";

pres.defineSlideMaster({
  title: "TITLE", background: { color: DEEP },
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: WHITE },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9, h: 0.75, fontFace: HEAD, fontSize: 30, bold: true, color: INK, valign: "middle", align: "left", margin: 0 }, text: "" } }],
  slideNumber: { x: 9.1, y: 5.2, w: 0.5, h: 0.3, fontFace: BODY, fontSize: 10, color: MUTED, align: "right" },
});
pres.defineSlideMaster({ title: "END", background: { color: DEEP } });

const num = (x, d = 0) => Number(x).toFixed(d);
const M = S.strategy_medium, FULL = M.full_comfort, CUT = M.budget_cutter, PEAK = M.peak_aware;
const energyCutPct = 100 * (1 - CUT.energy_kwh / FULL.energy_kwh);
const comfortDrop = Math.round((FULL.comfort - CUT.comfort) * 100);
const costSavedMed = 100 * (1 - PEAK.cost / CUT.cost);
const SH = S.energy_share_pct;
const PVC = S.peak_vs_cutter;

const card = (slide, x, y, w, h, fill = MINT) =>
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.08, objectName: "card" });
const text = (slide, t, o) => slide.addText(t, { isTextBox: true, margin: 0, fontFace: BODY, color: INK, valign: "top", ...o });
const circle = (slide, n, x, y, d = 0.4, fill = GREEN) => {
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: "step" });
  slide.addText(String(n), { isTextBox: true, x, y, w: d, h: d, align: "center", valign: "middle", fontFace: BODY, fontSize: 14, bold: true, color: WHITE, margin: 0 });
};
const img = (name) => path.join(ROOT, "docs/images", name);

// ======== Title ========
{
  const s = pres.addSlide({ masterName: "TITLE" });
  text(s, "Smart Energy Conservation Game", { x: 0.6, y: 1.25, w: 4.9, h: 1.6, fontFace: HEAD, fontSize: 38, bold: true, color: WHITE, valign: "top" });
  text(s, "Plan one household day against a fixed energy budget, in real time", { x: 0.6, y: 3.0, w: 4.6, h: 0.8, fontSize: 18, color: SOFT });
  text(s, ["Project 73", ...(team.length ? [team.map((m) => m.name).join(" · ")] : []), REPO].join("\n"), { x: 0.6, y: 4.35, w: 5, h: 0.9, fontSize: 12, color: SOFT, valign: "bottom" });
  s.addImage({ path: img("game_play.png"), x: 5.65, y: 1.4, w: 3.8, h: 2.375, altText: "Screenshot of the game: a house with appliances, a budget ring and live meters", shadow: { type: "outer", color: "000000", opacity: 0.4, blur: 12, offset: 4, angle: 90 } });
  s.addNotes("This is the Smart Energy Conservation Game. The player runs one household day against a fixed energy budget and sees energy, CO2, cost and score as it happens. The screenshot shows a heatwave day at 19:50: the budget ring has gone red because the household is over budget.");
}

// ======== 1 Problem ========
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("People see a bill, not the choices behind it", { placeholder: "title" });
  text(s, "A household meets its electricity use once a month, as a bill. Nobody sees what one hour of air conditioning cost while there is still time to change it, and it is hard to tell which appliances matter without measuring.", { x: 0.5, y: 1.3, w: 4.2, h: 1.9, fontSize: 16 });
  card(s, 0.5, 3.45, 4.2, 1.55, PAPER);
  text(s, "What we built", { x: 0.7, y: 3.55, w: 3.8, h: 0.35, fontSize: 14, bold: true, color: GREEN });
  text(s, "A four-minute game with a fixed energy budget, ten appliances, three levels and five random events. Live energy, CO₂, cost, comfort and score.", { x: 0.7, y: 3.92, w: 3.8, h: 1.05, fontSize: 14 });
  text(s, "Four questions for the data", { x: 5.1, y: 1.3, w: 4.4, h: 0.35, fontSize: 14, bold: true, color: GREEN });
  const qs = ["Which appliances use most of the day, and are the game's power ratings realistic?", "How much comfort does a household give up to meet a budget?", "How much does moving use to cheaper hours save?", "Do the answers survive if the game's numbers are wrong?"];
  qs.forEach((q, i) => {
    const y = 1.75 + i * 0.82;
    circle(s, i + 1, 5.1, y + 0.05, 0.4);
    text(s, q, { x: 5.65, y, w: 3.85, h: 0.7, fontSize: 14, valign: "middle" });
  });
  s.addNotes("The problem is feedback. A bill arrives weeks after the choices behind it. The game gives that feedback in four minutes. The brief asks for a budget, appliances to operate, a score, energy consumed, CO2 equivalent and cost, and the game shows all of them live. We then used data to answer four questions.");
}

// ======== 2 Data and method ========
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Real sources, cleaned data, simulated players", { placeholder: "title" });
  const box = (x, y, w, big, small, fill = MINT) => {
    card(s, x, y, w, 1.05, fill);
    text(s, big, { x: x + 0.12, y: y + 0.1, w: w - 0.24, h: 0.4, fontSize: 16, bold: true, color: GREEN });
    text(s, small, { x: x + 0.12, y: y + 0.5, w: w - 0.24, h: 0.5, fontSize: 12 });
  };
  const arrow = (x, y) => s.addText("→", { isTextBox: true, x, y, w: 0.3, h: 0.4, fontSize: 20, color: MUTED, align: "center", margin: 0, fontFace: BODY });
  const D = S.dataset, A = S.appliances;
  text(s, "Appliance power data", { x: 0.5, y: 1.2, w: 5, h: 0.3, fontSize: 14, bold: true });
  box(0.5, 1.55, 2.6, `${D.raw_appliance_sources} web pages`, `${D.raw_appliance_rows} rows, each with its URL`);
  arrow(3.12, 1.9);
  box(3.45, 1.55, 2.9, "Cleaned", `${D.appliance_log["duplicate rows removed"]} duplicates, ${D.appliance_log["annual kWh figures converted to average watts"]} unit conversion`);
  arrow(6.37, 1.9);
  box(6.7, 1.55, 2.8, `${A.within} of ${A.total} inside`, "published ranges; cooktop, heater, iron below", "FCEFD2");
  text(s, "Play logs", { x: 0.5, y: 2.85, w: 5, h: 0.3, fontSize: 14, bold: true });
  box(0.5, 3.2, 2.0, "6 strategies", "scripted households");
  arrow(2.52, 3.55);
  box(2.85, 3.2, 2.0, `${S.n_simulated} days`, "all levels, all events");
  arrow(4.87, 3.55);
  box(5.2, 3.2, 2.0, "6 rules", `${D.playlog_log["raw rows read"] - D.playlog_log["clean rows kept"]} rows removed`);
  arrow(7.22, 3.55);
  box(7.55, 3.2, 1.95, "Analysis", "6 graphs, plus a sensitivity test");
  card(s, 0.5, 4.5, 9, 0.6, "FCEFD2");
  text(s, `No human play data yet (${S.n_human} runs). Every finding that follows comes from simulated players. Export and cleaning for real runs are built and tested.`, { x: 0.7, y: 4.5, w: 8.6, h: 0.6, fontSize: 14, bold: true, valign: "middle" });
  s.addNotes("Two datasets. The appliance table has 33 rows read from three web pages, cleaned, and compared with the values the game uses: seven of ten are inside the published ranges, and three are below. The play logs are 612 days played by six scripted strategies, because no human data exists yet. The cleaning rules removed nothing because simulated rows are generated clean; we tested them with deliberately broken rows and with a real browser export. Say clearly that the findings are about the game's rules, not about people.");
}

// ======== 3 Energy findings ========
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("The air conditioner decides the day", { placeholder: "title" });
  const order = Object.entries(SH).sort((a, b) => b[1] - a[1]);
  const names = { fridge: "Refrigerator", cooktop: "Cooktop", ac: "Air conditioner", fan: "Ceiling fan", lights: "Lights", tv: "Television", computer: "Computer", washer: "Washing machine", heater: "Water heater", iron: "Iron" };
  s.addChart(pres.charts.BAR, [{ name: "Share of a full-comfort day's energy (%)", labels: order.map((o) => names[o[0]]), values: order.map((o) => o[1]) }], {
    x: 0.4, y: 1.15, w: 5.4, h: 3.85, barDir: "bar", catAxisOrientation: "maxMin", chartColors: order.map((o) => (o[0] === "ac" ? AMBER : "7FB5A0")),
    showValue: true, dataLabelFormatCode: '0"%"', dataLabelPosition: "outEnd", dataLabelFontSize: 11, dataLabelColor: INK, dataLabelFontFace: BODY,
    catAxisLabelColor: INK, catAxisLabelFontSize: 11, catAxisLabelFontFace: BODY, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: false, showTitle: true, title: "Share of a full-comfort day's energy", titleFontSize: 12, titleColor: MUTED, titleFontFace: BODY, barGapWidthPct: 45,
  });
  const stat = (y, big, small) => {
    card(s, 6.1, y, 3.4, 1.18, PAPER);
    text(s, big, { x: 6.3, y: y + 0.1, w: 3.0, h: 0.5, fontFace: HEAD, fontSize: 28, bold: true, color: GREEN, valign: "middle" });
    text(s, small, { x: 6.3, y: y + 0.62, w: 3.0, h: 0.5, fontSize: 12 });
  };
  stat(1.25, `${num(SH.ac)}%`, "of a full-comfort day is the air conditioner");
  stat(2.55, `−${num(energyCutPct)}%`, `energy to meet a 10 kWh budget, for ${comfortDrop} points less comfort`);
  stat(3.85, `${num(S.over_budget_pct_by_strategy.casual_random)}%`, "of unplanned days go over the budget");
  text(s, "Simulated players, Medium level", { x: 6.1, y: 5.1, w: 3.4, h: 0.25, fontSize: 10, color: MUTED });
  s.addNotes(`The air conditioner is ${num(SH.ac)} percent of a full-comfort day. With the cooktop, water heater and iron, four appliances make about 82 percent. A full-comfort day uses ${num(FULL.energy_kwh, 1)} kilowatt-hours; meeting the 10 kWh budget cuts ${num(energyCutPct)} percent of that and keeps ${num(CUT.comfort * 100)} percent of the comfort the household wanted. Casual play with no plan goes over budget in ${num(S.over_budget_pct_by_strategy.casual_random)} percent of runs. Most of the energy saving here comes from the budget forcing cuts. These are simulated players.`);
}

// ======== 4 Timing ========
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Timing saves money at no cost to comfort", { placeholder: "title" });
  const hours = Array.from({ length: 24 }, (_, h) => String(h).padStart(2, "0"));
  const H = S.hourly_medium;
  s.addChart(pres.charts.LINE, [
    { name: "Full comfort", labels: hours, values: H.full_comfort },
    { name: "Budget cutter", labels: hours, values: H.budget_cutter },
    { name: "Peak-aware", labels: hours, values: H.peak_aware },
  ], {
    x: 0.4, y: 1.15, w: 5.6, h: 3.85, chartColors: [RED, AMBER, TEAL], lineSize: 3, lineDataSymbol: "none",
    showLegend: true, legendPos: "b", legendFontSize: 11, legendColor: INK, legendFontFace: BODY,
    catAxisLabelColor: INK, catAxisLabelFontSize: 10, catAxisLabelFontFace: BODY, valAxisLabelColor: INK, valAxisLabelFontSize: 10, valAxisLabelFontFace: BODY,
    valGridLine: { color: "E3E8E6", size: 0.5 }, catGridLine: { style: "none" }, catAxisLabelFrequency: 2,
    showTitle: true, title: "Mean energy per hour on a Medium day (kWh)", titleFontSize: 12, titleColor: MUTED, titleFontFace: BODY,
    showValAxisTitle: false,
  });
  const stat = (y, big, small) => {
    card(s, 6.3, y, 3.2, 1.18, PAPER);
    text(s, big, { x: 6.5, y: y + 0.1, w: 2.8, h: 0.5, fontFace: HEAD, fontSize: 26, bold: true, color: GREEN, valign: "middle" });
    text(s, small, { x: 6.5, y: y + 0.62, w: 2.8, h: 0.5, fontSize: 12 });
  };
  stat(1.25, `$${num(CUT.cost, 2)} → $${num(PEAK.cost, 2)}`, `same energy, same comfort: ${num(costSavedMed)}% cheaper`);
  stat(2.55, `${num(PVC.cost_saved_pct_mean, 1)}%`, `mean saving over ${PVC.n_pairs} paired runs (95% interval ${num(PVC.ci95[0])} to ${num(PVC.ci95[1])})`);
  stat(3.85, `${num(CUT.peak_share * 100)}% → ${num(PEAK.peak_share * 100)}%`, "of energy used at peak price");
  text(s, "Peak price runs 17:00 to 22:00; off-peak 22:00 to 06:00.", { x: 0.5, y: 5.08, w: 5.4, h: 0.25, fontSize: 10, color: MUTED });
  text(s, "CO₂ does not change: the model uses one emission factor for every hour.", { x: 6.3, y: 5.1, w: 3.2, h: 0.25, fontSize: 10, color: MUTED });
  s.addNotes(`Both strategies use the same energy and give the same comfort. The budget cutter keeps its habits and uses power in the evening peak. The peak-aware strategy spreads flexible jobs, like the water heater and iron, across the cheap night hours. On a Medium day that is ${num(costSavedMed)} percent cheaper. Across ${PVC.n_pairs} paired runs the mean saving is ${num(PVC.cost_saved_pct_mean, 1)} percent. Be honest about the limit: carbon does not change here because the model uses one emission factor for every hour.`);
}

// ======== 5 Solution and limits ========
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("A game and four habits", { placeholder: "title" });
  s.addImage({ path: img("game_results.png"), x: 0.5, y: 1.25, w: 3.7, h: 2.19, altText: "Results screen of the game: a Gold medal with score 753, energy, CO2, cost and comfort", shadow: { type: "outer", color: "000000", opacity: 0.25, blur: 8, offset: 3, angle: 90 } });
  text(s, "At the end of a day: score, breakdown, tips from your own day, and a comparison with your last run.", { x: 0.5, y: 3.65, w: 3.7, h: 0.75, fontSize: 12, color: MUTED });
  const habits = [`Decide the air conditioner first (${num(SH.ac)}% of the day)`, `Move the water heater and iron to the night (${num(SH.heater + SH.iron)}%)`, `Plan the cooktop around meals (${num(SH.cooktop)}%)`, "Leave the small loads until last"];
  habits.forEach((h, i) => {
    const y = 1.25 + i * 0.62;
    circle(s, i + 1, 4.6, y + 0.05, 0.4);
    text(s, h, { x: 5.15, y, w: 4.35, h: 0.5, fontSize: 14, valign: "middle" });
  });
  text(s, "In a classroom: four-minute rounds, compare scores, export the runs and analyse what a class does.", { x: 4.6, y: 3.8, w: 4.9, h: 0.6, fontSize: 14, bold: true, color: GREEN });
  card(s, 0.5, 4.5, 9, 0.65, "FCEFD2");
  text(s, "Limits: simulated players only. Three appliance values are below published ranges (the relative results held when we tested this). The 0.445 kg/kWh emission factor is still to be confirmed against the IEA page.", { x: 0.7, y: 4.5, w: 8.6, h: 0.65, fontSize: 12, valign: "middle" });
  s.addNotes("The solution is the game plus the habits the data points to, in order of effect. The air conditioner first, then the water heater and iron moved to night, then plan the cooktop around meals. In class, students play a four-minute round and compare. A teacher can export the runs and see what the class really does. Finish with the limits: no human data yet, three appliance values below published ranges, and an emission factor we still need to confirm. Next step is to collect at least twenty real runs.");
}

// ======== Thanks ========
{
  const s = pres.addSlide({ masterName: "END" });
  text(s, "Thank you", { x: 0.6, y: 1.5, w: 8.8, h: 1.2, fontFace: HEAD, fontSize: 48, bold: true, color: WHITE });
  text(s, "Questions?", { x: 0.6, y: 2.7, w: 8.8, h: 0.6, fontSize: 24, color: SOFT });
  text(s, `Code, data and report: ${REPO}\nRun the game: python -m streamlit run app.py`, { x: 0.6, y: 4.1, w: 8.8, h: 0.9, fontSize: 14, color: SOFT, valign: "bottom" });
  s.addNotes("Offer to run the game live. The command is python -m streamlit run app.py.");
}

fs.mkdirSync(path.join(ROOT, "submission"), { recursive: true });
pres.writeFile({ fileName: path.join(ROOT, "submission/5_presentation.pptx") }).then((f) => console.log("wrote", f));
