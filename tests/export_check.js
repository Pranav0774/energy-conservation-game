// Reads {store, appliances} from stdin and prints what the browser's exporter would give: {columns, csv, runs}.
const Exporter = require("../frontend/exporter.js");
let raw = "";
process.stdin.on("data", (d) => (raw += d));
process.stdin.on("end", () => {
  const { store, appliances } = JSON.parse(raw);
  const { csv, runs } = Exporter.toCsv(store, appliances);
  console.log(JSON.stringify({ columns: Exporter.columns(appliances), csv, runs }));
});
