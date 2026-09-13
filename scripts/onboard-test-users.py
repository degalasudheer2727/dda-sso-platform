#!/usr/bin/env python3
"""Browser-driven login of generated users. Does not print passwords or tokens."""
import json, re, subprocess, time, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
fixture=json.loads((root/'.runtime/secrets.json').read_text())
users=[fixture['admin']] if '--admin' in sys.argv else fixture['users']
def browser(session,*args):
 r=subprocess.run(['npx','--yes','agent-browser','--session',session,*args],capture_output=True,text=True,timeout=60)
 if r.returncode: raise RuntimeError(r.stderr.strip() or r.stdout.strip())
 return r.stdout

def ref(snapshot,label):
 for line in snapshot.splitlines():
  if label in line:
   m=re.search(r'ref=(e\d+)',line)
   if m: return '@'+m.group(1)
 raise RuntimeError('Missing UI control: '+label+'\n'+snapshot)

for u in users:
 session='dda-'+u['username']
 try:
  browser(session,'open','http://webui.localhost:3000/auth')
  snap=browser(session,'snapshot','-i'); browser(session,'click',ref(snap,'Continue with DDA SSO'))
  snap=browser(session,'snapshot','-i')
  assert 'Email Address' in snap, 'Expected direct Dex login, without Keycloak selection page: '+snap
  browser(session,'fill',ref(snap,'Email Address'),u['email'])
  browser(session,'fill',ref(snap,'textbox "Password"'),u['password'])
  browser(session,'click',ref(snap,'button "Login"'))
  snap=browser(session,'snapshot','-i')
  assert 'Update Account Information' not in snap, 'Unexpected second profile form'
  browser(session,'wait','--load','networkidle')
  url=browser(session,'get','url').strip()
  if url!='http://webui.localhost:3000/': raise RuntimeError('Unexpected final URL: '+url)
  print(u['username']+': brokered browser login PASS',flush=True)
 finally:
  if '--keep-open' not in sys.argv: browser(session,'close')
