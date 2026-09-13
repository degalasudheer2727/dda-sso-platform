"""Reconcile the DDA group names and default enrollment without changing memberships."""
def reconcile_groups(call,base,specs):
 groups={g['name']:g for g in call(base+'/groups')}
 # Upgrade the earlier name in place: ID, memberships and existing mappings survive.
 old='openweb-users';new='openwebui-users'
 if old in groups:
  if new in groups:raise RuntimeError('Both legacy and canonical user groups exist; refusing an ambiguous merge.')
  g=call(base+'/groups/'+groups[old]['id'])
  g.update(name=new,path='/'+new)
  call(base+'/groups/'+g['id'],'PUT',g)
  groups={g['name']:g for g in call(base+'/groups')}
 for spec in specs:
  if spec['name'] not in groups:
   call(base+'/groups','POST',{'name':spec['name']})
   groups={g['name']:g for g in call(base+'/groups')}
  call(base+'/groups/'+groups[spec['name']]['id']+'/role-mappings/realm','POST',[call(base+'/roles/'+name) for name in spec['realmRoles']])
 # Default enrollment happens only when Keycloak creates a user. It does not
 # re-add the group on later logins after an administrator removes membership.
 call(base+'/default-groups/'+groups[new]['id'],'PUT')
 assert groups[new]['id'] in {g['id'] for g in call(base+'/default-groups')}
 return groups
