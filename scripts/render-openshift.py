#!/usr/bin/env python3
"""Generate native OpenShift resources. JSON files are valid YAML/Kustomize inputs."""
import argparse, json, os, secrets, subprocess, sys
from pathlib import Path
from bootstrap import realm, dex_config, write, ROOT
p=argparse.ArgumentParser()
p.add_argument('--domain',required=True,help='Example: apps.enterprise.example')
p.add_argument('--registry',required=True,help='Example: registry.enterprise.example/dda')
p.add_argument('--namespace',default='dda-sso')
p.add_argument('--storage-class',default=None)
p.add_argument('--output',default='openshift/rendered')
p.add_argument('--with-demo-users',action='store_true',help='Include the five LOCAL demo identities (lab only).')
p.add_argument('--ca-bundle',help='PEM root/intermediate CA bundle for the enterprise Routes')
p.add_argument('--reference',action='store_true',help='Render safe placeholders for the committed reference manifests.')
a=p.parse_args(); os.umask(0o077)
out=ROOT/a.output; out.mkdir(parents=True,exist_ok=True)
secret_path=out/'deployment-secrets.json'
if a.reference:
 s={k:'REPLACE_WITH_GENERATED_SECRET' for k in ['DEX_CLIENT_SECRET','WEBUI_CLIENT_SECRET','POSTGRES_PASSWORD','KEYCLOAK_ADMIN_PASSWORD','WEBUI_SECRET_KEY','WEBUI_ADMIN_PASSWORD','POSTGRES_ADMIN_PASSWORD']}; s['users']=[]
elif secret_path.exists(): s=json.loads(secret_path.read_text())
else:
 s={k:secrets.token_urlsafe(32) for k in ['DEX_CLIENT_SECRET','WEBUI_CLIENT_SECRET','POSTGRES_PASSWORD','KEYCLOAK_ADMIN_PASSWORD','WEBUI_SECRET_KEY','WEBUI_ADMIN_PASSWORD','POSTGRES_ADMIN_PASSWORD']}
 s['users']=[]
 if a.with_demo_users: s['users']=json.loads((ROOT/'.runtime/secrets.json').read_text())['users']
 write(secret_path,s,True)
if 'POSTGRES_ADMIN_PASSWORD' not in s: s['POSTGRES_ADMIN_PASSWORD']=secrets.token_urlsafe(32)
if 'WEBUI_ADMIN_PASSWORD' not in s:
 s['WEBUI_ADMIN_PASSWORD','POSTGRES_ADMIN_PASSWORD']=secrets.token_urlsafe(32); write(secret_path,s,True)
if not a.reference:
 s['users']=json.loads((ROOT/'.runtime/secrets.json').read_text())['users'] if a.with_demo_users else []
 if a.with_demo_users: s['admin']=json.loads((ROOT/'.runtime/secrets.json').read_text()).get('admin')
 else: s.pop('admin',None)
 write(secret_path,s,True)
ns=a.namespace; dex='https://dex.'+a.domain+'/dex'; kc='https://keycloak.'+a.domain; web='https://webui.'+a.domain
imgs={'dex':a.registry+'/dex:v2.45.1','keycloak':a.registry+'/keycloak-dda:26.7.3','postgresql':a.registry+'/postgresql:16','open-webui':a.registry+'/open-webui-dda:v0.11.3'}
resources=[]
def save(component,name,obj):
 f=component+'/'+name+'.yaml'; write(out/f,obj,True); resources.append(f)
def meta(name,component): return {'name':name,'namespace':ns,'labels':{'app.kubernetes.io/part-of':'dda-sso','app.kubernetes.io/name':component}}
def secret(name,data,component): save(component,name,{'apiVersion':'v1','kind':'Secret','metadata':meta(name,component),'type':'Opaque','stringData':data})
def envs(d): return [{'name':k,'value':str(v)} for k,v in d.items()]
def secenv(name,key): return {'name':name,'valueFrom':{'secretKeyRef':{'name':'identity-secrets','key':key}}}
def service(name,port,component=None):
 component=component or name
 save(component,name+'-service',{'apiVersion':'v1','kind':'Service','metadata':meta(name,component),'spec':{'selector':{'app':name},'ports':[{'name':'http' if port!=5432 else 'postgres','port':port,'targetPort':port}]}})
