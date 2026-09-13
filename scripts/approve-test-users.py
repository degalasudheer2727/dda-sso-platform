#!/usr/bin/env python3
"""Approve only generated lab users in the existing local Web UI database."""
import json, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
emails=[u['email'] for u in json.loads((root/'.runtime/secrets.json').read_text())['users']]
code='''import json,sys,sqlite3
emails=json.load(sys.stdin)
c=sqlite3.connect('/app/backend/data/webui.db')
with c:
 for email in emails:
  c.execute("UPDATE user SET role='user' WHERE email=? AND role='pending'", (email,))
rows=c.execute("SELECT email,role FROM user WHERE email IN ("+','.join('?' for _ in emails)+")",emails).fetchall()
assert len(rows)==5 and all(role=='user' for _,role in rows), rows
print('PASS: all five demo accounts have the ordinary user role')
'''
subprocess.run([str(root/'scripts/local.sh'),'stop','open-webui'],check=True)
try:
 subprocess.run(['docker','run','--rm','-i','--volumes-from','open-webui','--entrypoint','python',
  'ghcr.io/open-webui/open-webui:v0.11.3','-c',code],input=json.dumps(emails).encode(),check=True)
finally: subprocess.run([str(root/'scripts/local.sh'),'start','open-webui'],check=True)
