import json
from pathlib import Path
from collections import defaultdict

path = Path(__file__).parent / "traces.jsonl"
stats = defaultdict(lambda: {"calls": 0, "cost": 0.0, "latency_sum": 0.0, "errors": 0})

with open(path, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        s = stats[ev["span_name"]]
        s["calls"] += 1
        s["latency_sum"] += ev["latency_s"]
        if ev["status"] == "error":
            s["errors"] += 1
        else:
            s["cost"] += ev["cost_usd"] or 0.0

print(f"{'span':<16} {'calls':>6} {'errors':>7} {'avg_latency_s':>14} {'total_cost_usd':>15}")
for key, s in stats.items():
    avg_latency = s["latency_sum"] / s["calls"]
    print(f"{key:<16} {s['calls']:>6} {s['errors']:>7} {avg_latency:>14.2f} {s['cost']:>15.5f}")
