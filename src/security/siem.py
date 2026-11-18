"""Coletor acadêmico de logs com correlação por origem, deduplicação e retenção.

É um armazenamento central de laboratório, NÃO uma instalação Wazuh.
"""
import hashlib
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

REDACTIONS = [
    re.compile(r'(?i)(password|senha|totp_secret|totp_seed|authorization|token)\s*[:=]\s*([^\s,;]+)'),
    re.compile(r'(?i)(gh[pousr]_[A-Za-z0-9_]{20,})'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*'),
]


def clean_line(line):
    s = str(line)[:8192]
    s = REDACTIONS[0].sub(lambda m: m.group(1) + '=[REDACTED]', s)
    for pat in REDACTIONS[1:]:
        s = pat.sub('[REDACTED]', s)
    return s


class LocalSIEM:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS logs (
            id TEXT PRIMARY KEY, source TEXT NOT NULL, category TEXT NOT NULL,
            collected_at TEXT NOT NULL, message TEXT NOT NULL)''')
        self.conn.execute('CREATE INDEX IF NOT EXISTS logs_date_idx ON logs(collected_at)')
        self.conn.commit()

    def ingest(self, source, category, lines, at=None):
        at = (at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        count = 0
        for line in lines:
            line = clean_line(line).strip()
            if not line:
                continue
            # Idempotente ao reler a mesma janela de docker logs.
            event_id = hashlib.sha256(f'{source}\0{category}\0{line}'.encode()).hexdigest()
            cur = self.conn.execute('INSERT OR IGNORE INTO logs VALUES (?,?,?,?,?)',
                                    (event_id, source, category, at, line))
            count += cur.rowcount
        self.conn.commit()
        return count

    def expire(self, retention_days=30, now=None):
        if not 1 <= retention_days <= 365:
            raise ValueError('retention_days must be 1..365')
        now = now or datetime.now(timezone.utc)
        cutoff = (now.astimezone(timezone.utc) - timedelta(days=retention_days)).isoformat()
        cur = self.conn.execute('DELETE FROM logs WHERE collected_at < ?', (cutoff,))
        self.conn.commit()
        return cur.rowcount

    def summary(self):
        n = self.conn.execute('SELECT COUNT(*) FROM logs').fetchone()[0]
        sources = dict(self.conn.execute('SELECT source, COUNT(*) FROM logs GROUP BY source'))
        return {'events_total': n, 'sources': sources}

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()
