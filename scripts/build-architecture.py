#!/usr/bin/env python3
"""Generate editable Draw.io pages and matching SVG previews using only stdlib."""
from pathlib import Path
import xml.etree.ElementTree as E
import html, textwrap
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'architecture'; OUT.mkdir(exist_ok=True)
C={'ink':'#172B4D','muted':'#51647E','blue':'#1764C0','cyan':'#087E8B','purple':'#7146B8','green':'#18794E','amber':'#A15C00','red':'#B33B45','line':'#AFC0D4','paper':'#F4F7FC'}
mx=E.Element('mxfile',host='app.diagrams.net',type='device',version='24.7.17')
class Page:
 def __init__(self,name,slug,w=2200,h=1500):
  self.name=name;self.slug=slug;self.w=w;self.h=h;self.nodes={};self.items=[];self.edges=[]
  d=E.SubElement(mx,'diagram',name=name,id=slug)
  self.g=E.SubElement(d,'mxGraphModel',dx=str(w),dy=str(h),grid='1',gridSize='10',page='1',pageScale='1',pageWidth=str(w),pageHeight=str(h),math='0',shadow='0')
  self.r=E.SubElement(self.g,'root');E.SubElement(self.r,'mxCell',id='0');E.SubElement(self.r,'mxCell',id='1',parent='0')
  self.text(name,55,40,w-110,55,32,C['ink'],bold=True)
 def text(self,t,x,y,w,h,size=16,color=None,bold=False):
  ident='text'+str(len(self.items));style=f'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;fontFamily=Helvetica;fontSize={size};fontColor={color or C["muted"]};fontStyle={1 if bold else 0};'
  cell=E.SubElement(self.r,'mxCell',id=ident,value=t,style=style,vertex='1',parent='1');E.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
  self.items.append(('text',t,x,y,w,h,size,color or C['muted'],bold))
 def box(self,id,title,lines,x,y,w,h,accent='blue',fill='#FFFFFF',size=17):
  # Fit every body into its card; keep SVG and Draw.io typography consistent.
  while size>13 and 63+sum(max(1,len(textwrap.wrap(l,max(15,int((w-36)/(size*.51)))))) for l in lines)*(size+7)>h-12:
   size-=1
  col=C.get(accent,accent);self.nodes[id]=(x,y,w,h)
  value='<b>'+html.escape(title)+'</b><br><br>'+'<br>'.join(html.escape(l) for l in lines)
  st=f'rounded=1;arcSize=10;html=1;whiteSpace=wrap;align=left;verticalAlign=top;spacing=18;fillColor={fill};strokeColor={col};strokeWidth=2;fontFamily=Helvetica;fontSize={size};fontColor={C["ink"]};'
  cell=E.SubElement(self.r,'mxCell',id=id,value=value,style=st,vertex='1',parent='1');E.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
  self.items.append(('box',id,title,lines,x,y,w,h,col,fill,size))
 def band(self,title,x,y,w,h,color='#EAF0F9'):
  self.box('band'+str(len(self.items)),title,[],x,y,w,h,'line',color,17)
 def edge(self,source,target,label='',color='blue',start='bottom',end='top',via=None,dash=False):
  col=C.get(color,color);p={'top':(.5,0),'bottom':(.5,1),'left':(0,.5),'right':(1,.5)};a,b=p[start],p[end]
  id='edge'+str(len(self.edges));sty=f'edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;strokeColor={col};strokeWidth=2;fontColor={col};fontSize=14;labelBackgroundColor=#FFFFFF;exitX={a[0]};exitY={a[1]};entryX={b[0]};entryY={b[1]};'+('dashed=1;' if dash else '')
  cell=E.SubElement(self.r,'mxCell',id=id,value=label,style=sty,edge='1',parent='1',source=source,target=target)
  geom=E.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})
  if via:
   arr=E.SubElement(geom,'Array',**{'as':'points'})
   for x,y in via:E.SubElement(arr,'mxPoint',x=str(x),y=str(y))
  self.edges.append((source,target,label,col,a,b,via,dash))
 def svg(self):
  f=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">', '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="context-stroke"/></marker></defs>',f'<rect width="100%" height="100%" fill="{C["paper"]}"/>']
  def line(t,x,y,size=16,col=C['ink'],weight='400'):
   f.append(f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" fill="{col}" font-weight="{weight}">{html.escape(t)}</text>')
  for item in self.items:
   if item[0]=='text':
    _,t,x,y,w,h,size,col,bold=item
    for i,l in enumerate(textwrap.wrap(t,max(15,int(w/(size*.52))))):line(l,x,y+size+i*(size+6),size,col,'700' if bold else '400')
   else:
    _,id,title,ls,x,y,w,h,col,fill,size=item
    f.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{col}" stroke-width="2"/>')
    line(title,x+18,y+31,size,col,'700');cy=y+63
    for l in ls:
     for part in textwrap.wrap(l,max(15,int((w-36)/(size*.51)))) or ['']:
      line(part,x+18,cy,size,C['ink']);cy+=size+7
  for source,target,label,col,a,b,via,dash in self.edges:
   x,y,w,h=self.nodes[source];start=(x+w*a[0],y+h*a[1]);x,y,w,h=self.nodes[target];end=(x+w*b[0],y+h*b[1])
   points=[start]+(via or [])+[end]
   if not via and start[0]!=end[0] and start[1]!=end[1]:points=[start,(start[0],end[1]),end]
   s=' '.join(f'{x},{y}' for x,y in points)
   f.append(f'<polyline points="{s}" fill="none" stroke="{col}" stroke-width="2.4" marker-end="url(#arrow)" '+('stroke-dasharray="7 5"' if dash else '')+'/>')
   if label:
    k=max(0,(len(points)-2)//2);pa,pb=points[k:k+2];lx=(pa[0]+pb[0])/2;ly=(pa[1]+pb[1])/2-9
    width=len(label)*7.5+16
    f.append(f'<rect x="{lx-width/2}" y="{ly-17}" width="{width}" height="23" rx="4" fill="#FFFFFF"/>')
    f.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="14" fill="{col}">{html.escape(label)}</text>')
  line('DDA • Deployed state and enterprise handoff • 14 September 2026 • No credentials embedded',55,self.h-25,14,C['muted'])
  f.append('</svg>');(OUT/(self.slug+'.svg')).write_text('\n'.join(f))

p=Page('01  |  Deployed Mac architecture','01-local',2200,1500)
p.text('RUNNING LOCALLY  •  Intel Mac / Docker Desktop  •  Direct Dex login through Keycloak brokerage',55,105,2050,40,19,C['green'])
p.band('HOST / BROWSER',45,170,380,780)
p.band('DOCKER NETWORK  openwebui_default  •  named DNS aliases  •  persistent containers',470,170,1240,810)
p.band('SOURCE & OPERATIONS',1750,170,405,1245)
p.box('browser','User and administrator browser',['Web UI: webui.localhost:3000','Click “Continue with DDA SSO”','Dex username-or-email login','No second profile form','Existing Keycloak session enables SSO'],65,245,340,245)
p.box('dns','Local address boundary',['*.localhost resolves to loopback','Docker aliases use identical names','Host ports bind 127.0.0.1 only','Local HTTP is a demo exception','Issuer names must match everywhere'],65,555,340,245,'amber','#FFF9ED')
p.box('webui','OPEN WEBUI  v0.11.3',['Container: open-webui','Host 3000 → container 8080','Client ID: open-webui','Issuer: Keycloak /realms/dda','OIDC code + PKCE S256','Roles: webui-user / webui-admin'],500,270,350,255)
p.box('kc','KEYCLOAK  26.7.3',['Container: dda-keycloak','Host/container port 8080','Realm: dda | broker alias: dex','Confidential broker client','JWKS + issuer validation','No review-profile / no auto-link'],920,270,350,255,'purple')
p.box('dex','DEX  v2.45.1',['Container: dda-dex','Host/container port 5556','Issuer: /dex','5 fully populated test profiles','1 dedicated admin identity','bcrypt local passwords'],1340,270,340,255,'cyan')
p.box('webvol','EXISTING APP DATA',['External volume: open-webui','Mount: /app/backend/data','SQLite, accounts, chats, uploads','Original administrator retained'],500,720,350,175,'green','#F0FAF5')
p.box('pg','POSTGRESQL  16',['Container: dda-keycloak-db','Internal port 5432 only','Database / app role: keycloak','Separate postgres administrator'],920,625,350,175,'green')
p.box('pgvol','DATABASE VOLUME',['openwebui_keycloak-db-data','Mount: /var/lib/pgsql/data','Realm, broker links, roles, sessions'],920,825,350,140,'green','#F0FAF5',15)
p.box('dexvol','DEX STATE',['Volume: openwebui_dex-data','Mount: /var/dex','SQLite: dex.db','Signing keys and session state'],1340,720,340,175,'green','#F0FAF5')
p.box('git','LOCAL GIT REPOSITORY',['Per-component folders + READMEs','Compose + bootstrap generators','27 native OpenShift resources','Editable Draw.io + SVG diagrams','Verification scripts / screenshots'],1775,240,355,245)
p.box('private','PRIVATE RUNTIME STATE',['.runtime/secrets.json','TEST-USERS.md / ADMIN-ACCESS.md','Client / database / admin secrets','Excluded from Git','No credentials in this diagram'],1775,525,355,225,'amber','#FFF9ED')
p.box('backup','BACKUP & OFFLINE TRANSFER',['Quiesce SQLite writers','pg_dump + Dex / Web UI copies','Restore requires separate drill','6.3 GB class Docker image archive','SHA256 checksum + image lock'],1775,790,355,240,'green','#F0FAF5')
p.box('validation','VERIFIED LOCALLY',['5 direct user logins + admin login','Admin Panel + realm-admin SSO','Ordinary users remain non-admin','Invalid OAuth redirect rejected','Restart persistence and backup','Open WebUI arbitrary UID healthy'],1775,1070,355,285,'green')
p.band('INDEPENDENT DEVELOPER UTILITY  •  not in the SSO trust chain',45,1005,1665,410)
p.box('codex','CODEX ON THE MAC',['Existing ChatGPT authentication','User config routes model requests','MCP retrieves compressed originals'],75,1100,410,180)
p.box('headroom','HEADROOM  v0.27.0',['headroom-proxy: localhost:8787','HTTP / WebSocket token compression','Loopback dashboard; no user admin','Separate headroom-data volume'],625,1100,430,200,'cyan')
p.box('provider','UPSTREAM LLM SERVICE',['Codex traffic forwarded upstream','Independent of Web UI SSO','Enterprise Web UI inference endpoint','must be configured separately'],1195,1100,470,200,'purple')
p.edge('browser','webui','Open WebUI','blue','right','left',via=[(450,367),(450,397)])
p.edge('webui','kc','code + PKCE','blue','right','left')
p.edge('kc','dex','OIDC broker','purple','right','left')
p.edge('webui','webvol','persistent data','green')
p.edge('kc','pg','JDBC / 5432','green')
p.edge('pg','pgvol','','green')
p.edge('dex','dexvol','keys + sessions','green')
p.edge('codex','headroom','localhost:8787','cyan','right','left')
p.edge('headroom','provider','provider HTTPS','purple','right','left')
p.svg()

p=Page('02  |  Seamless SSO and administrator authorization','02-sso',2200,1710)
p.text('BROWSER FRONT CHANNEL + VERIFIED SERVER BACK CHANNELS  •  authorization code flow  •  no password relay to Web UI',55,105,2090,50,18)
cols=[('b','BROWSER',65),('w','OPEN WEBUI',595),('k','KEYCLOAK / dda',1125),('d','DEX / local',1655)]
for id,title,x in cols:p.box(id,title,[],x,195,470,65,'purple' if id=='k' else 'blue','#EAF0F9')
steps=[
 ('s1','1. Begin SSO',['/oauth/oidc/login','State + nonce + PKCE challenge','kc_idp_hint=dex'],65,310,470,150),
 ('s2','2. Authorize at Keycloak',['/realms/dda/protocol/openid-connect/auth','Client: open-webui','Exact registered Web UI callback'],1125,310,470,150),
 ('s3','3. Direct upstream login',['Dex /dex/auth/local/login','Email + password entered only here','No Keycloak selection page'],1655,515,470,150),
 ('s4','4. Dex → Keycloak callback',['/realms/dda/broker/dex/endpoint','Code exchanged at Dex /token','Broker client: keycloak-dda'],1125,720,470,155),
 ('s5','5. Validate and provision',['Dex issuer + JWKS signature checked','Stable federated subject maps identity','Complete profile imported / FORCE sync','Unique-user flow; collisions fail'],1125,930,470,185),
 ('s6','6. Keycloak → Web UI callback',['/oauth/oidc/callback','Web UI redeems authorization code','Client secret + PKCE verifier','Validates Keycloak token / claims'],595,1170,470,185),
 ('s7','7. Application session',['Signed-in user lands in Open WebUI','No second profile/details form','Second Keycloak app reuses SSO'],65,1170,470,185)]
for id,t,ls,x,y,w,h in steps:p.box(id,t,ls,x,y,w,h,'cyan' if id=='s3' else 'blue')
p.edge('s1','s2','browser redirect + provider hint','blue','right','left',via=[(560,385),(1100,385)])
p.edge('s2','s3','automatic broker redirect','purple','right','top',via=[(1890,385)])
p.edge('s3','s4','authorization code','cyan','bottom','right',via=[(1890,797)])
p.edge('s4','s5','','purple')
p.edge('s5','s6','Keycloak authorization code','purple','bottom','right',via=[(1360,1262)])
p.edge('s6','s7','app session established','blue','left','right')
p.box('dexclaims','AUTHORITATIVE PROFILE',['email: testuser01@dda.test','name: Alex Morgan','Stable subject: test identity ID','Admin: admin@dda.test','No client secret exposed to browser'],1655,945,470,245,'cyan','#EFFBFB')
p.box('trust','TWO CONFIDENTIAL CLIENTS',['Dex client: keycloak-dda','Keycloak client: open-webui','Independent generated secrets','Strict issuer / signature validation','No password/direct grant on app client'],65,565,470,250,'amber','#FFF9ED')
p.box('roles','EXPLICIT AUTHORIZATION',['openwebui-users (default) → webui-user → user','openwebui-admins → webui-admin → admin','Admin also: realm-management/realm-admin','Master admin remains separate','No email-based automatic account merge'],65,865,1000,235,'green','#F0FAF5')
p.box('session','SESSION AND LOGOUT BOUNDARY',['Keycloak access token: 5 minutes • SSO idle: 30 minutes • SSO max: 8 hours','Ending the app / Keycloak session does not promise immediate revocation of every upstream session or issued JWT.','Enterprise logout, deprovisioning, MFA and expiry semantics must be validated with the actual upstream provider.'],65,1420,2060,205,'amber','#FFF9ED',18)
p.svg()

p=Page('03  |  Air-gapped OpenShift deployment reference','03-openshift',2400,1720)
p.text('GENERATED REFERENCE — NOT DEPLOYED TO A CLUSTER  •  Replace registry, DNS domain, storage class and CA placeholders',55,105,2290,50,19,C['amber'])
p.band('CONNECTED BUILD / CONTROLLED TRANSFER',45,180,485,1435)
p.box('build','APPROVED BUILD WORKSTATION',['Pinned Dex and PostgreSQL images','Keycloak optimized production image','Open WebUI arbitrary-UID derivative','No runtime pip / npm / Maven pulls','Match target CPU architecture'],70,260,435,245)
p.box('archive','OFFLINE IMAGE BUNDLE',['docker save → dda-images.tar','Transfer archive + SHA256 checksum','Transfer repository + oc / Podman','Keep credentials out of image layers','Scan / SBOM / sign final images'],70,565,435,245,'green')
p.box('registry','INTERNAL REGISTRY',['registry.<enterprise>/dda','Import/tag/push with Podman','Record destination manifest digests','Configure pull secret and registry CA'],70,875,435,205,'purple')
p.box('accept','PRODUCTION ACCEPTANCE GATES',['Actual OpenShift version / SCC admission','PVC provisioning and restore drill','TLS trust + Route hairpin DNS','NetworkPolicy / ingress topology','HA design + load/failure tests','Real IdP MFA / user lifecycle','Approved internal LLM + RAG tests'],70,1140,435,365,'amber','#FFF9ED')
p.band('ENTERPRISE OPENSHIFT CLUSTER  •  namespace dda-sso  •  restricted SCC',580,180,1760,1435)
p.box('route','HTTPS INGRESS ROUTES',['webui.<domain>  •  keycloak.<domain>  •  dex.<domain>','Edge TLS termination; HTTP redirected to HTTPS','Trusted ingress CA in browsers and OIDC back channels','Use re-encrypt Routes + pod certificates if full in-cluster TLS is required'],625,260,1665,175,'blue','#EDF4FF',18)
p.box('ow','OPEN WEBUI DEPLOYMENT',['Derived v0.11.3 image','Service port 8080','OAuth code + PKCE / role claims','Direct Dex provider hint','Offline downloads/version checks OFF','Separate bootstrap admin Secret'],625,540,490,270)
p.box('kc','KEYCLOAK DEPLOYMENT',['Optimized 26.7.3 image','start --optimized --import-realm','Service 8080; management 9000','KC_HOSTNAME=https://keycloak…','xforwarded behind trusted router','Realm import only on first DB boot'],1210,540,490,270,'purple')
p.box('dx','DEX DEPLOYMENT',['Pinned v2.45.1 image','Service 5556; health 5558','https://dex.<domain>/dex','Config mounted from a Secret','Demo profiles explicitly opt-in','Replace with enterprise connector'],1795,540,490,270,'cyan')
p.box('wv','WEB UI PVC',['10 Gi RWO /app/backend/data','SQLite + files → ONE replica','Recreate strategy'],625,935,490,155,'green','#F0FAF5')
p.box('db','POSTGRESQL DEPLOYMENT + PVC',['SCLorg PostgreSQL 16','Internal Service 5432','10 Gi RWO /var/lib/pgsql/data','keycloak app role / postgres DBA'],1210,920,490,205,'green','#F0FAF5')
p.box('dv','DEX PVC',['1 Gi RWO /var/dex','SQLite signing/session state','ONE replica / Recreate'],1795,935,490,155,'green','#F0FAF5')
p.box('security','SECURITY & NETWORK POLICIES',['No fixed UID, privileged mode, hostPath or anyuid SCC','runAsNonRoot; drop ALL; no privilege escalation; RuntimeDefault seccomp','Default deny → explicit ingress-router, DNS, Keycloak-to-DB paths','OIDC Route HTTPS egress: narrow to your actual VIPs/CIDRs','Separate generated client/database/admin Secrets; no secret values in Git'],625,1195,1010,290,'amber','#FFF9ED',17)
p.box('ops','RUNTIME OPERATIONS',['Startup / readiness / liveness probes','Resource requests and memory limits','No public health/DB admin ports','Central audit / monitoring integration','Storage snapshots + logical DB backups','Single-replica reference is NOT HA','HA storage design before scaling'],1690,1195,595,290,'green','#F0FAF5',17)
p.edge('build','archive','export','green');p.edge('archive','registry','controlled import','purple')
p.edge('route','ow','','blue','bottom','top',via=[(1457,475),(870,475)])
p.edge('route','kc','','purple','bottom','top')
p.edge('route','dx','','cyan','bottom','top',via=[(1457,475),(2040,475)])
p.edge('ow','wv','persistent app data','green');p.edge('kc','db','JDBC / 5432','green');p.edge('dx','dv','persistent signing state','green')
p.svg()

p=Page('04  |  Identity inventory and operational ownership','04-operations',2200,1490)
p.text('SIX UPSTREAM IDENTITIES  •  five ordinary personas + one dedicated administrator  •  passwords intentionally excluded',55,105,2080,45,19)
p.box('users','UPSTREAM DEX PERSONAS',['testuser01@dda.test  •  Alex Morgan','testuser02@dda.test  •  Jamie Parker','testuser03@dda.test  •  Taylor Reed','testuser04@dda.test  •  Jordan Blake','testuser05@dda.test  •  Casey Brooks','','All five: webui-user role → ordinary app user','Stable IDs dda-test-01 … dda-test-05','Profile name/email inherited from Dex'],65,230,660,390,'blue')
p.box('admins','DEFAULT ADMINISTRATION',['Dex SSO identity: admin@dda.test / DDA Administrator','Keycloak dda: explicit realm-management/realm-admin','Open WebUI: openwebui-admins → webui-admin','Keycloak master: separate admin credential','PostgreSQL: postgres (internal administration only)','','Dex config: file/Git administration, no admin web UI','Headroom: loopback utility, no built-in user accounts','Existing Web UI administrators preserved'],785,230,1350,390,'purple')
p.box('config','REPRODUCIBLE SOURCE',['compose.yaml + compose.identity.yaml','scripts/bootstrap.py / sync-keycloak.py','Per-component README + config templates','scripts/render-openshift.py → 27 resources','images.lock.json + derived Dockerfiles','Draw.io pages + SVG previews'],65,705,660,305)
p.box('secrets','PRIVATE MATERIAL',['.runtime/TEST-USERS.md',' .runtime/ADMIN-ACCESS.md','Generated secrets and bcrypt hashes','Database dumps / app backups','Rendered OpenShift Secret files','','Excluded from Git; protect/encrypt for transfer'],785,705,620,305,'amber','#FFF9ED')
p.box('evidence','DEMONSTRATED / VERIFIED',['Direct login for all five identities','Fresh administrator provisioned without profile form','Web UI Admin Panel + Keycloak realm console SSO','Five ordinary users remain non-admin','Invalid redirect URI rejected','Backup completed; services restarted'],1465,705,670,305,'green','#F0FAF5')
p.box('limits','ENTERPRISE HANDOFF BOUNDARIES',['The Mac stack is running and tested. OpenShift manifests are rendered/checked, not cluster-validated.','No HA claim: SQLite stores and single PostgreSQL require a supported shared-storage/database design before scaling.','Model-provider access is independent: enterprise inference URL, CA, model artifacts and egress must be supplied.','Replace demo passwords with an approved enterprise identity source, named MFA admins, audit retention and a rotation process.','Production release requires your platform, network, certificate, capacity, restore and security acceptance evidence.'],65,1100,2070,275,'amber','#FFF9ED',19)
p.svg()
E.indent(mx,space='  ');E.ElementTree(mx).write(OUT/'dda-sso-architecture.drawio',encoding='utf-8',xml_declaration=True)
print('Generated four editable Draw.io pages and four matching SVG previews.')
