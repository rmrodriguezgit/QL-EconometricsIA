"""Validate, commit permitted project files, then push without rewriting history."""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REMOTE = 'https://github.com/rmrodriguezgit/Quantlabs-Econometrics.git'
FILES = {'README.md', 'AGENTS.md', 'CHANGELOG.md', 'VERSION', '.gitignore', 'pyproject.toml', 'uv.lock', 'Arrancar-Quantlabs.command', 'Arrancar-Quantlabs.cmd'}
DIRECTORIES = {'docs', 'scripts', 'tests', '.github', 'apps', 'engine', 'packages', 'examples'}
SUFFIXES = {'.md', '.json', '.py', '.yml', '.yaml', '.toml', '.txt', '.ts', '.tsx', '.css', '.html', '.rs', '.lock', '.cjs', '.command', '.cmd'}


def permitted(name):
    path = Path(name)
    if name in FILES:
        return True
    if not path.parts or path.parts[0] not in DIRECTORIES:
        return False
    if any(part.startswith('.') and part != '.github' for part in path.parts):
        return False
    if any(part in {'__pycache__', 'node_modules', 'data', 'runs', 'dist', 'target', 'binaries'} for part in path.parts):
        return False
    return path.suffix.lower() in SUFFIXES


def git(*args, root=ROOT):
    return subprocess.run(['git', *args], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


def sync(message, root=ROOT, remote=EXPECTED_REMOTE):
    if not message.strip():
        raise ValueError('Commit message cannot be empty')
    if git('branch', '--show-current', root=root) != 'main':
        raise ValueError('Expected branch main; inspect the current branch first')
    if git('remote', 'get-url', 'origin', root=root) != remote:
        raise ValueError('Unexpected origin; refusing to change remote or publish')
    staged = git('diff', '--cached', '--name-only', '-z', root=root).split('\0')
    if any(name and not permitted(name) for name in staged):
        raise ValueError('Staged files outside allowed scope; review staging first')
    for key in ['user.name', 'user.email']:
        if not git('config', '--get', key, root=root):
            raise ValueError(f'Configure repository-local {key} first')
    subprocess.run([sys.executable, 'scripts/check_docs.py'], cwd=root, check=True)
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                   cwd=root, check=True)
    if (root / 'apps/desktop/package.json').exists():
        import shutil
        npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
        if not npm:
            raise ValueError('Instala Node.js y ejecuta npm ci en apps/desktop')
        subprocess.run([npm, 'run', 'test:desktop', '--prefix', 'apps/desktop'], cwd=root, check=True)
        subprocess.run([npm, 'run', 'build', '--prefix', 'apps/desktop'], cwd=root, check=True)
    candidates = git('ls-files', '--cached', '--others', '--exclude-standard', '-z', root=root)
    paths = sorted({name for name in candidates.split('\0') if name and permitted(name)})
    if paths:
        git('add', '--all', '--', *paths, root=root)
    if git('diff', '--cached', '--name-only', root=root):
        git('commit', '-m', message, root=root)
        print('Commit created:', git('rev-parse', '--short', 'HEAD', root=root), flush=True)
    else:
        print('No new changes; retrying any pending push.', flush=True)
    # Run visibly and preserve local commit when authentication/network fails.
    subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=root, check=True)
    print('Push completed: origin/main', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--message', required=True)
    args = parser.parse_args()
    try:
        sync(args.message)
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f'Synchronization stopped: {error}', file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.strip(), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