def pvc(name,size,component):
 spec={'accessModes':['ReadWriteOnce'],'resources':{'requests':{'storage':size}}}
 if a.storage_class: spec['storageClassName']=a.storage_class
 save(component,name,{'apiVersion':'v1','kind':'PersistentVolumeClaim','metadata':meta(name,component),'spec':spec})
def route(name,host,port):
 save(name,name+'-route',{'apiVersion':'route.openshift.io/v1','kind':'Route','metadata':meta(name,name),
 'spec':{'host':host,'to':{'kind':'Service','name':name},'port':{'targetPort':'http'},
 'tls':{'termination':'edge','insecureEdgeTerminationPolicy':'Redirect'},'wildcardPolicy':'None'}})
def deployment(name,image,port,env,args,volumes,mounts,probe,mem='512Mi',cpu='250m'):
 container={'name':name,'image':image,'imagePullPolicy':'IfNotPresent','ports':[{'containerPort':port}],
 'env':env,'volumeMounts':mounts,'resources':{'requests':{'cpu':cpu,'memory':mem},'limits':{'memory':{'keycloak':'2Gi','open-webui':'3Gi'}.get(name,'1Gi')}},
 'securityContext':{'allowPrivilegeEscalation':False,'capabilities':{'drop':['ALL']},'runAsNonRoot':True},
 'readinessProbe':dict(probe,initialDelaySeconds=10,periodSeconds=10,timeoutSeconds=5),
 'livenessProbe':dict(probe,initialDelaySeconds=60,periodSeconds=20,timeoutSeconds=5),
 'startupProbe':dict(probe,failureThreshold=60,periodSeconds=10,timeoutSeconds=5)}
 if args: container['args']=args
 save(name,name+'-deployment',{'apiVersion':'apps/v1','kind':'Deployment','metadata':meta(name,name),
 'spec':{'replicas':1,'strategy':{'type':'Recreate'},'selector':{'matchLabels':{'app':name}},
 'template':{'metadata':{'labels':{'app':name,'app.kubernetes.io/part-of':'dda-sso'}},'spec':{
 'automountServiceAccountToken':False,'securityContext':{'runAsNonRoot':True,'seccompProfile':{'type':'RuntimeDefault'}},
 'containers':[container],'volumes':volumes,'terminationGracePeriodSeconds':60}}}})
def pv(n): return {'name':'data','persistentVolumeClaim':{'claimName':n}}
def mount(n,path): return {'name':n,'mountPath':path}
save('platform','namespace',{'apiVersion':'v1','kind':'Namespace','metadata':{'name':ns}})
secret('identity-secrets',{k:v for k,v in s.items() if isinstance(v,str)},'platform')
secret('dex-config',{'config.yaml':json.dumps(dex_config(dex,kc,s))},'dex')
secret('keycloak-realm',{'dda-realm.json':json.dumps(realm(dex,web,s))},'keycloak')
pvc('dex-data','1Gi','dex'); pvc('keycloak-db-data','10Gi','keycloak-db'); pvc('webui-data','10Gi','open-webui')
deployment('dex',imgs['dex'],5556,[],['dex','serve','/etc/dex/config.yaml'],
 [pv('dex-data'),{'name':'config','secret':{'secretName':'dex-config'}}],
 [mount('data','/var/dex'),dict(mount('config','/etc/dex'),readOnly=True)],{'httpGet':{'path':'/healthz','port':5558}},'128Mi','100m')
