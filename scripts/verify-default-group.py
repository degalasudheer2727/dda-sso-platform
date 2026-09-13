#!/usr/bin/env python3
"""Verify default enrollment; use a never-onboarded fixture for a first SSO test if available."""
import json,subprocess,sys,urllib.request,urllib.parse,uuid
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=json.loads((root/'.runtime/secrets.json').read_text())
body=urllib.parse.urlencode({'client_id':'admin-cli','grant_type':'password','username':'admin','password':s['KEYCLOAK_ADMIN_PASSWORD']}).encode()
r=urllib.request.Request('http://127.0.0.1:8080/realms/master/protocol/openid-connect/token',data=body,headers={'Host':'keycloak.localhost:8080'})
token=json.load(urllib.request.urlopen(r,timeout=20))['access_token']
def api(path,method='GET',data=None):
 r=urllib.request.Request('http://127.0.0.1:8080/admin/realms/dda'+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers={'Host':'keycloak.localhost:8080','Authorization':'Bearer '+token,'Content-Type':'application/json'})
 with urllib.request.urlopen(r,timeout=30) as response:
  raw=response.read();return json.loads(raw) if raw else None
groups={g['name']:g for g in api('/groups')}
assert 'openweb-users' not in groups
assert {g['name'] for g in api('/default-groups')}=={'openwebui-users'}
def verify(uid):
 memberships=api('/users/'+uid+'/groups')
 assert 'openwebui-users' in {g['name'] for g in memberships}
 roles={r['name'] for r in api('/users/'+uid+'/role-mappings/realm/composite')}
 assert 'webui-user' in roles and 'webui-admin' not in roles
# No group assignment in this create request: Keycloak must apply its default.
email='default-enrollment-'+uuid.uuid4().hex[:10]+'@dda.test'
uid=None
try:
 api('/users','POST',{'username':email,'email':email,'enabled':True})
 uid=api('/users?email='+urllib.parse.quote(email)+'&exact=true')[0]['id'];verify(uid)
 print('PASS: newly created user automatically inherits openwebui-users and webui-user.',flush=True)
finally:
 if uid:api('/users/'+uid,'DELETE')
# First real broker sign-in when a synthetic fixture is absent from both systems.
code="import sqlite3,json; c=sqlite3.connect('/app/backend/data/webui.db'); print(json.dumps([r[0] for r in c.execute(\"select email from user where email like 'testuser%@dda.test'\")]))"
existing_app=set(json.loads(subprocess.check_output(['docker','exec','open-webui','python','-c',code])))
first=None
for fixture in s['users']:
 if fixture['email'] not in existing_app and not api('/users?email='+urllib.parse.quote(fixture['email'])+'&exact=true'):
  first=fixture;break
if first:
 subprocess.run([sys.executable,str(root/'scripts/onboard-test-users.py'),'--user',first['username'],'--username'],check=True)
 uid=api('/users?email='+urllib.parse.quote(first['email'])+'&exact=true')[0]['id'];verify(uid)
 print('PASS: first broker SSO login automatically enrolled '+first['username']+'.',flush=True)
else:print('No unused fixture: default enrollment verified with a temporary new Keycloak user; existing accounts preserved.')
(root/'verification/default-group-results.json').write_text(json.dumps({'defaultGroup':'openwebui-users','legacyGroupAbsent':True,'newUserInheritedRole':'webui-user','temporaryProbeRemoved':True,'firstBrokerFixture':first['username'] if first else None},indent=2)+'\n')
