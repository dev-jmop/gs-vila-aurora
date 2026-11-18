"""Synthetic incident reconstruction. No actual incident is asserted."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from src.security.detector import read_jsonl, detect, parse_time
from src.security.evidence import create_manifest,verify_manifest

INCIDENT="INC-VA-0712"
SOURCES=("security_events.jsonl","phishing_events.jsonl","alerts.jsonl","detection_summary.json")

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def reconstruct(source, destination, collector="analista-forense-laboratorio"):
    source=Path(source); dest=Path(destination)
    if source.resolve()==dest.resolve(): raise ValueError("origem e destino devem diferir")
    if dest.exists() and any(dest.iterdir()): raise FileExistsError("Diretorio de caso nao esta vazio: preserve evidencias anteriores")
    if not all((source/name).is_file() for name in SOURCES): raise FileNotFoundError("Execute scripts/etapa2e_demo.py antes")
    if not verify_manifest(source): raise ValueError("Manifesto de origem nao confere. Nao prosseguir.")
    dest.mkdir(parents=True,exist_ok=True)
    raw=dest/'01_originais';raw.mkdir()
    for name in SOURCES: (raw/name).write_bytes((source/name).read_bytes())
    events=read_jsonl(raw/'security_events.jsonl')+read_jsonl(raw/'phishing_events.jsonl')
    alerts=read_jsonl(raw/'alerts.jsonl')
    # Ensure timeline is derived from source, not separately fabricated.
    events.sort(key=lambda e:parse_time(e['timestamp']))
    timeline=[]
    for ev in events:
        timeline.append({'timestamp_utc':parse_time(ev['timestamp']).isoformat(), 'event':ev['event'], 'identity':ev.get('identity','unknown'), 'source':ev.get('source','unknown'), 'simulation':ev.get('simulation',False)})
    with (dest/'02_timeline.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['timestamp_utc','event','identity','source','simulation']);w.writeheader();w.writerows(timeline)
    manifest=[{'filename':n,'source_sha256':sha256(source/n),'preserved_sha256':sha256(raw/n),'match':sha256(source/n)==sha256(raw/n)} for n in SOURCES]
    (dest/'03_cadeia_custodia.json').write_text(json.dumps({'incident_id':INCIDENT,'nature':'SIMULATED','collector':collector,'collected_at_utc':datetime.now(timezone.utc).isoformat(),'method':'copia byte a byte + SHA-256; originais preservados','artifacts':manifest,'limitation':'Hashes detectam modificacao, nao comprovam autenticidade ou posse exclusiva'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    rule_counts={key:sum(a['rule_id']==key for a in alerts) for key in sorted({a['rule_id'] for a in alerts})}
    report={'incident_id':INCIDENT,'classification':'SIMULACAO FORENSE / SEM INCIDENTE REAL','evidence_source':'Etapa 2E synthetic fixtures','event_count':len(events),'alerts_count':len(alerts),'alerts_by_rule':rule_counts,'first_event_utc':timeline[0]['timestamp_utc'] if timeline else None,'last_event_utc':timeline[-1]['timestamp_utc'] if timeline else None,'findings':['Falhas de login simuladas em janela de 5 minutos','Tentativa de uso de certificado revogado representada por evento TLS','Tentativa SQLi contra laboratorio sintetico','Evento MQTT de origem divergente','Interacoes simuladas em campanha de phishing'],'response_decisions':{'low_risk':'registrar alerta e orientar conscientizacao; nao altera acesso','high_risk':'proposta de isolamento/revogacao depende de aprovacao humana','automatic_real_actions':0},'limitations':['Nao foi realizada coleta de imagem forense de disco ou memoria','Nao ha prova de ataque real, autoria, IP de origem ou exfiltracao','Eventos gerados localmente para avaliacao academica']}
    (dest/'04_relatorio_INC-VA-0712.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (dest/'E4_relatorio_forense.md').write_text('# Relatorio forense — INC-VA-0712\n\n**Natureza:** simulacao academica; nao e um incidente real.\n\n## Escopo\nReconstrucao deterministica de eventos sinteticos produzidos na Etapa 2E.\n\n## Coleta e integridade\nForam copiados byte a byte os quatro artefatos listados em `03_cadeia_custodia.json`; os SHA-256 dos originais e copias conferem. O manifesto `sha256_manifest.json` protege os artefatos derivados contra alteracoes nao detectadas.\n\n## Cronologia\nConsulte `02_timeline.csv` (UTC). Total de eventos: **%s**. Total de alertas: **%s**.\n\n## Indicadores e achados\n- Falhas de login em curta janela, conforme VA-DET-01.\n- Falha de verificacao de certificado TLS, conforme VA-DET-02.\n- SQLi simulada, conforme VA-DET-03.\n- MQTT cross-site, conforme VA-DET-04.\n- Cliques de phishing ficticios, conforme VA-DET-05.\n\n## Contencao e resposta\nNao foi executada qualquer acao real de bloqueio, revogacao ou firewall. Acao de alto risco exige revisao e aprovacao humana.\n\n## Limitacoes\nSem imagem forense de disco/memoria; sem coleta de evidencia de incidente real; hashes nao conferem autenticidade por si so.\n\n## Referencias internas\n`01_originais/`, `02_timeline.csv`, `03_cadeia_custodia.json`, `04_relatorio_INC-VA-0712.json`, `sha256_manifest.json`.\n' % (len(events),len(alerts)),encoding='utf-8')
    create_manifest(dest)
    if not verify_manifest(dest): raise AssertionError('erro na verificacao de integridade')
    return report
