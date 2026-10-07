// Reads {cfg, level, days} from stdin and prints the tips Tips.build gives for each day.
const Scoring = require("../frontend/scoring.js");
const Tips = require("../frontend/tips.js");
let raw = "";
process.stdin.on("data", (d) => (raw += d));
process.stdin.on("end", () => {
  const { cfg, level, days } = JSON.parse(raw);
  console.log(JSON.stringify(days.map((minutes) => Tips.build(cfg, level, minutes, Scoring.evaluate(cfg, level, minutes)))));
});
