"""Receptor central HTTP de laboratorio (sem autenticacao; proxima etapa: VPN)."""
import json
import logging
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
LOG = logging.getLogger('cloud')

SCHEMA = '''CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY, site TEXT NOT NULL, ts_utc TEXT NOT NULL,
    kind TEXT NOT NULL, reading REAL NOT NULL, alert TEXT)'''


def accept_event(conn, obj):
    required = {'event_id', 'site', 'ts_utc', 'kind', 'reading', 'alert'}
    if not isinstance(obj, dict) or set(obj) != required:
        raise ValueError('campos invalidos')
    from .edge import SITES
    if obj['site'] not in SITES or obj['kind'] != SITES[obj['site']][0]:
        raise ValueError('site/tipo invalidos')
    if not isinstance(obj['event_id'], str) or len(obj['event_id']) > 80:
        raise ValueError('event_id invalido')
    reading = float(obj['reading'])
    if not (-1000 <= reading <= 1000):
        raise ValueError('leitura invalida')
    conn.execute('INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?)',
                 (obj['event_id'], obj['site'], obj['ts_utc'], obj['kind'], reading, obj['alert']))
    conn.commit()
    return {'event_id': obj['event_id'], 'status': 'stored'}


def make_handler(db_path):
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def respond(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path not in ('/health', '/stats'):
                return self.respond(404, {'error': 'not_found'})
            with lock, sqlite3.connect(db_path) as conn:
                count = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
                per_site = dict(conn.execute('SELECT site, COUNT(*) FROM events GROUP BY site').fetchall())
            return self.respond(200, {'status': 'ok', 'total_events': count, 'by_site': per_site})

        def do_POST(self):
            if self.path != '/events':
                return self.respond(404, {'error': 'not_found'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if size < 1 or size > 16384:
                    return self.respond(413, {'error': 'invalid_size'})
                obj = json.loads(self.rfile.read(size))
                with lock, sqlite3.connect(db_path) as conn:
                    result = accept_event(conn, obj)
                LOG.info('stored site=%s event=%s', obj['site'], obj['event_id'])
                return self.respond(200, result)
            except (ValueError, TypeError, KeyError, sqlite3.Error) as exc:
                LOG.warning('invalid_request: %s', exc)
                return self.respond(400, {'error': 'invalid_event'})

    return Handler


def main():
    path = Path(os.environ.get('DB_PATH', '/data/cloud.sqlite3'))
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute(SCHEMA)
    # Separacao do plano de dados (8080 sobre wg0) e observabilidade (8081).
    # A porta 8081 sera publicada SOMENTE em 127.0.0.1 do host Docker.
    class StatsOnly(make_handler(path)):
        def do_POST(self):
            return self.respond(405, {'error': 'method_not_allowed'})
    stats = ThreadingHTTPServer(('0.0.0.0', 8081), StatsOnly)
    threading.Thread(target=stats.serve_forever, daemon=True).start()
    server = ThreadingHTTPServer(('0.0.0.0', 8080), make_handler(path))
    LOG.info('cloud_listening port=8080')
    server.serve_forever()


if __name__ == '__main__':
    main()
