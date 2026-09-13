#!/usr/bin/env python3
"""Check deployment relationships/security intent, without requiring a live cluster."""
import json, pathlib, sys
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'openshift/reference')
k=json.loads((root/'kustomization.yaml').read_text())
objs=[json.loads((root/f).read_text()) for f in k['resources']]
assert len({(o['kind'],o['metadata']['name']) for o in objs})==len(objs)
bykind=lambda kind:[o for o in objs if o['kind']==kind]
svcs={o['metadata']['name'] for o in bykind('Service')}
pvcs={o['metadata']['name'] for o in bykind('PersistentVolumeClaim')}
secret_names={o['metadata']['name'] for o in bykind('Secret')}
for d in bykind('Deployment'):
 pod=d['spec']['template']['spec']; assert not pod['automountServiceAccountToken']
 assert pod['securityContext']['runAsNonRoot']; assert 'runAsUser' not in pod['securityContext']
 for c in pod['containers']:
  assert not c['securityContext']['allowPrivilegeEscalation']
  assert c['securityContext']['capabilities']['drop']==['ALL']
  assert all(x in c for x in ['readinessProbe','startupProbe','livenessProbe','resources'])
  for e in c['env']:
   if 'valueFrom' in e: assert e['valueFrom']['secretKeyRef']['name'] in secret_names
 for v in pod['volumes']:
  if 'persistentVolumeClaim' in v: assert v['persistentVolumeClaim']['claimName'] in pvcs
for r in bykind('Route'):
 assert r['spec']['to']['name'] in svcs
 assert r['spec']['tls']['insecureEdgeTerminationPolicy']=='Redirect'
realm=json.loads(next(o for o in bykind('Secret') if o['metadata']['name']=='keycloak-realm')['stringData']['dda-realm.json'])
assert realm['identityProviders'][0]['firstBrokerLoginFlowAlias']=='dda-first-broker-login'
assert realm['identityProviders'][0]['config']['syncMode']=='FORCE'
flow=realm['authenticationFlows'][0]
assert flow['authenticationExecutions'][0]['authenticator']=='idp-create-user-if-unique'
assert all(e.get('authenticator')!='idp-review-profile' for e in flow['authenticationExecutions'])
groups={g['name']:set(g['realmRoles']) for g in realm['groups']}
assert realm['defaultGroups']==['/openwebui-users']
assert groups=={'openwebui-users':{'webui-user'},'openwebui-admins':{'webui-user','webui-admin'}}
assert not set(realm.get('defaultRoles',[])) & {'webui-user','webui-admin'}
webui=next(o for o in bykind('Deployment') if o['metadata']['name']=='open-webui')
values={e['name']:e.get('value') for e in webui['spec']['template']['spec']['containers'][0]['env']}
assert json.loads(values['OAUTH_AUTHORIZE_PARAMS'])=={'kc_idp_hint':'dex'}
assert values['ENABLE_LOGIN_FORM']=='false'
assert 'WEBUI_ADMIN_PASSWORD' in values
assert realm['realm']=='dda' and realm['sslRequired']=='external'
c=realm['clients'][0]; assert not c['publicClient'] and not c['directAccessGrantsEnabled']
assert c['attributes']['pkce.code.challenge.method']=='S256'
assert len(c['redirectUris'])==1 and '*' not in c['redirectUris'][0]
print(f'PASS: {len(objs)} resources; references, HTTPS, PKCE, secrets, PVCs, probes, and restricted security settings.')