service('dex',5556); route('dex','dex.'+a.domain,5556)
pg_env=envs({'POSTGRESQL_USER':'keycloak','POSTGRESQL_DATABASE':'keycloak'})+[secenv('POSTGRESQL_PASSWORD','POSTGRES_PASSWORD'),secenv('POSTGRESQL_ADMIN_PASSWORD','POSTGRES_ADMIN_PASSWORD')]
deployment('keycloak-db',imgs['postgresql'],5432,pg_env,None,[pv('keycloak-db-data')],[mount('data','/var/lib/pgsql/data')],
 {'exec':{'command':['/bin/sh','-c','pg_isready -U keycloak -d keycloak']}},'256Mi','100m')
service('keycloak-db',5432)
k_env=envs({'KC_DB':'postgres','KC_DB_URL':'jdbc:postgresql://keycloak-db:5432/keycloak','KC_DB_USERNAME':'keycloak',
 'KC_HOSTNAME':kc,'KC_HTTP_ENABLED':'true','KC_PROXY_HEADERS':'xforwarded','KC_HEALTH_ENABLED':'true',
 'KC_BOOTSTRAP_ADMIN_USERNAME':'admin','JAVA_OPTS_KC_HEAP':'-Xms256m -Xmx1024m'})
k_env += [secenv('KC_DB_PASSWORD','POSTGRES_PASSWORD'),secenv('KC_BOOTSTRAP_ADMIN_PASSWORD','KEYCLOAK_ADMIN_PASSWORD')]
k_vol=[{'name':'realm','secret':{'secretName':'keycloak-realm'}},{'name':'data','emptyDir':{}}]
k_mount=[dict(mount('realm','/opt/keycloak/data/import'),readOnly=True),mount('data','/opt/keycloak/data')]
# Nested mounts: Kubernetes mounts data then the realm subdirectory.
w_env=envs({'WEBUI_URL':web,'OAUTH_CLIENT_ID':'open-webui','OPENID_PROVIDER_URL':kc+'/realms/dda/.well-known/openid-configuration',
 'OPENID_REDIRECT_URI':web+'/oauth/oidc/callback','OAUTH_PROVIDER_NAME':'DDA SSO','OAUTH_UPDATE_NAME_ON_LOGIN':'true','ENABLE_OAUTH_ROLE_MANAGEMENT':'true','OAUTH_ROLES_CLAIM':'roles','OAUTH_ALLOWED_ROLES':'webui-user,webui-admin','OAUTH_ADMIN_ROLES':'webui-admin','OAUTH_SCOPES':'openid email profile',
 'OAUTH_AUTHORIZE_PARAMS':json.dumps({'kc_idp_hint':'dex'}),'OAUTH_CODE_CHALLENGE_METHOD':'S256','ENABLE_OAUTH_SIGNUP':'true','ENABLE_LOGIN_FORM':'false',
 'OAUTH_MERGE_ACCOUNTS_BY_EMAIL':'false','DEFAULT_USER_ROLE':'user','WEBUI_ADMIN_EMAIL':'webui-admin@'+a.domain,'WEBUI_ADMIN_NAME':'DDA Bootstrap Admin','ENABLE_VERSION_UPDATE_CHECK':'false',
 'OFFLINE_MODE':'true','HF_HUB_OFFLINE':'1','DO_NOT_TRACK':'true','ANONYMIZED_TELEMETRY':'false','HOME':'/tmp'})
w_env += [secenv('OAUTH_CLIENT_SECRET','WEBUI_CLIENT_SECRET'),secenv('WEBUI_SECRET_KEY','WEBUI_SECRET_KEY'),secenv('WEBUI_ADMIN_PASSWORD','WEBUI_ADMIN_PASSWORD')]
w_vol=[pv('webui-data')]; w_mount=[mount('data','/app/backend/data')]
if a.ca_bundle:
 ca=Path(a.ca_bundle).read_text()
 save('platform','enterprise-ca',{'apiVersion':'v1','kind':'ConfigMap','metadata':meta('enterprise-ca','platform'),'data':{'ca.crt':ca}})
 for vols,mounts in [(k_vol,k_mount),(w_vol,w_mount)]:
  vols.append({'name':'enterprise-ca','configMap':{'name':'enterprise-ca'}}); mounts.append(dict(mount('enterprise-ca','/etc/enterprise-ca'),readOnly=True))
 k_env += envs({'KC_TRUSTSTORE_PATHS':'/etc/enterprise-ca/ca.crt'})
 w_env += envs({'SSL_CERT_FILE':'/etc/enterprise-ca/ca.crt','REQUESTS_CA_BUNDLE':'/etc/enterprise-ca/ca.crt'})
