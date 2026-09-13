#!/usr/bin/env python3
"""Explicit local fixture recovery after Keycloak users are deleted/recreated.
Only repairs known demo identities after checking their stable Dex subject.
Preserves WebUI IDs/data; never enables automatic email-based account merging.
"""
import base64,json,subprocess,urllib.request,urllib.parse
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=json.loads((root/'.runtime/secrets.json').read_text())
def call(path,method='GET',data=None):
 headers={'Host':'keycloak.localhost:8080'}
 if 'token' in globals(): headers['Authorization']='Bearer '+token
 if data is not None: headers['Content-Type']='application/json'
 with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8080'+path,headers=headers,method=method,data=json.dumps(data).encode() if data is not None else None),timeout=30) as r:
  raw=r.read();return json.loads(raw) if raw else None
body=urllib.parse.urlencode({'client_id':'admin-cli','grant_type':'password','username':'admin','password':s['KEYCLOAK_ADMIN_PASSWORD']}).encode()
r=urllib.request.Request('http://127.0.0.1:8080/realms/master/protocol/openid-connect/token',data=body,headers={'Host':'keycloak.localhost:8080'})
token=json.load(urllib.request.urlopen(r))['access_token']
read="import sqlite3,json; c=sqlite3.connect('/app/backend/data/webui.db'); print(json.dumps(c.execute('select id,email,oauth from user').fetchall()))"
rows=json.loads(subprocess.check_output(['docker','run','--rm','--network','none','-v','open-webui:/app/backend/data:ro','--entrypoint','python','ghcr.io/open-webui/open-webui:v0.11.3','-c',read]))
updates=[]
for u in s['users']:
 app=[x for x in rows if x[1]==u['email']];assert len(app)==1,'Expected one existing fixture account'
 oauth=json.loads(app[0][2]);old=oauth['oidc']['sub']
 uid=u['id'].encode();subject=base64.urlsafe_b64encode(bytes([10,len(uid)])+uid+b'\x12\x05local').decode().rstrip('=')
 found=call('/admin/realms/dda/users?email='+urllib.parse.quote(u['email'])+'&exact=true')
 if not found:
  call('/admin/realms/dda/users','POST',{'id':old,'username':u['email'],'email':u['email'],'emailVerified':True,'enabled':True,'firstName':u['firstName'],'lastName':u['lastName'],'groups':['/openweb-users'],'federatedIdentities':[{'identityProvider':'dex','userId':subject,'userName':u['name']}]})
  found=call('/admin/realms/dda/users?email='+urllib.parse.quote(u['email'])+'&exact=true')
 assert len(found)==1
 kc=found[0];links=call('/admin/realms/dda/users/'+kc['id']+'/federated-identity')
 assert any(x['identityProvider']=='dex' and x['userId']==subject for x in links),'Dex subject mismatch; refusing repair'
 oauth['oidc']['sub']=kc['id'];updates.append([json.dumps(oauth),app[0][0],app[0][2]])
# Stop for an atomic SQLite backup and compare-and-swap updates, then restart.
subprocess.run(['docker','stop','open-webui'],check=True,stdout=subprocess.DEVNULL)
try:
 code="""import sqlite3,json,sys,time
c=sqlite3.connect('/data/webui.db'); backup=sqlite3.connect('/data/webui.db.before-link-repair-'+str(time.time_ns()));c.backup(backup);backup.close()
with c:
 for value,uid,old in json.load(sys.stdin):
  assert c.execute('update user set oauth=? where id=? and oauth=?',(value,uid,old)).rowcount==1
print('PASS: five verified Dex identity links reconciled; WebUI data preserved.')
"""
 subprocess.run(['docker','run','--rm','-i','--network','none','-v','open-webui:/data','--entrypoint','python','ghcr.io/open-webui/open-webui:v0.11.3','-c',code],input=json.dumps(updates),text=True,check=True)
finally: subprocess.run(['docker','start','open-webui'],check=True,stdout=subprocess.DEVNULL)
