#!/usr/bin/env python3
"""Reconcile the local demo broker/client and complete profiles via Keycloak Admin API."""
import json, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from bootstrap import realm
root=Path(__file__).resolve().parents[1]
s=json.loads((root/'.runtime/secrets.json').read_text())
def call(path, method='GET', data=None, form=False):
 headers={'Host':'keycloak.localhost:8080'}
 if 'token' in globals(): headers['Authorization']='Bearer '+token
 payload=None
 if data is not None:
  payload=(urllib.parse.urlencode(data) if form else json.dumps(data)).encode()
  headers['Content-Type']='application/x-www-form-urlencoded' if form else 'application/json'
 r=urllib.request.Request('http://127.0.0.1:8080'+path,data=payload,headers=headers,method=method)
 with urllib.request.urlopen(r,timeout=30) as response:
  raw=response.read(); return json.loads(raw) if raw else None

token=call('/realms/master/protocol/openid-connect/token','POST',{'client_id':'admin-cli','grant_type':'password','username':'admin','password':s['KEYCLOAK_ADMIN_PASSWORD']},True)['access_token']
b='/admin/realms/dda'; alias='dda-first-broker-login'
flows=call(b+'/authentication/flows')
if not any(f['alias']==alias for f in flows):
 call(b+'/authentication/flows','POST',{'alias':alias,'providerId':'basic-flow','topLevel':True,'builtIn':False,'description':'Provision unique upstream identity without a second profile form'})
 call(b+'/authentication/flows/'+alias+'/executions/execution','POST',{'provider':'idp-create-user-if-unique'})
for ex in call(b+'/authentication/flows/'+alias+'/executions'):
 if ex.get('providerId')=='idp-create-user-if-unique':
  ex['requirement']='REQUIRED';call(b+'/authentication/flows/'+alias+'/executions','PUT',ex)
r=realm('http://dex.localhost:5556/dex','http://webui.localhost:3000',s)
call(b+'/identity-provider/instances/dex','PUT',r['identityProviders'][0])
for fixture in s['users']+([s['admin']] if s.get('admin') else []):
 users=call(b+'/users?email='+urllib.parse.quote(fixture['email'])+'&exact=true')
 for u in users:
  if u['email']==fixture['email']:
   u.update(firstName=fixture['firstName'],lastName=fixture['lastName'],emailVerified=True)
   call(b+'/users/'+u['id'],'PUT',u)
print('Reconciled direct provisioning flow, forced upstream profile sync, and five complete profiles.')

if s.get('admin'):
 admins=call(b+'/users?email='+urllib.parse.quote(s['admin']['email'])+'&exact=true')
 if admins:
  management=call(b+'/clients?clientId=realm-management')[0]
  role=call(b+'/clients/'+management['id']+'/roles/realm-admin')
  call(b+'/users/'+admins[0]['id']+'/role-mappings/clients/'+management['id'],'POST',[role])
  print('Dedicated SSO administrator granted dda realm administration.')

for name in ['webui-user','webui-admin']:
 try: call(b+'/roles/'+name)
 except urllib.error.HTTPError as e:
  if e.code!=404: raise
  call(b+'/roles','POST',{'name':name})
# Authorization comes from groups, not realm-wide defaults or fixture direct roles.
from keycloak_groups import reconcile_groups
groups=reconcile_groups(call,b,r['groups'])
for fixture in s['users']+([s['admin']] if s.get('admin') else []):
 found=call(b+'/users?email='+urllib.parse.quote(fixture['email'])+'&exact=true')
 if found:
  uid=found[0]['id']
  group='openwebui-admins' if fixture.get('username')=='admin' else 'openwebui-users'
  # Seed a group only on migration. Preserve administrators' later membership decisions.
  memberships=call(b+'/users/'+uid+'/groups')
  direct=call(b+'/users/'+uid+'/role-mappings/realm')
  legacy=[role for role in direct if role['name'] in ['webui-user','webui-admin']]
  if legacy or not fixture.get('group_migrated'):
   call(b+'/users/'+uid+'/groups/'+groups[group]['id'],'PUT')
   fixture['group_migrated']=True
  if legacy: call(b+'/users/'+uid+'/role-mappings/realm','DELETE',legacy)
default=call(b)['defaultRole']['name']
call(b+'/roles/'+default+'/composites','DELETE',[call(b+'/roles/webui-user'),call(b+'/roles/webui-admin')])
(root/'.runtime/secrets.json').write_text(json.dumps(s,indent=2)+'\n')
print('Reconciled openwebui-users and openwebui-admins group role inheritance.')
client=call(b+'/clients?clientId=open-webui')[0]
mapper=r['clients'][0]['protocolMappers'][0]
existing=call(b+'/clients/'+client['id']+'/protocol-mappers/models')
found=next((m for m in existing if m['name']==mapper['name']),None)
if found:
 mapper['id']=found['id'];call(b+'/clients/'+client['id']+'/protocol-mappers/models/'+found['id'],'PUT',mapper)
else: call(b+'/clients/'+client['id']+'/protocol-mappers/models','POST',mapper)
print('Synchronized explicit Web UI user/admin role claims.')
# Preserve the stable Dex federated subject for first-boot demo realm imports.
if s.get('admin'):
 admins=call(b+'/users?email='+urllib.parse.quote(s['admin']['email'])+'&exact=true')
 if admins:
  links=call(b+'/users/'+admins[0]['id']+'/federated-identity')
  link=next((x for x in links if x['identityProvider']=='dex'),None)
  if link:
   s['admin']['subject']=link['userId']
   (root/'.runtime/secrets.json').write_text(json.dumps(s,indent=2)+'\n')
