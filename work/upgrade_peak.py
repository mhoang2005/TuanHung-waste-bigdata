from pathlib import Path
import json

root=Path(r'C:\Users\OS\Documents\Giáo Trình\bigdata')
p=root/'src/wasteflow/demand.py'
s=p.read_text(encoding='utf-8')
s=s.replace('def build_demand(cfg, city, scenario):', '''class DemandStream:
    """Repeatable demand source; retain at most one simulated day in memory."""
    def __init__(self, cfg, city, scenario):
        self.cfg, self.city, self.scenario = cfg, city, scenario

    def __iter__(self):
        return iter_demand(self.cfg, self.city, self.scenario)


def build_demand(cfg, city, scenario):
    return DemandStream(cfg, city, scenario)


def iter_demand(cfg, city, scenario):''')
s=s.replace('    inputs = []\n    for day in range(cfg["days"]):', '    index = 0\n    for day in range(cfg["days"]):\n        inputs = []')
a=s.index('    priority = '); b=s.index('\n\n\ndef demand_hash',a)
s=s[:a]+'''        priority = {"generation": 0, "deposit": 1, "public_deposit": 2}
        inputs.sort(key=lambda x: (x["minute"], priority[x["kind"]], x["point_id"], x.get("household_id") or "", x["waste_type"]))
        for row in inputs:
            row["input_id"] = stable_id(cfg["seed"], "demand", index, json.dumps(row, sort_keys=True))
            index += 1
            yield row
'''+s[b:]
p.write_text(s,encoding='utf-8')
p=root/'src/wasteflow/simulation.py';s=p.read_text(encoding='utf-8')
s=s.replace('        self.input_cursor = 0','        self.input_cursor = 0\n        self._demand_iter = iter(demand)\n        self._next_input = next(self._demand_iter, None)')
s=s.replace('        while self.input_cursor < len(self.demand) and self.demand[self.input_cursor]["minute"] <= self.minute:\n            row = self.demand[self.input_cursor]', '        while self._next_input is not None and self._next_input["minute"] <= self.minute:\n            row = self._next_input\n            self._next_input = next(self._demand_iter, None)')
p.write_text(s,encoding='utf-8')
cfg=json.loads((root/'config/city.json').read_text(encoding='utf-8'))
cfg.update(households=3600,vehicle_capacity_kg=3500,vehicles_per_type=2,loading_kg_per_minute=120)
for t in cfg['types'].values():t['capacity_l'] *= 5
(root/'config/city-peak.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=root/'compose.yaml';s=p.read_text(encoding='utf-8')
s=s.replace('"live", "--days"','"live", "--config", "${SIMULATION_CONFIG:-config/city-peak.json}", "--days"')
s=s.replace('${TICK_SLEEP_SECONDS:-0.35}','${TICK_SLEEP_SECONDS:-2.0}')
p.write_text(s,encoding='utf-8')
for name in ('.env','.env.example'):
 p=root/name
 if p.exists():
  s=p.read_text(encoding='utf-8-sig')
  import re
  s=re.sub(r'^TICK_SLEEP_SECONDS=.*$', 'TICK_SLEEP_SECONDS=2.0',s,flags=re.M)
  if 'SIMULATION_CONFIG=' not in s:s+='\nSIMULATION_CONFIG=config/city-peak.json\n'
  p.write_text(s,encoding='utf-8')
