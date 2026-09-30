"""Read-only, bounded archive of the website's representative pages.

Wiki and album/archive contents are intentionally excluded at the user's request.
Only the login is submitted; all subsequent non-GET requests are blocked.
"""
import hashlib
import json
import re
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode, unquote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from common import ROOT, credentials, launch, authenticate

BASE = 'https://www.gahk.dk'
OUT = ROOT / 'website-archive'
MAX_PAGES = 100
SKIP = re.compile(r'/(?:admin|django-admin|opret|rediger|edit|delete|slet|logout|password[^/]*|besvar|upload|ny-mappe|hent-alt)(?:/|$)', re.I)

def canonical(url):
    p = urlsplit(url)
    if p.hostname not in ('www.gahk.dk', 'gahk.dk'):
        return None
    path = p.path.rstrip('/') + ('/' if p.path.rstrip('/') in ['/intern','/intern/den-hurtige','/intern/opslagstavle','/intern/begivenheder','/intern/alumneliste','/intern/fotoalbum','/intern/soegvaerelse','/intern/vaerelsestjek','/intern/ak','/intern/reparationer','/intern/stamtree','/intern/statistik','/intern/arkiv'] else '')
    # Keep only bounded, genuinely distinct pagination. Filters/sorts are views of the same data.
    query = [(k,v) for k,v in parse_qsl(p.query) if k == 'page' and v.isdigit() and int(v) <= 3]
    return urlunsplit(('https','www.gahk.dk',path,urlencode(query),''))

def exclusion(url):
    p = urlsplit(url).path
    if p.endswith('/abonnement') or p.endswith('/naeste-maaned'): return 'Personal calendar access link or directory editing view'
    if p.endswith('/ics'): return 'Calendar download, handled separately as an asset'
    if '/wiki' in p: return 'Wiki excluded by user'
    if not p.startswith('/intern/'): return 'Outside the internal-site book scope'
    if SKIP.search(p): return 'Editing, authentication, administrative or state-changing route'
    if p.startswith('/intern/fotoalbum/') and p.rstrip('/') != '/intern/fotoalbum': return 'Album contents excluded by user; overview only'
    if p.startswith('/intern/arkiv/') and p.rstrip('/') != '/intern/arkiv': return 'Stored files/folders excluded by user; overview only'
    if '/beboer/' in p and p != '/intern/beboer/456/profil': return 'Individual directory records: overview represented instead'
    if '/vaerelsestjek/se/' in p and not p.endswith('/101'): return 'Repeated room records: overview plus one representative read-only page'
    if '/eksport' in p or '/export' in p: return 'Duplicate downloadable directory view'
    return None

def ident(url):
    p=urlsplit(url)
    name=p.path.removeprefix('/intern/').strip('/') or 'dashboard'
    return re.sub(r'[^a-zA-Z0-9_-]+','-',unquote(name)) + ('-page-'+dict(parse_qsl(p.query))['page'] if p.query else '')

SANITIZE = '''() => {
  // Remove credential panels before screenshots, text extraction or HTML serialization.
  for (const e of [...document.querySelectorAll('main *')]) {
    if (e.children.length === 0 && /^(WiFi-kode|Fælleskalender)$/.test(e.textContent.trim())) {
      const box=e.closest('.card') || e.parentElement;
      box.textContent='Adgangsoplysninger udeladt';
    }
  }
  for(const i of document.querySelectorAll('input')) { i.removeAttribute('value'); i.value=''; }
  for(const e of document.querySelectorAll('script,meta[name*=csrf],input[type=hidden]')) e.remove();
  for(const e of document.querySelectorAll('*')) for(const a of [...e.attributes]) {
    if (/^on|^hx-|csrf|token|^data-.*(?:post|delete|upload|commit)/i.test(a.name)) e.removeAttribute(a.name);
  }
  for(const f of document.forms) {f.removeAttribute('action'); f.setAttribute('onsubmit','return false');}
  for(const i of document.images) i.loading='eager';
}'''

