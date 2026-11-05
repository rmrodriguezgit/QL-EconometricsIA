"""Paralelismo: nodos independientes en hilos, avisos por hilo, procesos internos y canal JSON-RPC limpio."""
import json
import os
import subprocess
import sys
import threading
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))

from quantlabs.core import execute  # noqa: E402
from quantlabs.parallel import capture_warnings, jobs_for, workers  # noqa: E402
from quantlabs.projects import dispatch_files  # noqa: E402


def comparable(run):
    sources = {k: {a: b for a, b in v.items() if a != 'retrieved_at'} for k, v in run['manifest']['sources'].items()}
    return json.dumps({'status': run['status'], 'nodes': run['nodes'], 'order': run['manifest']['execution_order'], 'sources': sources},
                      sort_keys=True, default=str)


class ParallelExecutionTests(unittest.TestCase):
    def test_examples_identical_with_and_without_threads(self):
        items = [item['id'] for item in dispatch_files('examples.list', {})['items'] if not item.get('network')]
        for example in items:
            project = dispatch_files('examples.read', {'id': example})['project']
            with patch.dict(os.environ, {'QL_ENGINE_THREADS': '1'}):
                sequential = comparable(execute(project))
            with patch.dict(os.environ, {'QL_ENGINE_THREADS': '8'}):
                parallel = comparable(execute(project))
            self.assertEqual(sequential, parallel, example)

    def test_independent_nodes_overlap_and_failures_skip_children(self):
        node = lambda i, t, p: {'id': i, 'type': t, 'node_version': '1.0.0', 'position': {'x': 0, 'y': 0}, 'parameters': p}
        edge = lambda s, t: {'id': f'{s}-{t}', 'source': s, 'source_port': 'data', 'target': t, 'target_port': 'data'}
        project = {'schema_version': '1.0.0', 'app_version': '0.17.0', 'title': 'p', 'nodes': [
            node('d', 'synthetic', {'scenario': 'multiple', 'n': 300, 'seed': 1}),
            node('a', 'describe', {}), node('b', 'describe', {}), node('c', 'describe', {}),
            node('bad', 'split', {'fraction': 5, 'method': 'temporal', 'seed': 1}), node('after', 'describe', {})],
            'edges': [edge('d', 'a'), edge('d', 'b'), edge('d', 'c'), edge('d', 'bad'),
                      {'id': 'x', 'source': 'bad', 'source_port': 'train', 'target': 'after', 'target_port': 'data'}]}
        import quantlabs.core as core
        original, seen, gate = core.describe, set(), threading.Barrier(3, timeout=5)

        def slow_describe(frame, params):
            seen.add(threading.current_thread().name)
            gate.wait()  # solo pasa si los tres descriptivos corren a la vez
            return original(frame, params)
        with patch.dict(os.environ, {'QL_ENGINE_THREADS': '4'}), patch.object(core, 'describe', slow_describe):
            run = execute(project)
        self.assertEqual({run['nodes'][k]['status'] for k in 'abc'}, {'succeeded'})
        self.assertEqual(len(seen), 3)
        self.assertEqual(run['nodes']['bad']['status'], 'failed')
        self.assertEqual(run['nodes']['after']['status'], 'skipped')
        self.assertEqual(list(run['nodes']), run['manifest']['execution_order'])

    def test_warnings_stay_in_their_thread(self):
        results = {}

        def emit(name):
            with capture_warnings() as messages:
                for i in range(50):
                    warnings.warn(f'{name}-{i}')
            results[name] = {str(m.message) for m in messages}
        threads = [threading.Thread(target=emit, args=(name,)) for name in 'abcd']
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for name in 'abcd':
            self.assertEqual(results[name], {f'{name}-{i}' for i in range(50)})

    def test_worker_settings(self):
        with patch.dict(os.environ, {'QL_ENGINE_THREADS': '3'}):
            self.assertEqual(workers(), 3)
        with patch.dict(os.environ, {'QL_ENGINE_PROCESSES': ''}):
            self.assertEqual(jobs_for(49 * 3 * 20 * 5), 1)  # muestra de clase: sin procesos
        with patch.dict(os.environ, {'QL_ENGINE_PROCESSES': '1'}):
            self.assertEqual(jobs_for(10**9), 1)
        with patch.dict(os.environ, {'QL_ENGINE_PROCESSES': '2'}):
            self.assertEqual(jobs_for(10**9), min(2, os.cpu_count() or 1))


class ChannelTests(unittest.TestCase):
    def test_persistent_process_answers_one_line_per_request_and_ignores_prints(self):
        code = ("import runpy,sys,builtins;sys.argv=['quantlabs'];"
                "import quantlabs.__main__ as m;orig=m.dispatch\n"
                "def noisy(r):\n print('ruido de una librería')\n return orig(r)\n"
                "m.dispatch=noisy;m.main()")
        requests = ''.join(json.dumps({'jsonrpc': '2.0', 'id': i, 'method': method}) + '\n'
                           for i, method in enumerate(['engine.health', 'engine.warmup', 'engine.health']))
        out = subprocess.run([sys.executable, '-c', code], input=requests, capture_output=True, text=True, timeout=120,
                             env={**os.environ, 'PYTHONPATH': str(ROOT / 'engine')}, cwd=ROOT)
        lines = out.stdout.strip().splitlines()
        self.assertEqual([json.loads(line)['id'] for line in lines], [0, 1, 2])
        self.assertTrue(json.loads(lines[1])['result']['ready'])
        self.assertIn('ruido de una librería', out.stderr)


if __name__ == '__main__':
    unittest.main()
