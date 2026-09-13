#!/usr/bin/env python3
import json, urllib.request, urllib.parse, urllib.error, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=json.loads((root/'.runtime/secrets.json').read_text())
def request(path,data=None,token=None):
 headers={'Host':'keycloak.localhost:8080'}
 if token: headers['Authorization']='Bearer '+token
 r=urllib.request.Request('http://127.0.0.1:8080'+path,data=data,headers=headers)
 return json.load(urllib.request.urlopen(r,timeout=20))
body=urllib.parse.urlencode({'client_id':'admin-cli','grant_type':'password','username':'admin','password':s['KEYCLOAK_ADMIN_PASSWORD']}).encode()
token=request('/realms/master/protocol/openid-connect/token',body)['access_token']
users=request('/admin/realms/dda/users',token=token)
for u in s['users']:
 matches=[x for x in users if x.get('email')==u['email']]
 assert len(matches)==1,u['email']
 assert matches[0].get('firstName')==u['firstName'] and matches[0].get('lastName')==u['lastName'], matches[0].get('email')
 links=request('/admin/realms/dda/users/'+matches[0]['id']+'/federated-identity',token=token)
 assert any(x['identityProvider']=='dex' for x in links)
clients=request('/admin/realms/dda/clients?clientId=open-webui',token=token)
c=clients[0]; assert not c['publicClient'] and not c['directAccessGrantsEnabled']
assert c['redirectUris']==['http://webui.localhost:3000/oauth/oidc/callback']
assert c['attributes']['pkce.code.challenge.method']=='S256'
q=urllib.parse.urlencode({'client_id':'open-webui','response_type':'code','scope':'openid','redirect_uri':'http://invalid.example/callback'})
try: request('/realms/dda/protocol/openid-connect/auth?'+q); raise AssertionError('Invalid redirect was accepted')
except urllib.error.HTTPError as e: assert e.code==400,e.code
code="import sqlite3,json; c=sqlite3.connect('/app/backend/data/webui.db'); print(json.dumps(c.execute(\"select email,role from user where email like 'testuser%@dda.test'\").fetchall()))"
rows=json.loads(subprocess.check_output(['docker','exec','open-webui','python','-c',code]))
assert len(rows)==5 and all(role=='user' for _,role in rows)
admins=[u for u in users if u.get('email')==s['admin']['email']]
assert len(admins)==1
mgmt=request('/admin/realms/dda/clients?clientId=realm-management',token=token)[0]
roles=request('/admin/realms/dda/users/'+admins[0]['id']+'/role-mappings/clients/'+mgmt['id'],token=token)
assert any(r['name']=='realm-admin' for r in roles)
admin_code="import sqlite3; c=sqlite3.connect('/app/backend/data/webui.db'); print(c.execute(\"select role from user where email='admin@dda.test'\").fetchone()[0])"
assert subprocess.check_output(['docker','exec','open-webui','python','-c',admin_code]).decode().strip()=='admin'
report={'dedicated_admin':'admin@dda.test','admin_role_verified':True,'brokered_users':5,'all_federated_to':'dex','all_webui_roles':'user','client':'open-webui','realm':'dda','pkce':'S256','invalid_redirect_rejected':True,'complete_upstream_profiles':True}
(root/'verification/local-results.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: five broker links, five ordinary app users, confidential client, PKCE and redirect rejection.')
