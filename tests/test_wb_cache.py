"""Regression: wbdata must not open an old shared or damaged shelve."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class WorldBankCacheTests(unittest.TestCase):
    def test_import_and_client_ignore_broken_shared_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            broken=Path(folder)/'cache'
            broken.write_bytes(b'not a shelve database')
            code='''import os
from quantlabs.wb_client import client
c=client()
assert str(c.cache_path) != os.environ['WBDATA_CACHE_PATH']
assert client() is c
'''
            result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'engine'),'WBDATA_CACHE_PATH':str(broken)},capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(broken.read_bytes(),b'not a shelve database')

if __name__=='__main__':unittest.main()
