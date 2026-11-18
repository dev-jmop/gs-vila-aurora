#!/usr/bin/env python3
"""Run the deterministic synthetic model and integrity-protected evidence generation."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ai.anomaly import evaluate,triage
from src.security.evidence import create_manifest,verify_manifest


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='evidence/runtime/etapa2g');a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    report=evaluate();decision=triage(report)
    (out/'model_evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'human_review.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    create_manifest(out)
    assert verify_manifest(out)
    print(json.dumps({'status':'PASSOU','synthetic':True,'accuracy':report['accuracy'],
        'precision':report['precision'],'recall':report['recall'],'f1':report['f1'],
        'confusion_matrix':report['confusion_matrix'], 'automatic_actions':0,
        'sha256_verified':True,'output':str(out)},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
