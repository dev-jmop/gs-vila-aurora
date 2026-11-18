"""SQL Injection intencional. APENAS container isolado e dados sintéticos."""
import os
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request

def init_lab(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS fake_users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL)')
        if not db.execute('SELECT 1 FROM fake_users LIMIT 1').fetchone():
            db.executemany('INSERT INTO fake_users(name,role) VALUES(?,?)', [('Ana Fictícia','voluntaria'),('Bruno Teste','operador'),('Carla Exemplo','auditor')])
        db.commit()

def query_vulnerable(db,term):
    # Deliberadamente inseguro: apenas dados inventados dentro de um container separado.
    statement="SELECT name, role FROM fake_users WHERE name LIKE '%" + term + "%'"
    return db.execute(statement).fetchall()

def query_safe(db,term):
    if len(term)>60 or any(ord(ch)<32 for ch in term): raise ValueError('entrada invalida')
    # Parametrizacao protege a sintaxe SQL independentemente do conteudo do termo.
    return db.execute('SELECT name, role FROM fake_users WHERE name LIKE ?',('%'+term+'%',)).fetchall()

def create_app(config=None):
    app=Flask(__name__)
    app.config['LAB_DB']=os.environ.get('LAB_DB','/data/sqli_lab.sqlite3')
    if config:app.config.update(config)
    init_lab(app.config['LAB_DB'])
    @app.get('/')
    def home():return jsonify({'ambiente':'laboratorio SQLi isolado','dados':'100% sinteticos','endpoints':['/vulnerable?q=','/safe?q=']})
    @app.get('/<mode>')
    def search(mode):
        if mode not in ('vulnerable','safe'):return jsonify({'error':'not_found'}),404
        term=request.args.get('q','')
        try:
            with sqlite3.connect(app.config['LAB_DB']) as db:
                rows=query_vulnerable(db,term) if mode=='vulnerable' else query_safe(db,term)
        except (sqlite3.Error, ValueError):
            return jsonify({'error':'invalid_query'}),400
        return jsonify({'mode':mode,'count':len(rows),'records':[{'name':n,'role':r} for n,r in rows]})
    return app

if __name__=='__main__':create_app().run(host='0.0.0.0',port=8091,debug=False)
