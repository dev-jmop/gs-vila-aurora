#!/usr/bin/env python3
"""Auditoria local do indice Git; nao imprime conteudo de segredos."""
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
checks=[]
r=subprocess.run(['git','ls-files','--cached'],cwd=ROOT,capture_output=True,text=True)
if r.returncode:
    raise SystemExit('ERRO: execute dentro de um repositorio Git inicializado.')
files=[line.strip() for line in r.stdout.splitlines() if line.strip()]
if not files:
    raise SystemExit('ERRO: nao ha arquivos no indice Git. Prepare git add antes da verificacao.')
prohibited=re.compile(r'(^|/)(runtime|__pycache__|secrets?|private)(/|$)|\.(key|pem|p12|pfx|sqlite3|db|pyc|env)$',re.I)
for f in files:
    if prohibited.search(f): checks.append(f'ARQUIVO PRIVADO NO GIT: {f}')
    p=ROOT/f
    if not p.is_file(): checks.append(f'ARQUIVO INDEXADO AUSENTE: {f}')
for required in ('E1_Arquitetura_Vila_Aurora.pdf','E3_Testes_Seguranca_Vila_Aurora.pdf','E4_Laudo_Forense_INC-VA-0712.pdf'):
    p=f'docs/relatorios/{required}'
    if p not in files: checks.append(f'PDF AUSENTE DO INDICE: {p}')
for f in files:
    if f.endswith(('.md','.txt')) and (ROOT/f).is_file():
        content=(ROOT/f).read_text(encoding='utf-8',errors='ignore')
        if 'Arch Linux' in content or 'arch linux' in content.lower():
            checks.append(f'REFERENCIA AO SO NA DOCUMENTACAO: {f}')
print(f'Arquivos indexados: {len(files)}')
if checks:
    print('NAO APROVADO:')
    for c in checks: print('  -',c)
    sys.exit(1)
print('PASSOU: arquivos sensiveis nao aparecem no indice, 3 PDFs presentes e sem mencoes ao SO.')
print('ATENCAO: verificacao basica; nao substitui revisao de historico, conteudo e credenciais.')
