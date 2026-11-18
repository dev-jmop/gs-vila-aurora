"""Valida provisionamento reprodutivel sem vazamento no stdout (ambiente isolado)."""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from werkzeug.security import check_password_hash

class FirstSetupTests(unittest.TestCase):
    def test_initial_credentials_local_and_not_printed(self):
        source=Path(__file__).resolve().parents[1]/'scripts'/'setup_panel_auth.py'
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'scripts').mkdir()
            target=root/'scripts'/'setup_panel_auth.py'
            shutil.copyfile(source,target)
            result=subprocess.run([sys.executable,str(target)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            auth=root/'auth'/'runtime'
            text=(auth/'credenciais_iniciais.txt').read_text()
            self.assertNotIn('senha: ',result.stdout)
            self.assertNotIn('TOTP_secret: ',result.stdout)
            users=json.loads((auth/'users.json').read_text())
            self.assertEqual(set(users),{'operador','tecnico','coordenacao','auditor'})
            for name in ('users.json','session.key','credenciais_iniciais.txt'):
                self.assertEqual(stat.S_IMODE((auth/name).stat().st_mode),0o600)
            blocks=text.split('\n\n')
            self.assertGreaterEqual(len(blocks),4)
            for block in blocks:
                lines=block.splitlines()
                if not lines:continue
                username=lines[0]; self.assertIn(username,users)
                password=[x.split(': ',1)[1] for x in lines if x.startswith('senha: ')][0]
                self.assertTrue(check_password_hash(users[username]['password_hash'],password))
            again=subprocess.run([sys.executable,str(target)],capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0)
