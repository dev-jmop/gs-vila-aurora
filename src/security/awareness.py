"""Offline, consent-free phishing awareness simulation with imaginary identities.
No email is generated, delivered, or transmitted. No credential collection.
"""
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROSTER = [f"colaborador-ficticio-{i:02d}" for i in range(1, 13)]
OPENED = set(ROSTER[:7])
CLICKED = set(ROSTER[:3])
REPORTED = set(ROSTER[3:7])


def simulate(outdir: Path, now=None):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    now = now or datetime.now(timezone.utc)
    ts = now.isoformat()
    events=[]
    for identity in ROSTER:
        events.append({"timestamp": ts, "source": "phishing_simulation", "identity": identity, "event": "simulated_delivery", "scenario": "atualizacao-de-cadastro-ficticia"})
        if identity in OPENED:
            events.append({"timestamp": ts, "source": "phishing_simulation", "identity": identity, "event": "simulated_open", "scenario": "atualizacao-de-cadastro-ficticia"})
        if identity in CLICKED:
            events.append({"timestamp": ts, "source": "phishing_simulation", "identity": identity, "event": "simulated_click", "scenario": "atualizacao-de-cadastro-ficticia"})
        if identity in REPORTED:
            events.append({"timestamp": ts, "source": "phishing_simulation", "identity": identity, "event": "simulated_report", "scenario": "atualizacao-de-cadastro-ficticia"})
    with (outdir/'phishing_events.jsonl').open('w', encoding='utf-8') as f:
        for item in events: f.write(json.dumps(item, ensure_ascii=False, sort_keys=True)+'\n')
    counts=Counter(e['event'] for e in events)
    delivered=counts['simulated_delivery']
    metrics={
        "mode": "OFFLINE_SYNTHETIC_NOT_REAL_PEOPLE", "generated_at_utc": ts,
        "simulated_deliveries": delivered,
        "simulated_opens": counts['simulated_open'],
        "simulated_clicks": counts['simulated_click'],
        "simulated_reports": counts['simulated_report'],
        "simulated_open_rate_pct": round(100*counts['simulated_open']/delivered, 2),
        "simulated_click_rate_pct": round(100*counts['simulated_click']/delivered, 2),
        "simulated_report_rate_pct": round(100*counts['simulated_report']/delivered, 2),
        "credentials_collected": 0,
        "real_messages_sent": 0,
        "notes": "Cenario predefinido para exercicio e demonstracao, nao medicao de usuarios reais."
    }
    (outdir/'phishing_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (outdir/'phishing_metrics.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['metric','value']);w.writerows((k,v) for k,v in metrics.items() if not isinstance(v,(list,dict)))
    return metrics
