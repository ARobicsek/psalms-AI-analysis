import json, sys, collections
from pathlib import Path
sys.path.insert(0, '.')
import tiktoken
enc = tiktoken.get_encoding('o200k_base')
from src.agents.fact_checker import FactChecker
p = int(sys.argv[1]); out = Path(f'output/psalm_{p}')
t = json.load(open(out/f'psalm_{p:03d}_fact_check_telemetry.json', encoding='utf-8'))
bundle = (out/f'psalm_{p:03d}_research_trimmed.md').read_text(encoding='utf-8')
fc = FactChecker(db_path=Path('database/tanakh.db'), client=object())
cur = collections.Counter(); err = 0
for e in t['trace']:
    if e.get('kind') != 'lookup' or not e['run'].startswith('local'): continue
    r = fc._run_tool(e['tool'], e['args'], bundle)
    if 'error' in r: err += 1
    cur[e['tool']] += len(enc.encode(json.dumps(r, ensure_ascii=False)[:20000]))
for k in cur: print(f'{k:16s} {cur[k]:7d}')
print('TOTAL', sum(cur.values()), 'errors', err)
