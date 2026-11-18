import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from werkzeug.security import generate_password_hash
from src.supervision.auth import authenticate, totp, verify_totp
from src.supervision.panel import create_app
from src.supervision.sqli_lab import create_app as create_lab, query_safe, query_vulnerable

class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); root=Path(self.tmp.name)
        self.secret='JBSWY3DPEHPK3PXP'
        self.users={'operador':{'role':'operador','password_hash':generate_password_hash('teste-ficticio'),'totp_secret':self.secret}}
        (root/'users.json').write_text(json.dumps(self.users))
        self.panel=create_app({'TESTING':True,'USERS_FILE':str(root/'users.json'),'CLOUD_DB':str(root/'events.sqlite3')}).test_client()
        self.lab=create_lab({'TESTING':True,'LAB_DB':str(root/'lab.sqlite3')}).test_client()
    def tearDown(self):self.tmp.cleanup()
    def test_totp_valid_invalid(self):
        self.assertTrue(verify_totp(self.secret,totp(self.secret,at=60),at=60))
        self.assertFalse(verify_totp(self.secret,'0000000',at=60))
    def test_auth_two_factors(self):
        self.assertEqual(authenticate(self.users,'operador','teste-ficticio',totp(self.secret)), 'operador')
        self.assertIsNone(authenticate(self.users,'operador','senha-incorreta',totp(self.secret)))
    def test_rbac_denies_audit(self):
        resp=self.panel.post('/login',data={'username':'operador','password':'teste-ficticio','code':totp(self.secret)})
        self.assertEqual(resp.status_code,302)
        self.assertEqual(self.panel.get('/audit').status_code,403)
        self.assertEqual(self.panel.get('/dashboard').status_code,200)
    def test_sqli_before_after(self):
        payload="' OR 1=1 -- "
        old=self.lab.get('/vulnerable',query_string={'q':payload}).get_json()
        new=self.lab.get('/safe',query_string={'q':payload}).get_json()
        self.assertEqual(old['count'],3)
        self.assertEqual(new['count'],0)
    def test_safe_normal_search(self):
        self.assertEqual(self.lab.get('/safe',query_string={'q':'Ana'}).get_json()['count'],1)
    def test_safe_errors_hide_sql(self):
        r=self.lab.get('/safe',query_string={'q':'a'*100})
        self.assertEqual(r.status_code,400)
        self.assertEqual(r.get_json(),{'error':'invalid_query'})

if __name__=='__main__':unittest.main()
