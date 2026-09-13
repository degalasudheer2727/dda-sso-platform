#!/usr/bin/env python3
"""Render local identity configuration. Existing generated secrets are never rotated."""
import json, os, secrets, subprocess, base64
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runtime'

def write(path, data, private=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n' if not isinstance(data, str) else data)
    if private: path.chmod(0o600)

def realm(dex_url, webui_url, s):
    result = {
      'realm':'dda','displayName':'DDA Enterprise SSO','enabled':True,
      'sslRequired':'external','registrationAllowed':False,'resetPasswordAllowed':False,
      'loginWithEmailAllowed':True,'duplicateEmailsAllowed':False,'bruteForceProtected':True,
      'accessTokenLifespan':300,'ssoSessionIdleTimeout':1800,'ssoSessionMaxLifespan':28800,
      'authenticationFlows':[{'alias':'dda-first-broker-login','description':'Provision unique upstream identity without a second profile form',
        'providerId':'basic-flow','topLevel':True,'builtIn':False,'authenticationExecutions':[
        {'authenticator':'idp-create-user-if-unique','authenticatorFlow':False,'requirement':'REQUIRED','priority':10,'userSetupAllowed':False}]}],
      'identityProviders':[{'alias':'dex','displayName':'DDA Test Identities','providerId':'oidc','enabled':True,
        'trustEmail':True,'storeToken':False,'firstBrokerLoginFlowAlias':'dda-first-broker-login',
        'config':{'clientId':'keycloak-dda','clientSecret':s['DEX_CLIENT_SECRET'],
          'authorizationUrl':dex_url+'/auth','tokenUrl':dex_url+'/token','userInfoUrl':dex_url+'/userinfo',
          'jwksUrl':dex_url+'/keys','issuer':dex_url,'validateSignature':'true','useJwksUrl':'true',
          'defaultScope':'openid email profile','syncMode':'FORCE','pkceEnabled':'true','pkceMethod':'S256'}}],
      'roles':{'realm':[{'name':'webui-user'},{'name':'webui-admin'}]},
      'defaultRoles':['webui-user'],
      'clients':[{'clientId':'open-webui','name':'DDA Open WebUI','enabled':True,'protocol':'openid-connect',
        'publicClient':False,'secret':s['WEBUI_CLIENT_SECRET'],'standardFlowEnabled':True,
        'directAccessGrantsEnabled':False,'serviceAccountsEnabled':False,
        'redirectUris':[webui_url+'/oauth/oidc/callback'],'webOrigins':[webui_url],
        'baseUrl':webui_url,'rootUrl':webui_url,
        'attributes':{'pkce.code.challenge.method':'S256','post.logout.redirect.uris':webui_url+'/*'},
        'defaultClientScopes':['web-origins','acr','roles','profile','email'],
        'optionalClientScopes':['address','phone','offline_access','microprofile-jwt'],
        'protocolMappers':[{'name':'webui-roles','protocol':'openid-connect','protocolMapper':'oidc-usermodel-realm-role-mapper',
          'config':{'claim.name':'roles','jsonType.label':'String','multivalued':'true','id.token.claim':'true','access.token.claim':'true','userinfo.token.claim':'true'}}]}]}

    if s.get('admin',{}).get('subject'):
      a=s['admin']
      result['users']=[{'username':a['email'],'email':a['email'],'firstName':a['firstName'],'lastName':a['lastName'],
        'enabled':True,'emailVerified':True,'realmRoles':['webui-user','webui-admin'],
        'clientRoles':{'realm-management':['realm-admin']},
        'federatedIdentities':[{'identityProvider':'dex','userId':a['subject'],'userName':a['username']}]}]
    return result

def dex_config(issuer, kc_url, s):
    return {'issuer':issuer, 'storage':{'type':'sqlite3','config':{'file':'/var/dex/dex.db'}},
      'web':{'http':'0.0.0.0:5556'},'telemetry':{'http':'0.0.0.0:5558'},
      'frontend':{'issuer':'DDA Test Identity Provider'},
      'oauth2':{'skipApprovalScreen':True},'enablePasswordDB':True,
      'staticClients':[{'id':'keycloak-dda','name':'Keycloak DDA Broker',
         'secret':s['DEX_CLIENT_SECRET'],'redirectURIs':[kc_url+'/realms/dda/broker/dex/endpoint']}],
      'staticPasswords':[{'email':u['email'],'hash':u['hash'],'username':u.get('name',u['username']),'userID':u['id']} for u in s['users']+([s['admin']] if s.get('admin') else [])]}

def main():
    os.umask(0o077); RUNTIME.mkdir(exist_ok=True)
    secret_file=RUNTIME/'secrets.json'
    if secret_file.exists(): s=json.loads(secret_file.read_text())
    else:
      s={key:secrets.token_urlsafe(32) for key in ['DEX_CLIENT_SECRET','WEBUI_CLIENT_SECRET','POSTGRES_PASSWORD','KEYCLOAK_ADMIN_PASSWORD','WEBUI_SECRET_KEY']}
      s['users']=[{'id':f'dda-test-{i:02d}','username':f'testuser{i:02d}','email':f'testuser{i:02d}@dda.test','password':secrets.token_urlsafe(14)} for i in range(1,6)]
      # Reuse the already installed image's bcrypt; no Python packages needed on the Mac.
      cmd=['docker','run','--rm','-i','--entrypoint','python','ghcr.io/open-webui/open-webui:v0.11.3','-c',
           'import bcrypt,json,sys; print(json.dumps([bcrypt.hashpw(p.encode(),bcrypt.gensalt()).decode() for p in json.load(sys.stdin)]))']
      hashes=json.loads(subprocess.check_output(cmd,input=json.dumps([u['password'] for u in s['users']]).encode()))
      for u,h in zip(s['users'],hashes): u['hash']=h
      write(secret_file,s,True)
    if 'admin' not in s:
      password=secrets.token_urlsafe(20)
      hashed=subprocess.check_output(['docker','run','--rm','-i','--entrypoint','python','ghcr.io/open-webui/open-webui:v0.11.3','-c','import bcrypt,sys; print(bcrypt.hashpw(sys.stdin.read().encode(),bcrypt.gensalt()).decode())'],input=password.encode()).decode().strip()
      s['admin']={'id':'dda-admin','username':'admin','email':'admin@dda.test','name':'DDA Administrator','firstName':'DDA','lastName':'Administrator','password':password,'hash':hashed}
    # Dex v2.45.1 local connector subject: base64url of protobuf user_id/connector_id.
    s['admin'].setdefault('subject',base64.urlsafe_b64encode(b'\x0a\x09dda-admin\x12\x05local').decode().rstrip('='))
    if 'WEBUI_BOOTSTRAP_PASSWORD' not in s: s['WEBUI_BOOTSTRAP_PASSWORD']=secrets.token_urlsafe(32)
    if 'POSTGRES_ADMIN_PASSWORD' not in s: s['POSTGRES_ADMIN_PASSWORD']=secrets.token_urlsafe(32)
    names=['Alex Morgan','Jamie Parker','Taylor Reed','Jordan Blake','Casey Brooks']
    for u,name in zip(s['users'],names):
      u['name']=name; u['firstName'],u['lastName']=name.split(' ',1)
    write(secret_file,s,True)
    d='http://dex.localhost:5556/dex'; k='http://keycloak.localhost:8080'; w='http://webui.localhost:3000'
    write(RUNTIME/'dex/config.yaml',dex_config(d,k,s),True)
    r=realm(d,w,s); r['sslRequired']='none' # localhost demo only; OpenShift uses external HTTPS.
    write(RUNTIME/'keycloak/dda-realm.json',r,True)
    # Container runtime config must be readable by its non-root user, inside private .runtime directory.
    for p in [RUNTIME/'dex/config.yaml',RUNTIME/'keycloak/dda-realm.json']: p.chmod(0o644)
    write(RUNTIME/'identity.env','\n'.join(f'{k}={v}' for k,v in s.items() if isinstance(v,str))+'\n',True)
    rows=['# Local demo credentials — do not commit or reuse in production','',
          'Keycloak admin: `admin` / `'+s['KEYCLOAK_ADMIN_PASSWORD']+'`','',
          '| Dex identity | Full name | Email | Password |','|---|---|---|---|']
    rows += [f"| {u['username']} | {u['name']} | {u['email']} | `{u['password']}` |" for u in s['users']]
    write(RUNTIME/'TEST-USERS.md','\n'.join(rows)+'\n',True)
    write(RUNTIME/'ADMIN-ACCESS.md', '# Local administration\n\n| Service | Account | Password / method |\n|---|---|---|\n'+f"| Keycloak master console | admin | `{s['KEYCLOAK_ADMIN_PASSWORD']}` |\n| Dex upstream admin identity | admin@dda.test | `{s['admin']['password']}` |\n| Keycloak dda / Open WebUI | admin@dda.test | Sign in through Dex with the password above |\n| Web UI local break-glass (fresh DB) | webui-bootstrap@dda.test | `{s['WEBUI_BOOTSTRAP_PASSWORD']}` |\n| PostgreSQL | postgres | `{s['POSTGRES_ADMIN_PASSWORD']}` (internal network only) |\n"+'\nDex configuration administration is file/Git-based; its admin identity is for downstream SSO. Headroom has no application admin users and remains loopback-only. Existing Open WebUI administrators are preserved.\n',True)
    print('Rendered .runtime configuration and TEST-USERS.md; existing secrets preserved.')
if __name__=='__main__': main()
