import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

sync = load('sync')
check_docs = load('check_docs')

class DocumentationTests(unittest.TestCase):
    def test_current_documents(self):
        check_docs.check()

    def test_missing_reference_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in [*check_docs.REQUIRED, 'docs/bibliografia.json']:
                dest = root / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((ROOT / name).read_bytes())
            path = root / 'docs/COBERTURA.md'
            path.write_text(path.read_text().replace('B02', 'MISSING'))
            with self.assertRaisesRegex(ValueError, 'Missing reference: B02'):
                check_docs.check(root)

class ScopeTests(unittest.TestCase):
    def test_private_files_excluded(self):
        for name in ['bibliografía/book.pdf', 'bibliografía.zip', '.env',
                     'docs/book.pdf', 'docs/token.key', 'scripts/__pycache__/a.pyc',
                     'docs/.env.txt', 'data/private.csv', 'apps/desktop/node_modules/pkg/index.ts',
                     'apps/desktop/dist/index.html', 'apps/desktop/src-tauri/target/build.rs',
                     'apps/desktop/src-tauri/binaries/engine.lock']:
            self.assertFalse(sync.permitted(name), name)
        self.assertTrue(sync.permitted('docs/ARQUITECTURA.md'))
        self.assertTrue(sync.permitted('.github/workflows/docs.yml'))

    def test_unexpected_remote_rejected_before_validation_or_staging(self):
        with patch.object(sync, 'git', side_effect=['main', 'https://other.invalid/repo']), \
             patch.object(sync.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'Unexpected origin'):
                sync.sync('docs: change')
            run.assert_not_called()

    def test_foreign_staging_rejected(self):
        with patch.object(sync, 'git', side_effect=['main', sync.EXPECTED_REMOTE, '.env']), \
             patch.object(sync.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'outside allowed scope'):
                sync.sync('docs: change')
            run.assert_not_called()

    def test_push_failure_preserves_commit_and_retry_is_idempotent(self):
        # Mock validation to avoid recursively running this test suite.
        responses = ['main', sync.EXPECTED_REMOTE, '', 'author', 'author@example.test',
                     'README.md', '', 'README.md', '', 'abc123']
        with patch.object(sync, 'git', side_effect=responses) as git, \
             patch.object(sync.subprocess, 'run', side_effect=[None, None, None,
                         subprocess.CalledProcessError(1, ['git', 'push'])]):
            with self.assertRaises(subprocess.CalledProcessError):
                sync.sync('docs: change')
            self.assertTrue(any(call.args[:1] == ('commit',) for call in git.call_args_list))
            self.assertFalse(any(call.args[:1] == ('reset',) for call in git.call_args_list))
        responses = ['main', sync.EXPECTED_REMOTE, '', 'author', 'author@example.test',
                     'README.md', '', '']
        with patch.object(sync, 'git', side_effect=responses) as git, \
             patch.object(sync.subprocess, 'run') as run:
            sync.sync('docs: retry')
            self.assertFalse(any(call.args[:1] == ('commit',) for call in git.call_args_list))
            self.assertEqual(run.call_args.args[0], ['git', 'push', '-u', 'origin', 'main'])

if __name__ == '__main__':
    unittest.main()
