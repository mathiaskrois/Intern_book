import json
from playwright.sync_api import sync_playwright
from common import credentials, launch, authenticate
from archive import SANITIZE

cfg = credentials()
with sync_playwright() as p:
    context = launch(p)
    page = context.pages[0]
    authenticate(page, cfg)
    page.evaluate(SANITIZE)
    print(json.dumps({'url': page.url, 'title': page.title(), 'text': page.locator('body').inner_text()[:16000],
        'forms': page.locator('form').evaluate_all('(fs) => fs.map(f => ({action:f.action, method:f.method, inputs:[...f.querySelectorAll("input,button")].map(i=>({tag:i.tagName,type:i.type,name:i.name,text:i.textContent}))}))'),
        'links': page.locator('a').evaluate_all('(as) => as.map(a=>({text:a.innerText,url:a.href}))')}, ensure_ascii=False, indent=2))
    context.close()
