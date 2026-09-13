#!/usr/bin/env python3
"""Exercise local demo group promotion, demotion and denial; restore membership."""
import json,os,subprocess,sys,urllib.request,urllib.parse
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=json.loads((root/'.runtime/secrets.json').read_text())
body=urllib.parse.urlencode({'client_id':'admin-cli','grant_type':'password','username':'admin','password':s['KEYCLOAK_ADMIN_PASSWORD']}).encode()
r=urllib.request.Request('http://127.0.0.1:8080/realms/master/protocol/openid-connect/token',data=body,headers={'Host':'keycloak.localhost:8080'})
token=json.load(urllib.request.urlopen(r))['access_token']
def api(path,method='GET'):
 r=urllib.request.Request('http://127.0.0.1:8080/admin/realms/dda'+path,method=method,headers={'Host':'keycloak.localhost:8080','Authorization':'Bearer '+token})
 with urllib.request.urlopen(r,timeout=30) as response:
  raw=response.read();return json.loads(raw) if raw else None
groups={g['name']:g['id'] for g in api('/groups')}
uid=api('/users?email=testuser05%40dda.test&exact=true')[0]['id'];base='/users/'+uid+'/groups/'
original={g['id'] for g in api('/users/'+uid+'/groups')}
assert groups['openweb-users'] in original
assert not any(r['name'] in ['webui-user','webui-admin'] for r in api('/users/'+uid+'/role-mappings/realm'))
def login(role=None,denied=False):
 cmd=[sys.executable,str(root/'scripts/onboard-test-users.py'),'--user','testuser05','--username']
 if denied: cmd.append('--expect-denied')
 subprocess.run(cmd,check=True)
 if role:
  code="import sqlite3; c=sqlite3.connect('/app/backend/data/webui.db'); print(c.execute(\"select role from user where email='testuser05@dda.test'\").fetchone()[0])"
  assert subprocess.check_output(['docker','exec','open-webui','python','-c',code]).decode().strip()==role
  print('PASS: inherited Open WebUI role '+role,flush=True)
try:
 api(base+groups['openwebui-admins'],'PUT');login('admin')
 api(base+groups['openwebui-admins'],'DELETE');login('user')
 api(base+groups['openweb-users'],'DELETE');login(denied=True)
finally:
 current={g['id'] for g in api('/users/'+uid+'/groups')}
 for gid in current-original: api(base+gid,'DELETE')
 for gid in original-current: api(base+gid,'PUT')
 login('user')
print('PASS: group promotion, demotion, denial and original membership restored.')

(root/'verification/group-results.json').write_text(json.dumps({'groups':['openweb-users','openwebui-admins'],'promotion':'passed','demotion':'passed','unassigned_login':'denied','original_membership':'restored','applied_at':'SSO login'},indent=2)+'\n')
