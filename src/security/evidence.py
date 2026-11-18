"""Integrity manifest for generated evidence files. Not a digital signature."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

def create_manifest(outdir):
    outdir=Path(outdir)
    manifest={'created_at_utc':datetime.now(timezone.utc).isoformat(),'algorithm':'SHA-256','files':[]}
    for file in sorted(outdir.iterdir()):
        if file.is_file() and file.name!='sha256_manifest.json':
            manifest['files'].append({'filename':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(), 'bytes':file.stat().st_size})
    (outdir/'sha256_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return manifest

def verify_manifest(outdir):
    outdir=Path(outdir)
    manifest=json.loads((outdir/'sha256_manifest.json').read_text(encoding='utf-8'))
    return all((outdir/item['filename']).is_file() and hashlib.sha256((outdir/item['filename']).read_bytes()).hexdigest()==item['sha256'] for item in manifest['files'])
