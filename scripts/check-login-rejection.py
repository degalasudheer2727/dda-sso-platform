#!/usr/bin/env python3
"""Verify the demo username adapter does not bypass password validation."""
import subprocess, re, os
def browser(session,*args):
 r=subprocess.run(([os.environ['AGENT_BROWSER_BIN']] if os.environ.get('AGENT_BROWSER_BIN') else ['npx','--yes','agent-browser'])+['--session',session,*args],capture_output=True,text=True,timeout=60)
 if r.returncode: raise RuntimeError(r.stderr.strip() or r.stdout.strip())
 return r.stdout

def ref(snapshot,label):
 for line in snapshot.splitlines():
  if label in line:
   m=re.search(r'ref=(e\d+)',line)
   if m: return '@'+m.group(1)
 raise RuntimeError('Missing UI control: '+label+'\n'+snapshot)

session='dda-login-rejection'
try:
 for username in ['testuser01','unknown-demo-user']:
  browser(session,'open','http://webui.localhost:3000/auth')
  snap=browser(session,'snapshot','-i');browser(session,'click',ref(snap,'Continue with DDA SSO'))
  snap=browser(session,'snapshot','-i')
  browser(session,'fill',ref(snap,'Username or email'),username)
  browser(session,'fill',ref(snap,'textbox "Password"'),'deliberately-invalid-demo-password')
  browser(session,'click',ref(snap,'button "Login"'))
  snap=browser(session,'snapshot')
  assert 'Invalid Username or email and password.' in snap,'Expected password rejection'
 print('PASS: wrong password and unknown username rejected.')
finally:
 browser(session,'close')
