#!/usr/bin/env python3
"""RT-22: amostra observada de recursos e disponibilidade, sem alterar serviços.

Energia calculada somente se o operador informar potência medida ou assumida.
MTTD/MTTR calculados somente com timestamps explícitos e verificados.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.security.detector import parse_time
from src.security.evidence import create_manifest, verify_manifest


def run(args, timeout=15):
    try:
        p=subprocess.run(args,text=True,capture_output=True,timeout=timeout,check=False)
        return p.returncode,p.stdout.strip(),p.stderr.strip()[:300]
    except (subprocess.TimeoutExpired,OSError) as exc:
        return 127,'',str(exc)


def number_with_unit(s):
    match=re.search(r'([\d.]+)\s*([a-zA-Z]+)',s.strip())
    if not match:return None
    val=float(match.group(1));unit=match.group(2)
    scale={'B':1,'kB':1e3,'KB':1e3,'MB':1e6,'GB':1e9,'TB':1e12,
           'KiB':1024,'MiB':1024**2,'GiB':1024**3,'TiB':1024**4}
    return val*scale[unit] if unit in scale else None


def parse_stats(blob):
    raw=json.loads(blob.strip().splitlines()[-1])
    mem=raw.get('MemUsage','')
    net=raw.get('NetIO','')
    cpu=raw.get('CPUPerc','').strip().rstrip('%')
    return {'cpu_pct':float(cpu) if cpu else None,
            'memory_bytes':number_with_unit(mem.split('/')[0]) if '/' in mem else None,
            'network_rx_bytes_total':number_with_unit(net.split('/')[0]) if '/' in net else None,
            'network_tx_bytes_total':number_with_unit(net.split('/')[1]) if '/' in net else None}


def time_metrics(fault, detected, recovered):
    vals=[parse_time(v) for v in (fault,detected,recovered)]
    if vals[0]>vals[1] or vals[1]>vals[2]:
        raise ValueError('timestamp order: fault <= detected <= recovered')
    return {'mttd_seconds_observed':round((vals[1]-vals[0]).total_seconds(),2),
            'mttr_seconds_observed':round((vals[2]-vals[1]).total_seconds(),2)}


def wan_seconds(folder):
    if not folder:return None
    root=Path(folder)
    start=parse_time((root/'inicio_utc.txt').read_text().strip())
    end=parse_time((root/'fim_utc.txt').read_text().strip())
    return round((end-start).total_seconds(),2) if end>=start else None


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--samples',type=int,default=5)
    p.add_argument('--interval',type=float,default=2.0)
    p.add_argument('--service',default='edge-ubs')
    p.add_argument('--sudo',action='store_true',help='Usa sudo -n; rode sudo -v antes')
    p.add_argument('--watts',type=float,help='Potencia média em W medida/assumida; estimativa, não medição')
    p.add_argument('--watts-origin',choices=['measured','assumed'],default='assumed')
    p.add_argument('--fault-utc')
    p.add_argument('--detected-utc')
    p.add_argument('--recovered-utc')
    p.add_argument('--wan-evidence')
    p.add_argument('--output',default='evidence/runtime/etapa2h_metricas')
    args=p.parse_args()
    if not 1<=args.samples<=100:p.error('--samples entre 1 e 100')
    if not 0.5<=args.interval<=3600:p.error('--interval entre 0.5 e 3600')
    if args.watts is not None and not 0<args.watts<5000:p.error('--watts invalido')
    if any([args.fault_utc,args.detected_utc,args.recovered_utc]) and not all([args.fault_utc,args.detected_utc,args.recovered_utc]):
        p.error('Informe os tres timestamps MTTD/MTTR ou nenhum')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    docker=['sudo','-n','docker'] if args.sudo else ['docker']
    compose=docker+['compose','-f','compose.wireguard.full.yaml','-f','compose.panel.yaml']
    rc,cid,err=run(compose+['ps','-q',args.service])
    if rc!=0 or not cid:raise SystemExit('Nao foi possivel encontrar container: '+(err or args.service))
    cid=cid.splitlines()[0]
    observations=[]
    for i in range(args.samples):
        stamp=datetime.now(timezone.utc).isoformat()
        sc,stats,stats_err=run(docker+['stats','--no-stream','--format','{{json .}}',cid],timeout=25)
        # health vem da propria rede VPN, sem liberar porta no host
        hc,healthy,health_err=run(compose+['exec','-T',args.service,'python','-c',
            "import urllib.request;print(urllib.request.urlopen('http://10.77.0.1:8080/health',timeout=4).status)"],timeout=15)
        row={'observed_at_utc':stamp,'health_ok':hc==0 and healthy.strip()=='200',
             'stats_ok':sc==0}
        if sc==0:
            try:row.update(parse_stats(stats))
            except (ValueError,KeyError,IndexError,json.JSONDecodeError) as exc:row['stats_error']=str(exc)
        else:row['stats_error']=stats_err
        observations.append(row)
        if i+1 < args.samples:time.sleep(args.interval)
    health_up=sum(row['health_ok'] for row in observations)
    total_duration=(parse_time(observations[-1]['observed_at_utc'])-parse_time(observations[0]['observed_at_utc'])).total_seconds()
    deltas={}
    for k in ('network_rx_bytes_total','network_tx_bytes_total'):
        numbers=[row[k] for row in observations if row.get(k) is not None]
        deltas[k.replace('_bytes_total','_bytes_delta')]=max(0,numbers[-1]-numbers[0]) if len(numbers)>1 else None
    report={'service':args.service,'observed_availability_pct':round(100*health_up/len(observations),2),
      'successful_probe_count':health_up,'total_probe_count':len(observations),
      'observation_duration_seconds':round(total_duration,2),
      'sample_count':len(observations),
      'cpu_pct_samples':[row.get('cpu_pct') for row in observations],
      'memory_bytes_samples':[row.get('memory_bytes') for row in observations],
      'network_io':deltas,
      'autonomy_seconds_from_wan_evidence':wan_seconds(args.wan_evidence),
      'mttd_seconds_observed':None,'mttr_seconds_observed':None,
      'energy_wh_estimate':round(args.watts*total_duration/3600,4) if args.watts is not None else None,
      'energy_watts_input':args.watts,'energy_watts_source':args.watts_origin if args.watts is not None else None,
      'limitations':'Percentual é disponibilidade observada somente nesta janela de amostragem, não SLA anual. Docker stats não mede energia. MTTD/MTTR sem timestamps de detecção reais são nulos.'}
    if args.fault_utc:report.update(time_metrics(args.fault_utc,args.detected_utc,args.recovered_utc))
    (out/'amostras.json').write_text(json.dumps(observations,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/'metricas.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    create_manifest(out)
    print(json.dumps({'status':'PASSOU','availability_pct_observed':report['observed_availability_pct'],
                      'samples':len(observations),'autonomy_seconds':report['autonomy_seconds_from_wan_evidence'],
                      'energy_measured':args.watts is not None and args.watts_origin=='measured',
                      'sha256_verified':verify_manifest(out),'output':str(out)},indent=2,ensure_ascii=False))

if __name__=='__main__':main()
