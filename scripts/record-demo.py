#!/usr/bin/env python3
"""Record a synthetic-user SSO demo; password input remains masked in the video."""
import json,os,re,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
u=json.loads((root/'.runtime/secrets.json').read_text())['users'][0]
env=os.environ.copy();env['PATH']=str(root/'.runtime/browser-tools/node_modules/ffmpeg-static')+os.pathsep+env['PATH']
session='dda-record-final'
def run(*args):
 p=subprocess.run(['npx','--yes','agent-browser','--session',session,*args],capture_output=True,text=True,env=env,timeout=90)
 if p.returncode:raise RuntimeError(p.stderr or p.stdout)
 return p.stdout

def ref(s,label):
 for line in s.splitlines():
  if label in line:
   m=re.search(r'ref=(e\d+)',line)
   if m:return '@'+m.group(1)
 raise RuntimeError('Missing '+label)
run('open','http://webui.localhost:3000/auth')
run('record','start',str(root/'verification/user-sso-demo.webm'))
try:
 time.sleep(2)
 s=run('snapshot','-i');run('click',ref(s,'Continue with DDA SSO'))
 s=run('snapshot','-i');assert 'Username or email' in s
 time.sleep(2)
 run('fill',ref(s,'Username or email'),u['email']);run('fill',ref(s,'textbox "Password"'),u['password'])
 run('click',ref(s,'button "Login"'));run('wait','--load','networkidle')
 assert run('get','url').strip()=='http://webui.localhost:3000/'
 time.sleep(3)
 run('open','http://keycloak.localhost:8080/realms/dda/account/');run('wait','--load','networkidle')
 assert 'Alex Morgan' in run('snapshot','-i')
 time.sleep(3)
finally:
 print(run('record','stop'));run('close')
print('Recorded direct upstream login, Open WebUI return, and account-console session reuse.')
