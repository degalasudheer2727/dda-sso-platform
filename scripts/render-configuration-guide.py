#!/usr/bin/env python3
"""Render the guide's small Markdown subset to an offline HTML document.
Standard library only; images remain adjacent local files. No CDN dependencies.
"""
import html,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root/'docs/CONFIGURATION-GUIDE.md'
def slug(s):return re.sub(r'[^a-z0-9 -]','',s.lower()).replace(' ','-')
def inline(s):
 protected=[]
 def code(m):
  protected.append('<code>'+html.escape(m[1])+'</code>');return f'CODEPLACEHOLDER{len(protected)-1}END'
 s=re.sub(r'`([^`]+)`',code,s);s=html.escape(s)
 s=re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',r'<a class="image-link" href="\2" target="_blank" rel="noopener"><img src="\2" alt="\1" loading="lazy"></a>',s)
 s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',s)
 s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
 for i,v in enumerate(protected):s=s.replace(f'CODEPLACEHOLDER{i}END',v)
 return s
lines=source.read_text().splitlines();parts=[];toc=[];i=0
while i<len(lines):
 line=lines[i]
 if not line.strip():i+=1;continue
 if line.startswith('```'):
  block=[];i+=1
  while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
  parts.append('<pre><code>'+html.escape('\n'.join(block))+'</code></pre>');i+=1;continue
 m=re.match(r'^(#{1,3}) (.*)',line)
 if m:
  level=len(m[1]);title=m[2];ident=slug(title)
  parts.append(f'<h{level} id="{ident}">{inline(title)}</h{level}>')
  if level==2:toc.append(f'<a href="#{ident}">{html.escape(title)}</a>')
  i+=1;continue
 if line.startswith('|') and i+1<len(lines) and re.match(r'^\|[- :|]+\|$',lines[i+1]):
  rows=[];headers=[v.strip() for v in line.strip('|').split('|')];i+=2
  while i<len(lines) and lines[i].startswith('|'):
   rows.append([v.strip() for v in lines[i].strip('|').split('|')]);i+=1
  parts.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+inline(v)+'</th>' for v in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>');continue
 if re.match(r'^\d+\. ',line):
  items=[]
  while i<len(lines) and re.match(r'^\d+\. ',lines[i]):items.append(re.sub(r'^\d+\. ','',lines[i]));i+=1
  parts.append('<ol>'+''.join('<li>'+inline(v)+'</li>' for v in items)+'</ol>');continue
 if line.startswith('!['):parts.append('<figure>'+inline(line)+'</figure>');i+=1;continue
 paragraph=[line];i+=1
 while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|!\[|\d+\. )',lines[i]):paragraph.append(lines[i]);i+=1
 parts.append('<p>'+inline(' '.join(paragraph))+'</p>')
css='''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:30px}body{margin:0;background:#f5f7fb;color:#213047;font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}aside{position:fixed;inset:0 auto 0 0;width:270px;padding:30px 22px;background:#10253a;color:#d8e7ef;overflow:auto}aside .brand{font-size:30px;font-weight:800;color:white;letter-spacing:2px}aside .sub{font-size:12px;color:#89cfc4;text-transform:uppercase;letter-spacing:1px;margin:8px 0 28px}nav a{display:block;color:#bdd0df;text-decoration:none;padding:9px 10px;font-size:13px;line-height:1.45;border-left:2px solid transparent}nav a:hover,nav a.active{background:#19384e;color:white;border-color:#51c8b1}main{margin-left:270px;padding:44px 46px 100px;max-width:1510px}.eyebrow{color:#087f79;font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase}h1{font-size:42px;line-height:1.15;letter-spacing:-1px;color:#122d42;margin:12px 0 25px}h2{font-size:27px;color:#12334a;line-height:1.25;border-top:1px solid #d5e0ea;padding-top:34px;margin-top:60px}h3{font-size:20px;color:#087f79;margin:30px 0 10px}p{max-width:1000px}a{color:#067a78;text-underline-offset:3px}code{background:#e8eef3;border-radius:4px;padding:2px 5px;font-size:.85em;overflow-wrap:anywhere}pre{padding:22px;background:#112b40;color:#d7f5ed;border-radius:10px;overflow:auto}pre code{background:none;padding:0;white-space:pre;font-size:13px}figure{margin:25px 0;background:white;border:1px solid #dae3eb;padding:12px;border-radius:12px;box-shadow:0 5px 18px #132e4410}figure img{display:block;width:100%;height:auto;border-radius:6px}figure:after{content:"Live configuration screenshot · Click image for full resolution";display:block;color:#637588;font-size:12px;margin:8px 3px 0}.table-wrap{overflow-x:auto;margin:20px 0;background:white;border:1px solid #dce4eb;border-radius:9px}table{width:100%;border-collapse:collapse;font-size:14px}th{text-align:left;background:#e6f1f2;color:#123e4b;font-weight:650}th,td{padding:13px 16px;border-bottom:1px solid #e3e9ee;vertical-align:top}tr:last-child td{border-bottom:0}li{padding:4px 0}.toplinks{font-size:13px;margin:0 0 30px}.foot{font-size:12px;color:#698091;margin-top:50px}@media(max-width:900px){aside{position:static;width:auto;padding:20px}nav{display:none}main{margin:0;padding:28px 20px}h1{font-size:34px}}@media print{aside,.toplinks{display:none}main{margin:0;padding:0}body{background:white;font-size:11px}h2{break-before:page}figure,table{break-inside:avoid}a{color:inherit}figure:after{display:none}}'''
page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DDA SSO | Configuration guide</title><style>'+css+'</style></head><body><aside><div class="brand">DDA / SSO</div><div class="sub">Administrator field guide</div><nav>'+''.join(toc)+'</nav></aside><main><div class="eyebrow">Local deployment · Enterprise handoff</div><div class="toplinks"><a href="CONFIGURATION-GUIDE.md">Markdown source</a> · <a href="configuration/local-effective-config.json">Non-secret configuration</a> · <a href="../architecture/dda-sso-architecture.drawio">Draw.io architecture</a></div>'+''.join(parts)+'<p class="foot">Offline document. Adjacent screenshots are required. Capture date and deployment limits are stated above.</p></main><script>const links=[...document.querySelectorAll("nav a")];const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting)links.forEach(a=>a.classList.toggle("active",a.hash==="#"+e.target.id))}),{rootMargin:"-5% 0px -75% 0px"});document.querySelectorAll("h2").forEach(h=>observer.observe(h));</script></body></html>'
(root/'docs/CONFIGURATION-GUIDE.html').write_text(page)
print('Built offline configuration guide HTML.')
