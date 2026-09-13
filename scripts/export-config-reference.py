#!/usr/bin/env python3
"""Export an allowlisted, credential-free reference from the running local lab.
Never exports tokens, signing keys, password hashes, or arbitrary user records.
"""
import datetime,json,subprocess,urllib.request,urllib.parse
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=json.loads((root/'.runtime/secrets.json').read_text())
body=urllib.parse.urlencode({'client_id':'admin-cli','grant_type':'password','username':'admin','password':s['KEYCLOAK_ADMIN_PASSWORD']}).encode()
r=urllib.request.Request('http://127.0.0.1:8080/realms/master/protocol/openid-connect/token',data=body,headers={'Host':'keycloak.localhost:8080'})
token=json.load(urllib.request.urlopen(r,timeout=20))['access_token']
def get(path):
 r=urllib.request.Request('http://127.0.0.1:8080/admin/realms/dda'+path,headers={'Host':'keycloak.localhost:8080','Authorization':'Bearer '+token})
 return json.load(urllib.request.urlopen(r,timeout=20))
def pick(obj,keys):return {k:obj[k] for k in keys.split() if k in obj}
r=get('');client=get('/clients?clientId=open-webui')[0];broker=get('/identity-provider/instances/dex')
groups=[]
for g in get('/groups'):
 if g['name'] in ['openwebui-users','openwebui-admins']:
  groups.append({'name':g['name'],'roles':[v['name'] for v in get('/groups/'+g['id']+'/role-mappings/realm')]})
realm=pick(r,'realm displayName enabled sslRequired registrationAllowed resetPasswordAllowed loginWithEmailAllowed duplicateEmailsAllowed bruteForceProtected failureFactor waitIncrementSeconds maxFailureWaitSeconds failureResetTimeSeconds accessTokenLifespan ssoSessionIdleTimeout ssoSessionMaxLifespan')
client_ref=pick(client,'clientId name publicClient standardFlowEnabled directAccessGrantsEnabled implicitFlowEnabled serviceAccountsEnabled redirectUris webOrigins baseUrl rootUrl defaultClientScopes optionalClientScopes frontchannelLogout')
client_ref['attributes']=pick(client.get('attributes',{}),'pkce.code.challenge.method post.logout.redirect.uris')
client_ref['clientSecret']='[private: .runtime/secrets.json → WEBUI_CLIENT_SECRET]'
client_ref['roleMapper']=[{'name':m['name'],'type':m['protocolMapper'],'config':pick(m['config'],'claim.name jsonType.label multivalued id.token.claim access.token.claim userinfo.token.claim')} for m in get('/clients/'+client['id']+'/protocol-mappers/models') if m['name']=='webui-roles']
broker_ref=pick(broker,'alias displayName providerId enabled trustEmail storeToken firstBrokerLoginFlowAlias')
broker_ref['config']=pick(broker['config'],'clientId authorizationUrl tokenUrl userInfoUrl jwksUrl issuer validateSignature useJwksUrl defaultScope syncMode pkceEnabled pkceMethod')
broker_ref['config']['clientSecret']='[private: .runtime/secrets.json → DEX_CLIENT_SECRET]'
flow=get('/authentication/flows/dda-first-broker-login/executions')
flow_ref=[pick(e,'displayName providerId requirement level priority') for e in flow]
env=json.loads(subprocess.check_output(['docker','inspect','open-webui','--format','{{json .Config.Env}}']))
env=dict(v.split('=',1) for v in env)
web=pick(env,'WEBUI_URL OAUTH_CLIENT_ID OPENID_PROVIDER_URL OPENID_REDIRECT_URI OAUTH_PROVIDER_NAME OAUTH_SCOPES OAUTH_UPDATE_NAME_ON_LOGIN ENABLE_OAUTH_ROLE_MANAGEMENT OAUTH_ROLES_CLAIM OAUTH_ALLOWED_ROLES OAUTH_ADMIN_ROLES OAUTH_AUTHORIZE_PARAMS OAUTH_CODE_CHALLENGE_METHOD OAUTH_MERGE_ACCOUNTS_BY_EMAIL ENABLE_OAUTH_SIGNUP ENABLE_LOGIN_FORM DEFAULT_USER_ROLE OFFLINE_MODE HF_HUB_OFFLINE ENABLE_VERSION_UPDATE_CHECK OLLAMA_BASE_URL')
web['OAUTH_CLIENT_SECRET']='[private: .runtime/secrets.json → WEBUI_CLIENT_SECRET]'
web['WEBUI_SECRET_KEY']='[private: .runtime/secrets.json → WEBUI_SECRET_KEY]'
dex=json.loads((root/'.runtime/dex/config.yaml').read_text())
dex_ref=pick(dex,'issuer storage web telemetry frontend oauth2 enablePasswordDB')
dex_ref['identities']=[pick(u,'username email userID') for u in dex['staticPasswords']]
dex_ref['clients']=[dict(pick(c,'id name redirectURIs'),secret='[private: DEX_CLIENT_SECRET]') for c in dex['staticClients']]
report={'capturedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Local Mac runtime; allowlisted values only. OpenShift reference is separate.','keycloak':{'realm':realm,'broker':broker_ref,'client':client_ref,'groups':groups,'defaultGroups':[g['name'] for g in get('/default-groups')],'firstBrokerFlow':flow_ref},'openWebUI':{'environment':web,'uiNote':'Persisted User Access defaults can differ from DEFAULT_USER_ROLE. OAuth settings are environment-managed.'},'dex':dex_ref}
out=root/'docs/configuration';out.mkdir(parents=True,exist_ok=True)
(out/'local-effective-config.json').write_text(json.dumps(report,indent=2)+'\n')
print('Exported allowlisted local configuration; credentials represented by private references.')
