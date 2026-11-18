import unittest
from pathlib import Path
from src.tls_config import configure_tls

ROOT = Path(__file__).resolve().parent.parent


class TestMTLSConfig(unittest.TestCase):
    def test_no_plaintext_listener(self):
        config = (ROOT/'mqtt/mosquitto.conf').read_text()
        self.assertIn('listener 8883', config)
        self.assertIn('require_certificate true', config)
        self.assertIn('allow_anonymous false', config)
        self.assertNotIn('listener 1883', config)
        self.assertIn('crlfile /certs/ca.crl', config)

    def test_ten_unique_client_roles_in_acl(self):
        acl = (ROOT/'mqtt/aclfile').read_text()
        for site in ['centro','escola','ubs','horta','abrigo']:
            self.assertIn(f'user sensor-{site}\ntopic write vila/{site}/telemetry', acl)
            self.assertIn(f'user edge-{site}\ntopic read vila/{site}/telemetry', acl)

    def test_configure_tls_requires_certificate_files(self):
        class FakeClient:
            def tls_set(self, **kwargs): self.config = kwargs
            def tls_insecure_set(self, value): self.insecure = value
        client = FakeClient()
        configure_tls(client)
        self.assertTrue(client.config['certfile'])
        self.assertFalse(client.insecure)


if __name__ == '__main__':
    unittest.main()