def main():
    for d in ['pages','screenshots','assets']: (OUT/d).mkdir(parents=True,exist_ok=True)
    cfg=credentials(); records=[]; failures=[]; skipped={}; assetmap={}; seen=set()
    roots=['','opslagstavle/','den-hurtige/','begivenheder/','alumneliste/','fotoalbum/','soegvaerelse/','vaerelsestjek/','ak/','oelkaelder/min-saldo','reparationer/','stamtree/','statistik/','arkiv/','beboer/456/profil']
    queue=deque((BASE+'/intern/'+r,None) for r in roots)
    with sync_playwright() as pw:
        ctx=launch(pw); page=ctx.pages[0]; authenticate(page,cfg)
        ctx.route('**/*', lambda route: route.continue_() if route.request.method in ('GET','HEAD') else route.abort())
        # No external frames, telemetry, or navigation; preserve the site's own content.
        page.route('https://calendar.google.com/**',lambda r:r.abort())
        while queue and len(records)<MAX_PAGES:
            url,parent=queue.popleft(); url=canonical(url)
            if not url or url in seen: continue
            reason=exclusion(url)
            if reason: skipped[url]=reason;continue
            seen.add(url); key=ident(url)
            try:
                response=page.goto(url,wait_until='domcontentloaded',timeout=30000)
                page.wait_for_timeout(600)
                if response.status >= 400 or '/login' in page.url:
                    failures.append({'url':url,'status':response.status,'reason':'HTTP error or login redirect'});continue
                awaitable=page.evaluate('''() => ({links:[...document.querySelectorAll('a[href]')].map(a=>({url:a.href,text:a.innerText.trim()})),
                  style:[...document.querySelectorAll('link[rel=stylesheet]')].map(e=>e.href)})''')
                links=awaitable['links']
                # Stop all live pollers before freezing this read-only snapshot.
                page.evaluate(SANITIZE)
                page.evaluate('''async()=>{await Promise.race([Promise.all([...document.images].map(i=>i.decode().catch(()=>{}))),new Promise(r=>setTimeout(r,8000))]);await document.fonts.ready;}''')
                data=page.evaluate('''() => {const m=document.querySelector('main')||document.body;const c=m.cloneNode(true);
                  c.querySelectorAll('form,select,button,.emoji-picker,.who-picker,[hidden]').forEach(e=>e.remove());
                  return {title:document.title,heading:m.querySelector('h1')?.innerText||document.title,
                    text:c.innerText||c.textContent,html:m.innerHTML,
                    images:[...m.querySelectorAll('img[src]')].map(i=>({url:i.src,alt:i.alt,width:i.naturalWidth,height:i.naturalHeight})),
                    headings:[...m.querySelectorAll('h1,h2,h3')].map(e=>e.innerText),
                    tables:[...m.querySelectorAll('table')].map(t=>[...t.rows].map(r=>[...r.cells].map(c=>c.innerText.trim()))),
                    notices:[...m.querySelectorAll('.notice-card')].map(e=>({id:e.id,author:e.querySelector('.notice-name')?.innerText,date:e.querySelector('time')?.textContent,datetime:e.querySelector('time')?.dateTime,body:e.querySelector('.board-body')?.innerHTML})),
                    colors:[...new Set([...document.querySelectorAll('body,aside,h1,.card')].map(e=>getComputedStyle(e).backgroundColor))]};}''')
                # Detaching loses innerText layout semantics, so build readable text with BS4.
                clean=BeautifulSoup(data['html'],'html.parser')
                for x in clean.select('input,textarea,select,button,.emoji-picker,.who-picker,[hidden],script'):x.decompose()
                text='\n'.join(x.strip() for x in clean.get_text('\n').splitlines() if x.strip())
                if cfg['WEBSITE_PASSWORD'] in text: raise RuntimeError('Secret guard: content was not saved')
                (OUT/'pages'/f'{key}.txt').write_text(text)
                (OUT/'pages'/f'{key}.content.html').write_text(str(clean))
                raw=page.content()
                if cfg['WEBSITE_PASSWORD'] in raw: raise RuntimeError('Secret guard: HTML was not saved')
                (OUT/'pages'/f'{key}.html').write_text(raw)
                page.screenshot(path=str(OUT/'screenshots'/f'{key}.jpg'),full_page=True,type='jpeg',quality=85,animations='disabled')
                # A separate main-content capture is useful for restrained facsimiles in print.
                if page.locator('main').count():
                    page.locator('main').screenshot(path=str(OUT/'screenshots'/f'{key}-main.png'),animations='disabled')
                internal=[]
                for link in links:
                    target=canonical(link['url'])
                    if not target:continue
                    if target not in internal:internal.append(target)
                    reason=exclusion(target)
                    if reason:skipped[target]=reason
                    elif target not in seen:queue.append((target,url))
                # Download original page images and stylesheet; never enter photo/file stores.
                for asset in data['images'] + [{'url':u,'alt':'stylesheet'} for u in awaitable['style']]:
                    src=asset['url']
                    if src in assetmap or urlsplit(src).hostname not in ('www.gahk.dk','gahk.dk'):continue
                    try:
                        r=ctx.request.get(src,timeout=20000)
                        if not r.ok:assetmap[src]={'error':f'HTTP {r.status}'};continue
                        blob=r.body()
                        if len(blob)>20_000_000:assetmap[src]={'error':'20 MB per-asset limit'};continue
                        filename=re.sub(r'[^a-zA-Z0-9._-]+','-',unquote(urlsplit(src).path).strip('/'))
                        path='assets/'+filename
                        (OUT/path).write_bytes(blob)
                        assetmap[src]={'path':path,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'content_type':r.headers.get('content-type','')}
                    except Exception as e:assetmap[src]={'error':type(e).__name__}
                record={'id':key,'url':url,'original_url':url,'final_url':page.url,'title':data['title'],'heading':data['heading'],
                    'parent':parent,'section':urlsplit(url).path.split('/')[2] or 'dashboard','outgoing_internal_links':internal,
                    'links':links,'images':data['images'],'screenshot_path':f'screenshots/{key}.jpg','main_screenshot_path':f'screenshots/{key}-main.png',
                    'html_path':f'pages/{key}.html','content_path':f'pages/{key}.txt','content_html_path':f'pages/{key}.content.html',
                    'headings':data['headings'],'tables':data['tables'],'notices':data['notices'],
                    'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'captured_at':datetime.now(timezone.utc).isoformat()}
                records.append(record)
                (OUT/'index.json').write_text(json.dumps({'pages':records,'assets':assetmap,'failures':failures,'excluded':skipped},ensure_ascii=False,indent=2))
                print(f'{len(records):03d} {key} | {len(text)} characters | {len(data["images"])} images',flush=True)
            except Exception as e:
                failures.append({'url':url,'reason':type(e).__name__+': '+str(e)[:140]})
                print('FAILED '+key+' '+type(e).__name__,flush=True)
        ctx.close()
    # Make all saved HTML passive and local; retain original source URLs in the index.
    for record in records:
        for field in ['html_path','content_html_path']:
            path=OUT/record[field]; soup=BeautifulSoup(path.read_text(),'html.parser')
            for e in soup.select('[src],link[href]'):
                attr='src' if e.has_attr('src') else 'href'; absolute=urljoin(record['url'],e[attr])
                if absolute in assetmap and 'path' in assetmap[absolute]:e[attr]='../'+assetmap[absolute]['path']
                elif e.name=='iframe':e.decompose()
                else:e[attr]=absolute
            for a in soup.select('a[href]'):
                dest=canonical(urljoin(record['url'],a['href']))
                if dest in seen and any(r['url']==dest for r in records):a['href']=ident(dest)+'.html'
                else:a['href']=urljoin(record['url'],a['href'])
            path.write_text(str(soup))
    result={'captured_at':datetime.now(timezone.utc).isoformat(),'scope':'Internal site overview and useful read-only subpages; no wiki, album contents or stored archive files.',
        'limits':{'max_pages':MAX_PAGES,'pagination_pages':3,'per_asset_bytes':20_000_000},'remaining_queue':list(queue),
        'pages':records,'assets':assetmap,'failures':failures,'excluded':skipped}
    (OUT/'index.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(f'DONE: {len(records)} pages, {len(assetmap)} assets, {len(failures)} failures.',flush=True)

if __name__=='__main__':main()
