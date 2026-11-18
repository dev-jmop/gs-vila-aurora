# Painel de supervisao didatico. Apenas localhost.
import json
import os
import secrets
import sqlite3
import time
from collections import defaultdict
from functools import wraps
from pathlib import Path
from flask import Flask, abort, flash, redirect, render_template_string, request, session, url_for
from .auth import authenticate, load_users

STYLE = '''<style>
:root{font-family:system-ui,Arial,sans-serif;color:#132536;background:#f5f8fa}body{margin:0}
header{background:#123b58;color:white;padding:1.1rem max(1rem,calc((100vw - 1000px)/2))}
main{max-width:1000px;margin:1.5rem auto;padding:0 1rem}section,article{background:white;border:1px solid #b8ccd8;border-radius:12px;padding:1.2rem;margin-bottom:1rem}
nav a{color:#fff;margin-right:1.2rem}a{color:#075a85}table{border-collapse:collapse;width:100%}td,th{text-align:left;border-bottom:1px solid #d6e1e8;padding:.7rem}
input,button{font:inherit;padding:.7rem;max-width:100%;margin:.25rem 0}input{border:1px solid #607c91;border-radius:5px}button{background:#005b87;color:white;border:0;border-radius:6px;cursor:pointer}button:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid #ee9800;outline-offset:2px}.ok{font-weight:700;color:#006845}.notice{background:#fff1cc;padding:.7rem}
</style>'''
TEMPLATE='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Vila Aurora · {{ title }}</title>'''+STYLE+'''</head><body><header><strong>Rede Comunitária Vila Aurora</strong><p>Supervisão demonstrativa · dados sintéticos</p><nav>{% if user %}<a href="{{url_for('dashboard')}}">Painel</a><a href="{{url_for('audit')}}">Auditoria</a><a href="{{url_for('technical')}}">Técnicos</a><a href="{{url_for('logout')}}">Sair</a>{% endif %}</nav></header><main><h1>{{title}}</h1><p role="status">{% for m in get_flashed_messages() %}{{m}}{% endfor %}</p>'''+'''{{ body|safe }}'''+'''</main></body></html>'''

def create_app(config=None):
    app=Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get('PANEL_SESSION_KEY',''), USERS_FILE=os.environ.get('PANEL_USERS_FILE','/auth/users.json'), CLOUD_DB=os.environ.get('PANEL_CLOUD_DB','/cloud/cloud.sqlite3'), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict', PERMANENT_SESSION_LIFETIME=900, MAX_CONTENT_LENGTH=8192)
    if config: app.config.update(config)
    if not app.config['SECRET_KEY']:
        if not app.config.get('TESTING'): raise RuntimeError('PANEL_SESSION_KEY obrigatoria. Execute setup_panel_auth.py')
        app.config['SECRET_KEY']='test-only-not-for-deployment'
    attempts=defaultdict(list)

    @app.after_request
    def headers(resp):
        resp.headers['Content-Security-Policy']="default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
        resp.headers['X-Content-Type-Options']='nosniff'
        resp.headers['Cache-Control']='no-store'
        resp.headers['Referrer-Policy']='no-referrer'
        return resp

    def view(title,body):
        return render_template_string(TEMPLATE,title=title,body=body,user=session.get('user'))

    def requires(*roles):
        def decorator(fn):
            @wraps(fn)
            def wrapped(*args,**kwargs):
                if not session.get('user'): return redirect(url_for('login'))
                if roles and session.get('role') not in roles: abort(403)
                return fn(*args,**kwargs)
            return wrapped
        return decorator

    @app.get('/')
    def index(): return redirect(url_for('dashboard') if session.get('user') else url_for('login'))

    @app.route('/login',methods=['GET','POST'])
    def login():
        if request.method=='POST':
            ip=request.remote_addr or 'unknown'; now=time.monotonic()
            attempts[ip]=[t for t in attempts[ip] if now-t<60]
            if len(attempts[ip])>=6: return view('Login','<section role="alert">Muitas tentativas. Tente novamente mais tarde.</section>'),429
            username=request.form.get('username','')[:80]
            password=request.form.get('password','')[:200]
            code=request.form.get('code','')
            try: role=authenticate(load_users(app.config['USERS_FILE']),username,password,code)
            except (OSError,ValueError,KeyError): role=None
            if role:
                session.clear();session['user']=username;session['role']=role;session['csrf']=secrets.token_urlsafe(24);session.permanent=True
                attempts[ip].clear()
                return redirect(url_for('dashboard'))
            attempts[ip].append(now)
            flash('Credenciais ou código inválidos.')
        return view('Acesso com MFA','''<section><form method="post"><label>Usuário<br><input name="username" autocomplete="username" required></label><p><label>Senha<br><input name="password" type="password" autocomplete="current-password" required></label></p><p><label>Código TOTP de seis dígitos<br><input name="code" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" required></label></p><button>Entrar</button></form><p>Somente contas fictícias de laboratório. Não use credenciais reais.</p></section>''')

    @app.get('/logout')
    def logout():session.clear();return redirect(url_for('login'))

    def stats():
        path=Path(app.config['CLOUD_DB'])
        if not path.exists(): return [],0,'Banco central não encontrado.'
        try:
            with sqlite3.connect(f'file:{path}?mode=ro',uri=True,timeout=2) as db:
                rows=db.execute('SELECT site, COUNT(*) FROM events GROUP BY site ORDER BY site').fetchall()
                return rows,sum(n for _,n in rows),None
        except sqlite3.Error: return [],0,'Não foi possível consultar a telemetria agora.'

    @app.get('/dashboard')
    @requires()
    def dashboard():
        from markupsafe import escape
        rows,total,error=stats()
        body='<section><h2>Eventos por espaço</h2><p>Total: <strong>'+str(total)+'</strong></p>'
        if error:body+='<p role="alert">'+str(escape(error))+'</p>'
        body+='<table><thead><tr><th>Espaço</th><th>Eventos</th></tr></thead><tbody>'
        for site,n in rows:body+=f'<tr><td>{escape(site)}</td><td>{n}</td></tr>'
        body+='</tbody></table><p>Leitura direta e somente consulta ao banco de telemetria central.</p></section>'
        body+='<section><h2>Perfil</h2><p>Usuário: '+str(escape(session['user']))+' · papel: '+str(escape(session['role']))+'</p></section>'
        return view('Painel de supervisão',body)

    @app.get('/audit')
    @requires('auditor','coordenacao')
    def audit():
        return view('Auditoria','<section><p>Acesso restrito aos perfis auditor e coordenação.</p><p>Eventos técnicos do laboratório são consultados nos logs Docker. Integração SIEM ainda pendente.</p></section>')

    @app.get('/technical')
    @requires('tecnico','coordenacao')
    def technical():
        return view('Área técnica','<section><p>Acesso restrito a técnico e coordenação. Nenhum atuador físico está conectado.</p></section>')

    @app.post('/ack')
    @requires('operador','tecnico','coordenacao')
    def acknowledge():
        if not secrets.compare_digest(request.form.get('csrf',''),session.get('csrf','')): abort(403)
        flash('Confirmação simulada; nenhum comando físico foi enviado.')
        return redirect(url_for('dashboard'))

    @app.errorhandler(403)
    def denied(_):return view('Acesso negado','<section role="alert">Seu perfil não permite esta operação.</section>'),403
    return app

if __name__=='__main__':
    create_app().run(host='0.0.0.0',port=8090,debug=False)
