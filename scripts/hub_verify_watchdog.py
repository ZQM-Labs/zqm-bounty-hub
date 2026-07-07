"""Local watchdog: runs bounty hub verification every 60 minutes."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(r'C:\Users\zqmco\AppData\Local\hermes\outputs\bounty_hub_verify.log')
SCRIPTS = Path(r'C:\Users\zqmco\AppData\Local\hermes\skills\zqm-bounty-hub\scripts')
PY = Path(r'C:\Users\zqmco\AppData\Local\hermes\venvs\bounty-hub-research\Scripts\python.exe')
if not PY.exists():
    PY = Path(sys.executable)


def run_once() -> str:
    code = f'''
import json
import sys
from pathlib import Path
sys.path.insert(0, r'{SCRIPTS}')
import hub_scores as hs
import hub_opportunity_alerts as hoa
import hub_pipeline as hpl
LOG = Path(r'{LOG}')
LOG.parent.mkdir(parents=True, exist_ok=True)
out_dir = Path(r'{SCRIPTS.parent / "outputs" / "cache"}')
out_dir.mkdir(parents=True, exist_ok=True)
today = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y-%m-%d')
(out_dir / f'{{today}}_programs.json').write_text(json.dumps({{'items': [{{'handle': 'shopify', 'name': 'Shopify', 'state': 'active', 'submission_state': 'open', 'offers_bounties': True, 'open_scope': True}}]}}), encoding='utf-8')
(out_dir / f'{{today}}_program_details.json').write_text(json.dumps({{'results': {{'shopify': {{'detail': {{'submission_state': 'open', 'offers_bounties': True, 'open_scope': True}}, 'weaknesses': ['XSS'], 'structured_scopes': ['*.shopify.com']}}}}}}), encoding='utf-8')
(out_dir / f'{{today}}_hacktivity.json').write_text(json.dumps({{'items': []}}), encoding='utf-8')
(out_dir / f'{{today}}_pipeline.json').write_text(json.dumps({{'report_intents': [], 'my_reports': []}}), encoding='utf-8')
print(hs.build_ranked_list())
print(hoa.build_alerts())
print(hpl.build_pipeline_markdown()[:200])
'''
    try:
        p = subprocess.run([str(PY), '-c', code], capture_output=True, text=True, cwd=str(SCRIPTS), timeout=120)
        first_line = (p.stdout or p.stderr).strip().splitlines()[0] if (p.stdout or p.stderr) else 'NO_OUTPUT'
        status = 'PASS' if p.returncode == 0 else 'FAIL'
        detail = first_line if status == 'PASS' else (' '.join((p.stderr or p.stdout or '').split())[:120] or first_line)
        return f'{status}: {detail}'
    except FileNotFoundError as e:
        return f'FAIL: missing executable: {e}'
    except Exception as e:
        return f'FAIL: {type(e).__name__}: {e}'


def _rotate_log(max_bytes: int = 1_048_576, backup_count: int = 5) -> None:
    try:
        if not LOG.exists() or LOG.stat().st_size < max_bytes:
            return
        log_dir = LOG.parent
        for i in range(backup_count, 1, -1):
            src = log_dir / f'{LOG.name}.{i}'
            dst = log_dir / f'{LOG.name}.{i + 1}'
            if src.exists():
                if i == backup_count:
                    src.unlink()
                else:
                    src.rename(dst)
        rotated = log_dir / f'{LOG.name}.1'
        if rotated.exists():
            rotated.unlink()
        LOG.rename(rotated)
    except Exception:
        pass


def main() -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    while True:
        ts = datetime.now(timezone.utc).isoformat()
        status = run_once()
        line = f'[{ts}] {status}\n'
        try:
            with LOG.open('a', encoding='utf-8') as f:
                f.write(line)
            _rotate_log()
        except Exception:
            pass
        print(line, end='')
        try:
            time.sleep(3600)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main()
