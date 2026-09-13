#!/usr/bin/env python3
"""Check Git-index content for private artifacts and known local generated credentials."""
import json,re,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
files=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
values=set()
def collect(d):
 if isinstance(d,dict):
  for k,v in d.items():
   if isinstance(v,str) and len(v)>=12 and any(t in k.lower() for t in ['password','secret','hash']):values.add(v.encode())
   else:collect(v)
 elif isinstance(d,list):
  for v in d:collect(v)
for path in [root/'.runtime/secrets.json',root/'openshift/rendered/deployment-secrets.json']:
 if path.exists():collect(json.loads(path.read_text()))
patterns=[re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),re.compile(rb'github_pat_[A-Za-z0-9_]{40,}'),re.compile(rb'AKIA[0-9A-Z]{16}')]
problems=[]
for f in filter(None,files):
 if f.startswith(('.runtime/','backups/','openshift/rendered/','verification/private/')) or f.endswith(('deployment-secrets.json','.p12','.pfx')):
  problems.append(f+' (private path)');continue
 data=subprocess.check_output(['git','show',':'+f],cwd=root)
 if any(v in data for v in values):problems.append(f+' (generated credential match)')
 if any(p.search(data) for p in patterns):problems.append(f+' (credential pattern)')
if problems:
 print('FAIL: credential/private-artifact scan\n'+'\n'.join(problems));sys.exit(1)
print(f'PASS: {len(list(filter(None,files)))} indexed files; no known generated credentials or private runtime artifacts.')
