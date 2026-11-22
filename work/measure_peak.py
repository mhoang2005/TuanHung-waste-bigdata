import json
from collections import Counter
from datetime import timedelta
from wasteflow.util import ROOT, load_config, read_json, stable_id, write_json, parse_time
from wasteflow.city import make_city
from wasteflow.demand import build_demand
from wasteflow.simulation import Simulation
from wasteflow.quality import FaultInjector

cfg=load_config()
results=[]
for name, scenario in read_json(ROOT/'config/scenarios.json').items():
    city=make_city(cfg)
    demand=build_demand(cfg,city,scenario)
    rid=stable_id('wasteflow:1.2.0',json.dumps(cfg,sort_keys=True),name,'adaptive')
    sim=Simulation(cfg,city,demand,scenario,'adaptive',rid)
    faults=FaultInjector(cfg,rid)
    truth,transport=Counter(),Counter()
    breakdown={}
    while sim.minute < cfg['days']*1440:
        minute=sim.minute
        rows=sim.step()
        truth[minute]=len(rows)
        if len(rows)>=max(truth.values()):
            breakdown[minute]=dict(Counter(e['event_type'] for e in rows))
        for row in faults.inject(rows,minute):
            transport[row['transport_minute']]+=1
    for row in faults.drain():
        transport[row['transport_minute']]+=1
    peak=max(truth,key=truth.get)
    tpeak=max(transport,key=transport.get)
    peak_hour=max((sum(truth.get(m,0) for m in range(start,start+60,cfg['tick_minutes'])),start)
                  for start in range(cfg['days']*1440-50))
    results.append({'scenario':name,'days':cfg['days'],'households':cfg['households'],
        'truth_events':sum(truth.values()),'average_events_per_day':sum(truth.values())/cfg['days'],
        'peak_generated_per_tick':truth[peak],'peak_minute':peak,
        'peak_time':(parse_time(cfg['start'])+timedelta(minutes=peak)).isoformat(),
        'peak_event_types':breakdown[peak],
        'peak_rolling_hour_generated':peak_hour[0],
        'transport_events':sum(transport.values()),'peak_emitted_per_tick':transport[tpeak],
        'peak_emitted_minute':tpeak})
report={'tick_minutes':cfg['tick_minutes'],'seed':cfg['seed'],'policy':'adaptive',
        'unit':'simulation time; not wall-clock throughput','scenarios':results}
write_json(ROOT/'reports/peak-records-2026-11-02.json',report)
print(json.dumps(report,ensure_ascii=True,indent=2))