deployment('keycloak',imgs['keycloak'],8080,k_env,['start','--optimized','--import-realm'],k_vol,k_mount,
 {'httpGet':{'path':'/health/ready','port':9000}},'768Mi','500m')
service('keycloak',8080); route('keycloak','keycloak.'+a.domain,8080)
deployment('open-webui',imgs['open-webui'],8080,w_env,None,w_vol,w_mount,{'httpGet':{'path':'/health','port':8080}},'1Gi','500m')
service('open-webui',8080); route('open-webui','webui.'+a.domain,8080)
# Default deny ingress and egress. Explicitly allow only DNS, internal DB, and HTTPS Routes.
save('platform','default-deny',{'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':meta('default-deny','platform'),
 'spec':{'podSelector':{},'policyTypes':['Ingress','Egress']}})
for app,port in [('dex',5556),('keycloak',8080),('open-webui',8080)]:
 save(app,'allow-router',{'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':meta(app+'-allow-router',app),
 'spec':{'podSelector':{'matchLabels':{'app':app}},'policyTypes':['Ingress'],
 'ingress':[{'from':[{'namespaceSelector':{'matchLabels':{'network.openshift.io/policy-group':'ingress'}}}], 'ports':[{'protocol':'TCP','port':port}]}]}})
save('keycloak-db','allow-keycloak',{'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':meta('db-from-keycloak','keycloak-db'),
 'spec':{'podSelector':{'matchLabels':{'app':'keycloak-db'}},'policyTypes':['Ingress'],'ingress':[{'from':[{'podSelector':{'matchLabels':{'app':'keycloak'}}}],'ports':[{'port':5432,'protocol':'TCP'}]}]}})
save('platform','allow-dns',{'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':meta('allow-dns','platform'),
 'spec':{'podSelector':{},'policyTypes':['Egress'],'egress':[{'to':[{'namespaceSelector':{'matchLabels':{'kubernetes.io/metadata.name':'openshift-dns'}}}],'ports':[{'port':5353,'protocol':'UDP'},{'port':5353,'protocol':'TCP'},{'port':53,'protocol':'UDP'},{'port':53,'protocol':'TCP'}]}]}})
save('keycloak','allow-db',{'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':meta('keycloak-to-db','keycloak'),
 'spec':{'podSelector':{'matchLabels':{'app':'keycloak'}},'policyTypes':['Egress'],'egress':[{'to':[{'podSelector':{'matchLabels':{'app':'keycloak-db'}}}],'ports':[{'port':5432,'protocol':'TCP'}]}]}})
# HTTPS Route hairpin: external VIPs/host-network routers need ipBlock rules tailored by operator.
for app in ['keycloak','open-webui']:
 save(app,'allow-route-https',{'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':meta(app+'-route-https',app),
 'spec':{'podSelector':{'matchLabels':{'app':app}},'policyTypes':['Egress'],'egress':[{'ports':[{'port':443,'protocol':'TCP'}]}]}})
write(out/'kustomization.yaml',{'apiVersion':'kustomize.config.k8s.io/v1beta1','kind':'Kustomization','resources':resources})
write(out/'DEPLOYMENT.txt',f'Namespace: {ns}\nDex: {dex}\nKeycloak: {kc}\nOpen WebUI: {web}\nSecret file: deployment-secrets.json (private)\n')
print(f'Rendered {len(resources)} native resources at {out}; no cluster was modified.')
