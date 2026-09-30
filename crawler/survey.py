import json
from playwright.sync_api import sync_playwright
from common import credentials, launch, authenticate, ROOT

paths = ['den-hurtige/', 'opslagstavle/', 'begivenheder/', 'alumneliste/', 'fotoalbum/', 'soegvaerelse/', 'vaerelsestjek/', 'ak/', 'oelkaelder/min-saldo', 'reparationer/', 'stamtree/', 'statistik/', 'arkiv/']
with sync_playwright() as p:
    ctx = launch(p)
    page = ctx.pages[0]
    authenticate(page, credentials())
    results = []
    for path in paths + ['https://gahk.dk/wiki', 'https://www.gahk.dk/']:
        url = path if path.startswith('https:') else 'https://www.gahk.dk/intern/' + path
        try:
            response = page.goto(url, wait_until='networkidle', timeout=40000)
            result = page.evaluate('''() => {
                const main = document.querySelector('main') || document.body;
                return {title:document.title, text:main.innerText.slice(0,9000),
                  main:main.tagName+'#'+main.id+'.'+main.className,
                  links:[...main.querySelectorAll('a')].map(a=>({text:a.innerText,url:a.href})),
                  images:[...main.querySelectorAll('img')].map(i=>({src:i.src,alt:i.alt,width:i.naturalWidth,height:i.naturalHeight})),
                  styles:[...document.querySelectorAll('link[rel=stylesheet]')].map(x=>x.href)};
            }''')
            result.update(url=page.url, status=response.status)
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
        except Exception as e:
            print(json.dumps({'url':url,'error':str(e)[:200]}), flush=True)
    (ROOT / 'crawler' / 'survey.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
    ctx.close()
