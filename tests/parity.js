// Reads {cfg, level, cases:[minutes,...]} from stdin, prints one evaluation per case as JSON.
const Scoring = require("../frontend/scoring.js");
let raw = "";
process.stdin.on("data", (d) => (raw += d));
process.stdin.on("end", () => {
  const { cfg, level, cases } = JSON.parse(raw);
  console.log(JSON.stringify(cases.map((minutes) => Scoring.evaluate(cfg, level, minutes))));
});
