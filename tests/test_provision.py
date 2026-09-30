import os
import tempfile
import unittest
from unittest.mock import patch
import server
from core import Workspace


class ProvisionTests(unittest.TestCase):
    def test_short_password_only_for_explicit_preview_provisioning(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(server, 'DB', os.path.join(directory, 'preview.sqlite3')):
            for environment in ['', 'production', 'preview']:
                with patch.dict(os.environ, {'PMO_ENV': environment}):
                    with self.assertRaises(ValueError):
                        server.add_user('regular', 'x')
                    if environment != 'preview':
                        with self.assertRaises(ValueError):
                            server.add_user('demo', 'x', demo=True)
            with patch.dict(os.environ, {'PMO_ENV': 'preview'}):
                with self.assertRaises(ValueError):
                    server.add_user('demo', '', demo=True)
                server.add_user('demo', 'x', demo=True)
            w = Workspace(server.DB)
            try:
                saved = w.db.execute('SELECT password FROM users WHERE id=?', ('demo',)).fetchone()[0]
                self.assertNotEqual(saved, 'x')
                self.assertEqual(saved, server.hash_password('x', saved.split(':')[0]))
            finally:
                w.close()
