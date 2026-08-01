const source = "../data/nhs-gpad/apr-2026-national-daily-v1/daily_appointments.csv";
const trainingEnd = "2026-04-16";
let rows = [];
const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
function csv(text) { const [header, ...lines] = text.trim().split("\n"); const keys = header.split(","); return lines.map(line => Object.fromEntries(keys.map((key, i) => [key, line.split(",")[i]]))); }
function weekday(date) { return new Date(`${date}T00:00:00Z`).getUTCDay(); }
function run(capacity) {
  const training = rows.filter(row => row.service_date <= trainingEnd); const evaluation = rows.filter(row => row.service_date > trainingEnd);
  const baseline = new Map();
  for (const row of training) { const key = weekday(row.service_date); const item = baseline.get(key) || { volume: [], dna: [] }; item.volume.push(+row.recorded_appointments); item.dna.push(+row.dna_appointments / (+row.attended_appointments + +row.dna_appointments)); baseline.set(key, item); }
  const signals = evaluation.map(row => { const item = baseline.get(weekday(row.service_date)); const forecast = item.volume.reduce((a,b)=>a+b,0) / item.volume.length; const dna = item.dna.reduce((a,b)=>a+b,0) / item.dna.length; const gap = forecast - capacity; return { date: row.service_date, forecast, dna, gap, status: gap > 0 ? "Review shortfall" : "Capacity sufficient" }; });
  document.querySelector("#capacity-summary").textContent = number.format(capacity); document.querySelector("#risk-days").textContent = `${signals.filter(s=>s.gap>0).length} of ${signals.length}`; const peak = Math.max(...signals.map(s=>s.gap)); document.querySelector("#peak-gap").textContent = `${peak >= 0 ? "+" : ""}${number.format(peak)}`;
  document.querySelector("#ledger").innerHTML = signals.map(s => `<tr><td>${s.date}</td><td>${number.format(s.forecast)}</td><td>${(s.dna*100).toFixed(1)}%</td><td class="${s.gap>0?"risk":"good"}">${s.gap>=0?"+":""}${number.format(s.gap)}</td><td><span class="status ${s.gap>0?"risk":"good"}">${s.status}</span></td></tr>`).join(""); document.querySelector("table").hidden = false;
}
fetch(source).then(response => { if (!response.ok) throw new Error("fixture unavailable"); return response.text(); }).then(text => { rows = csv(text); document.querySelector("#loading").hidden = true; run(+document.querySelector("#capacity").value); }).catch(() => { document.querySelector("#loading").textContent = "Unable to load the approved public fixture. Serve this folder from the repository root."; });
document.querySelector("#scenario").addEventListener("submit", event => { event.preventDefault(); const capacity = +document.querySelector("#capacity").value; const error = document.querySelector("#input-error"); if (!Number.isInteger(capacity) || capacity < 1) { error.textContent = "Enter a positive whole-number capacity scenario."; return; } error.textContent = ""; run(capacity); });
